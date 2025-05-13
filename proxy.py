from flask import Flask, request, Response
import requests
from ntfy import send_ntfy_notification

app = Flask(__name__)

ACESTREAM_ORIGIN = "http://acestream-proxy:6878"
PROXY_BASE = "https://channels.subasically.me/ace"


@app.route("/ace/manifest.m3u8")
def proxy_manifest():
    ace_id = request.args.get("id")
    if not ace_id:
        return "Missing id parameter", 400

    try:
        # Step 1: Get redirect from AceStream proxy
        redirect_resp = requests.get(
            f"{ACESTREAM_ORIGIN}/ace/manifest.m3u8?id={ace_id}", allow_redirects=False
        )
        if "Location" not in redirect_resp.headers:
            send_ntfy_notification(
                "Manifest Proxy Error", "No redirect from AceStream proxy"
            )
            return "No redirect from AceStream proxy", 502

        redirect_url = redirect_resp.headers["Location"]

        # Step 2: Fetch the actual .m3u8 playlist
        raw = requests.get(redirect_url, timeout=5)
        raw.raise_for_status()

        # Step 3: Rewrite URLs for HTTPS playback
        modified = raw.text.replace(
            "http://channels.subasically.me:6878/ace/", f"{PROXY_BASE}/"
        )
        modified = modified.replace(
            "http://acestream-proxy:6878/ace/", f"{PROXY_BASE}/"
        )

        return Response(
            modified,
            content_type="application/vnd.apple.mpegurl",
            headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "no-cache"},
        )

    except Exception as e:
        send_ntfy_notification("Manifest Proxy Error", str(e))
        return f"Error: {e}", 500
