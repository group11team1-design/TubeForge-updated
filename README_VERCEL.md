# TubeForge — Vercel deployment package

This version serves both the website and Flask API from the same Vercel project. The incorrect `flask_cors` import is fixed.

## Publish to GitHub
1. Download and extract this ZIP.
2. Replace the files in the root of your `group11team1-design/TubeForge` repository with the extracted files. Keep the `api/` and `static/` folders.
3. Commit/push to `main`. Vercel should redeploy automatically.
4. In Vercel, set the project Root Directory to `./`; leave the Python/Flask preset and install command as detected. No environment variables are required for the basic setup.
5. Test `https://YOUR-PROJECT.vercel.app/api/health` — it should return JSON with `status: ok`.

## Important serverless design choice
Vercel Functions are not suitable for reliably downloading, merging, converting, and storing large videos as a long-running background job. This version therefore runs metadata analysis in the Vercel backend and redirects the browser to a media URL hosted by the source CDN. It supports source-hosted progressive MP4 (video+audio) and original audio when available. It does not merge separate video/audio tracks, convert to MP3, or provide reliable live download progress/cancellation. Quality availability depends on the source.

Use this only for content you are authorized to download and follow the source platform's terms and applicable law.
