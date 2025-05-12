import requests
from bs4 import BeautifulSoup
import time
import os
import logging
import json
from ntfy import send_ntfy_notification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def check_server_version(server_ip, max_retries=30, timeout=5):
    logging.info("Checking server version...")
    for attempt in range(max_retries):
        try:
            version_check_url = (
                f"http://{server_ip}/webui/api/service?method=get_version"
            )
            response = requests.get(version_check_url, timeout=timeout)
            response.raise_for_status()  # Raise an exception for HTTP errors

            version_data = response.json()
            if "result" in version_data and "version" in version_data["result"]:
                version = version_data["result"]["version"]
                logging.info(f"Server is up and running on version: {version}")
                return version
            else:
                logging.warning(
                    f"Version key not found in the response. {version_data}"
                )
        except requests.RequestException as e:
            logging.error(
                f"Attempt {attempt + 1} of {max_retries}: Error fetching version - {e}"
            )

        time.sleep(timeout)

    logging.error("Failed to retrieve server version after maximum retries.")
    return None


def collect_acestream_ids(search_query):
    logging.info(f"Search for {search_query}")
    url = f"https://acestreamsearch.net/en/?q={search_query}"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data for query '{search_query}': {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    acestream_links = [
        (link["href"].replace("acestream://", ""), link.get_text(strip=True))
        for link in soup.find_all("a", href=True)
        if link["href"].startswith("acestream://")
    ]
    return acestream_links


def fetch_tvmaze_info(channels_json, output_json="tvmaze.json"):
    logging.info("Fetching TVmaze info for channels...")
    tvmaze_data = {}
    api_key = os.getenv("TVMAZE_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    # Load mapping file if it exists
    mapping_path = "tvmaze_channel_map.json"
    channel_map = {}
    if os.path.exists(mapping_path):
        with open(mapping_path, "r") as f:
            channel_map = json.load(f)

    for ch in channels_json:
        # Use mapped name if available, else fallback to original
        orig_name = ch["title"].split("[")[0].strip()
        search_name = channel_map.get(ch["title"], orig_name)
        try:
            resp = requests.get(
                "https://api.tvmaze.com/search/shows",
                params={"q": search_name},
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            results = resp.json()
            if results:
                show = results[0]["show"]
                tvmaze_data[orig_name] = {
                    "name": show.get("name"),
                    "genres": show.get("genres"),
                    "summary": show.get("summary"),
                    "image": show.get("image", {}).get("medium"),
                    "officialSite": show.get("officialSite"),
                    "tvmaze_url": show.get("url"),
                }
        except Exception as e:
            logging.warning(f"TVmaze lookup failed for {search_name}: {e}")
    with open(output_json, "w") as f:
        json.dump(tvmaze_data, f, indent=2)
    logging.info(f"TVmaze info saved to {output_json}")


def generate_playlist_and_json(
    acestream_data, playlist_filename, json_filename, server_ip
):
    base_url = f"http://{server_ip}/ace/getstream?id="
    # Deduplicate by AceStream ID, keep first occurrence
    seen = set()
    deduped = []
    for acestream_id, text_content in acestream_data:
        if acestream_id not in seen:
            deduped.append((acestream_id, text_content))
            seen.add(acestream_id)
    # Write .m3u8 playlist
    with open(playlist_filename, "w") as f:
        for acestream_id, text_content in deduped:
            f.write(f"#EXTINF:-1,{text_content}\n")
            f.write(f"{base_url}{acestream_id}\n")
    # Write .json file
    channels_json = [
        {"id": acestream_id, "title": text_content}
        for acestream_id, text_content in deduped
    ]
    with open(json_filename, "w") as f:
        json.dump(channels_json, f, indent=2)
    # Fetch TVmaze info for channels only if API key is set
    if os.getenv("TVMAZE_API_KEY"):
        fetch_tvmaze_info(channels_json)
    else:
        logging.info("TVMAZE_API_KEY not set, skipping TVmaze info fetch.")


def update_index_html(server_ip, html_path="index.html"):
    # Replace the __SERVER_IP__ placeholder in index.html with the actual server_ip
    try:
        with open(html_path, "r") as f:
            html = f.read()
        html = html.replace("__SERVER_IP__", server_ip.split(":")[0])
        with open(html_path, "w") as f:
            f.write(html)
        logging.info(f"Updated {html_path} with server IP: {server_ip}")
    except Exception as e:
        logging.error(f"Failed to update {html_path}: {e}")


def background_scraper():
    logging.info("\n" + "*" * 50)
    logging.info("Starting AceStream Link Scraper...")
    send_ntfy_notification(
        "AceStream Link Scraper", "Starting AceStream Link Scraper..."
    )
    logging.info("*" * 50 + "\n")

    search_queries = os.getenv("SEARCH_QUERIES", "[US],[UK],DAZN,Eleven,ESPN").split(
        ","
    )
    update_interval = int(os.getenv("UPDATE_INTERVAL", 360)) * 60
    server_ip = os.getenv("SERVER_IP", "localhost:6878")

    while True:
        all_channels = []
        for query in search_queries:
            acestream_data = collect_acestream_ids(query)
            if acestream_data:
                logging.info(
                    f"Found {len(acestream_data)} entries for query '{query.strip('[]')}'"
                )
                all_channels.extend(acestream_data)
        if all_channels:
            generate_playlist_and_json(
                all_channels, "playlist.m3u8", "channels.json", server_ip
            )
            update_index_html(server_ip)
            logging.info(
                f"\nGenerated playlist.m3u8, channels.json, and updated index.html with {len(all_channels)} entries."
            )
        else:
            logging.info("No channels found for any query.")
        logging.info(
            f"Waiting for {update_interval / 3600} hours before next update...\n"
        )
        send_ntfy_notification(
            "AceStream Link Scraper",
            f"Updated playlist with {len(all_channels)} channels.",
        )
        time.sleep(update_interval)


def main():
    server_ip = os.getenv("SERVER_IP", "localhost:6878")
    api_ip = os.getenv("API_SERVER_IP", server_ip)

    if not check_server_version(api_ip):
        logging.error("Server version check failed. Exiting...")
        send_ntfy_notification(
            "AceStream Link Scraper", "Server version check failed. Exiting..."
        )
        return

    # Run the scraper in the main thread
    background_scraper()


if __name__ == "__main__":
    main()
