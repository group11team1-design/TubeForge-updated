const API_BASE = (window.TUBEFORGE_API || "").replace(/\/$/, "");
const apiUrl = (path) => `${API_BASE}${path}`;
const $ = (x) => document.getElementById(x);
const show = (x) => x.classList.remove("hidden");
const hide = (x) => x.classList.add("hidden");

$("inspect").onclick = async () => {
  const url = $("url").value.trim();
  if (!url) return err("Paste a video URL first.");
  $("inspect").disabled = true;
  $("inspect").textContent = "Analyzing...";
  hide($("error"));
  try {
    const response = await fetch(apiUrl("/api/info"), {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not analyze this URL.");
    $("thumb").src = data.thumbnail || "";
    $("title").textContent = data.title || "Video";
    $("meta").textContent = [data.uploader, data.duration].filter(Boolean).join(" • ");
    show($("preview"));
    $("quality").innerHTML = '<option value="best">Best available MP4</option>';
    (data.qualities || []).forEach(q => $("quality").insertAdjacentHTML("beforeend", `<option value="${q.height}">${q.label}</option>`));
    if (!(data.qualities || []).length && $("format").value === "video") {
      $("quality").insertAdjacentHTML("beforeend", '<option value="best">Source default (may be unavailable)</option>');
    }
    if (data.note) $("notice").textContent = data.note;
  } catch (e) { err(e.message); }
  finally { $("inspect").disabled = false; $("inspect").textContent = "Analyze"; }
};

$("format").onchange = () => {
  $("quality").disabled = $("format").value !== "video";
  if ($("format").value === "mp3") {
    $("notice").textContent = "MP3 conversion is unavailable in Vercel serverless mode. Choose Original Audio for a direct audio file.";
  } else {
    $("notice").textContent = "Vercel mode sends you to a source-hosted media URL; it does not store or convert the file on this server.";
  }
};

$("download").onclick = () => {
  const url = $("url").value.trim();
  if (!url) return err("Paste a video URL first.");
  if ($("format").value === "mp3") {
    return err("MP3 conversion needs FFmpeg and a persistent/long-running worker, which this Vercel serverless version does not provide. Choose Original Audio instead.");
  }
  hide($("error"));
  $("download").disabled = true;
  $("status").textContent = "Resolving source link...";
  $("pct").textContent = "";
  $("bar").style.width = "25%";
  show($("box"));
  const params = new URLSearchParams({ url, format: $("format").value, height: $("quality").value });
  // Navigation lets the source CDN deliver the media directly, avoiding the
  // Vercel Function response-size cap and cross-origin fetch restrictions.
  window.location.assign(apiUrl(`/api/download?${params.toString()}`));
  setTimeout(() => { $("download").disabled = false; $("status").textContent = "If no download starts, try another quality or source URL."; }, 4000);
};

function err(message) { $("error").textContent = message; show($("error")); }
