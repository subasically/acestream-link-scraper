import requests
from bs4 import BeautifulSoup
import time
import os
import logging
import json
from ntfy import send_ntfy_notification

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def check_server_version(server_ip, max_retries=30, timeout=5):
    logging.info("Checking server version...")
    for attempt in range(max_retries):
        try:
            version_check_url = f"http://{server_ip}/webui/api/service?method=get_version"
            response = requests.get(version_check_url, timeout=timeout)
            response.raise_for_status()  # Raise an exception for HTTP errors

            version_data = response.json()
            if 'result' in version_data and 'version' in version_data['result']:
                version = version_data['result']['version']
                logging.info(f"Server is up and running on version: {version}")
                return version
            else:
                logging.warning(f"Version key not found in the response. {version_data}")
        except requests.RequestException as e:
            logging.error(f"Attempt {attempt + 1} of {max_retries}: Error fetching version - {e}")

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

    soup = BeautifulSoup(response.text, 'html.parser')
    acestream_links = [(link['href'].replace('acestream://', ''), link.get_text(strip=True))
                       for link in soup.find_all('a', href=True) if link['href'].startswith('acestream://')]
    return acestream_links

def generate_playlist_and_json(acestream_data, playlist_filename, json_filename, server_ip):
    base_url = f"http://{server_ip}/ace/getstream?id="
    # Write .m3u8 playlist
    with open(playlist_filename, 'w') as f:
        for acestream_id, text_content in acestream_data:
            f.write(f"#EXTINF:-1,{text_content}\n")
            f.write(f"{base_url}{acestream_id}\n")
    # Write .json file
    channels_json = [
        {"id": acestream_id, "title": text_content}
        for acestream_id, text_content in acestream_data
    ]
    with open(json_filename, 'w') as f:
        json.dump(channels_json, f, indent=2)

def background_scraper():
    logging.info("\n" + "*" * 50)
    logging.info("Starting AceStream playlist generator...")
    send_ntfy_notification("AceStream Playlist Generator", "Starting AceStream playlist generator...")
    logging.info("*" * 50 + "\n")
    
    search_queries = os.getenv('SEARCH_QUERIES', '[US],[UK],DAZN,Eleven,ESPN').split(',')
    update_interval = int(os.getenv('UPDATE_INTERVAL', 360)) * 60
    server_ip = os.getenv('SERVER_IP', 'localhost:6878')

    while True:
        all_channels = []
        for query in search_queries:
            acestream_data = collect_acestream_ids(query)
            if acestream_data:
                logging.info(f"Found {len(acestream_data)} entries for query '{query.strip('[]')}'")
                all_channels.extend(acestream_data)
        if all_channels:
            generate_playlist_and_json(
                all_channels,
                "playlist.m3u8",
                "channels.json",
                server_ip
            )
            logging.info(f"\nGenerated playlist.m3u8 and channels.json with {len(all_channels)} entries.")
        else:
            logging.info("No channels found for any query.")
        logging.info(f"Waiting for {update_interval / 3600} hours before next update...\n")
        send_ntfy_notification("AceStream Playlist Generator", f"Updated playlist with {len(all_channels)} channels.")
        time.sleep(update_interval)

def main():
    server_ip = os.getenv('SERVER_IP', 'localhost:6878')
    if not check_server_version(server_ip):
        logging.error("Server version check failed. Exiting...")
        send_ntfy_notification("AceStream Playlist Generator", "Server version check failed. Exiting...")
        return

    # Run the scraper in the main thread
    background_scraper()

if __name__ == "__main__":
    main()
