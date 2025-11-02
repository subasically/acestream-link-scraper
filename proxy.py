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


@app.route("/ace/<path:subpath>")
def proxy_ace_content(subpath):
    """Proxy all other AceStream content (m3u8 playlists, ts segments, etc.)"""
    
    try:
        # Forward the request to the AceStream proxy
        url = f"{ACESTREAM_ORIGIN}/ace/{subpath}"
        logging.info(f"Proxying content: {url}")
        
        # Forward query parameters if any
        if request.query_string:
            url += f"?{request.query_string.decode()}"
        
        resp = requests.get(url, timeout=10, stream=True)
        resp.raise_for_status()
        
        # Determine content type
        content_type = resp.headers.get('Content-Type', 'application/octet-stream')
        
        # If it's an m3u8 file, rewrite URLs
        if '.m3u8' in subpath or 'mpegurl' in content_type:
            scheme = request.headers.get('X-Forwarded-Proto', request.scheme)
            host = request.host
            proxy_base = f"{scheme}://{host}/ace"
            
            content = resp.text
            content = content.replace("http://acestream-proxy:6878/ace/", f"{proxy_base}/")
            content = content.replace("http://localhost:6878/ace/", f"{proxy_base}/")
            
            return Response(
                content,
                content_type="application/vnd.apple.mpegurl",
                headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "no-cache"},
            )
        else:
            # For video segments, stream them directly
            return Response(
                resp.iter_content(chunk_size=8192),
                content_type=content_type,
                headers={"Access-Control-Allow-Origin": "*"},
            )
            
    except Exception as e:
        error_msg = f"Error proxying {subpath}: {str(e)}"
        logging.error(error_msg)
        return error_msg, 500
