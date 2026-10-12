from flask import Flask, jsonify, request, send_from_directory, redirect
from flask_cors import CORS
from urllib.parse import urlparse
import os
import yt_dlp

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app, origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","), supports_credentials=False)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def checked_url(value):
    value = (value or "").strip()
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Enter a valid http or https video URL.")
    return value


def extract(url):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "socket_timeout": 12,
        "retries": 1,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


@app.get("/api/health")
def health():
    return jsonify(status="ok", service="TubeForge API", mode="serverless-direct")


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/config.js")
def config():
    return send_from_directory(BASE_DIR, "config.js")


@app.post("/api/info")
def info():
    try:
        data = request.get_json(silent=True) or {}
        url = checked_url(data.get("url"))
        info_data = extract(url)
        qualities = {}
        # Vercel cannot run a long download/FFmpeg merge reliably. List only
        # progressive formats that already contain both video and audio.
        for fmt in info_data.get("formats", []):
            if fmt.get("url") and fmt.get("vcodec") != "none" and fmt.get("acodec") != "none" and fmt.get("height"):
                height = int(fmt["height"])
                if fmt.get("ext") == "mp4":
                    qualities[height] = max(qualities.get(height, 0), float(fmt.get("fps") or 0))
        return jsonify(
            title=info_data.get("title"),
            thumbnail=info_data.get("thumbnail"),
            duration=info_data.get("duration_string"),
            uploader=info_data.get("uploader"),
            qualities=[{"height": h, "label": f"{h}p" + (f" {int(fps)}fps" if fps >= 50 else "")} for h, fps in sorted(qualities.items(), reverse=True)],
            note="Vercel mode uses direct source links. Only combined audio/video MP4 qualities are listed; separate tracks and conversion require a dedicated worker.",
        )
    except Exception as exc:
        return jsonify(error=str(exc)), 400


@app.get("/api/download")
def download():
    """Resolve a media URL and redirect the browser to the source CDN.

    This avoids buffering a video through a serverless function, which has
    response-size and execution-time limits. Only formats already hosted by
    the source are offered; no transcoding or merging is performed.
    """
    try:
        url = checked_url(request.args.get("url"))
        media_format = request.args.get("format", "video")
        height = request.args.get("height", "best")
        info_data = extract(url)
        formats = info_data.get("formats", [])
        if media_format == "audio":
            candidates = [f for f in formats if f.get("url") and f.get("acodec") != "none" and f.get("vcodec") == "none"]
            candidates.sort(key=lambda f: (f.get("ext") == "m4a", f.get("abr") or 0), reverse=True)
        else:
            candidates = [f for f in formats if f.get("url") and f.get("ext") == "mp4" and f.get("vcodec") != "none" and f.get("acodec") != "none"]
            if height != "best":
                try:
                    max_height = int(height)
                    under = [f for f in candidates if (f.get("height") or 0) <= max_height]
                    if under:
                        candidates = under
                except ValueError:
                    pass
            candidates.sort(key=lambda f: ((f.get("height") or 0), (f.get("tbr") or 0)), reverse=True)
        if not candidates:
            return jsonify(error="No directly downloadable format of this type is available for this video on Vercel. Try another quality or audio/video mode."), 422
        target = candidates[0].get("url")
        if not target:
            return jsonify(error="The source did not provide a direct media URL."), 422
        return redirect(target, code=302)
    except Exception as exc:
        return jsonify(error=str(exc)), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
