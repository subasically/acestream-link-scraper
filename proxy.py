from flask import Flask, request, Response
import requests
import os
import logging
from ntfy import send_ntfy_notification

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

ACESTREAM_ORIGIN = "http://acestream-proxy:6878"


@app.route("/ace/manifest.m3u8")
def proxy_manifest():
    ace_id = request.args.get("id")
    if not ace_id:
        return "Missing id parameter", 400

    # Build proxy base URL dynamically from request
    scheme = request.headers.get('X-Forwarded-Proto', request.scheme)
    host = request.host
    proxy_base = f"{scheme}://{host}/ace"
    
    logging.info(f"Proxying manifest for ID: {ace_id}, proxy_base: {proxy_base}")

    try:
        # Step 1: Get redirect from AceStream proxy
        redirect_resp = requests.get(
            f"{ACESTREAM_ORIGIN}/ace/manifest.m3u8?id={ace_id}", allow_redirects=False, timeout=10
        )
        
        logging.info(f"AceStream response status: {redirect_resp.status_code}")
        
        if "Location" not in redirect_resp.headers:
            error_msg = f"No redirect from AceStream proxy. Status: {redirect_resp.status_code}"
            logging.error(error_msg)
            send_ntfy_notification("Manifest Proxy Error", error_msg)
            return error_msg, 502

        redirect_url = redirect_resp.headers["Location"]
        logging.info(f"Redirect URL: {redirect_url}")

        # Step 2: Fetch the actual .m3u8 playlist
        raw = requests.get(redirect_url, timeout=10)
        raw.raise_for_status()

        # Step 3: Rewrite URLs for playback through this proxy
        modified = raw.text
        # Replace various possible internal URLs with proxy URL
        modified = modified.replace("http://acestream-proxy:6878/ace/", f"{proxy_base}/")
        modified = modified.replace("http://localhost:6878/ace/", f"{proxy_base}/")
        
        logging.info(f"Successfully proxied manifest, length: {len(modified)}")

        return Response(
            modified,
            content_type="application/vnd.apple.mpegurl",
            headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "no-cache"},
        )

    except Exception as e:
        error_msg = f"Error proxying manifest: {str(e)}"
        logging.error(error_msg)
        send_ntfy_notification("Manifest Proxy Error", error_msg)
        return error_msg, 500
