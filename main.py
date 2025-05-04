import requests
from bs4 import BeautifulSoup
import time
import os
import logging
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

def test_acestream_link(acestream_id, acestream_title, server_ip, timeout, delay):
    test_url = f"http://{server_ip}/ace/manifest.m3u8?id={acestream_id}"
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(test_url, timeout=timeout)
            if response.status_code == 200:
                logging.info(f"✅ {acestream_title} is working!")
                return True
            else:
                logging.warning(f"❌ ConnectionError: {acestream_title} - {test_url}")
        except requests.RequestException as e:
            logging.error(f"❌ Exception: {acestream_title} - {test_url}")
        time.sleep(delay)
    return False

def generate_m3u8_file(acestream_data, filename, server_ip):
    base_url = f"http://{server_ip}/ace/getstream?id="
    with open(filename, 'w') as f:
        pass
    existing_ids = set()
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith(base_url):
                existing_ids.add(line.strip().replace(base_url, ''))
    
    with open(filename, 'a') as f:
        for acestream_id, text_content in acestream_data:
            if acestream_id not in existing_ids:
                f.write(f"#EXTINF:-1,{text_content}\n")
                f.write(f"{base_url}{acestream_id}\n")
    
def main():
    logging.info("\n" + "*" * 50)
    logging.info("Starting AceStream playlist generator...")
    send_ntfy_notification("AceStream Playlist Generator", "Starting AceStream playlist generator...")
    logging.info("*" * 50 + "\n")
    
    search_queries = os.getenv('SEARCH_QUERIES', '[US],[UK],DAZN,Eleven,ESPN').split(',')
    update_interval = int(os.getenv('UPDATE_INTERVAL', 360)) * 60
    server_ip = os.getenv('SERVER_IP', '10.10.10.5:6878')
    test_delay = int(os.getenv('TEST_DELAY', 5))
    timeout = int(os.getenv('TIMEOUT', 10))

    if not check_server_version(server_ip):
        logging.error("Server version check failed. Exiting...")
        send_ntfy_notification("AceStream Playlist Generator", "Server version check failed. Exiting...")
        return
    
    channels = []
    while True:
        for query in search_queries:
            acestream_data = collect_acestream_ids(query)
            if acestream_data:
                playlist_filename = f"{query.strip('[]')}.m3u8"
                generate_m3u8_file(acestream_data, playlist_filename, server_ip)
                channels.append(query.strip('[]'))
                logging.info(f"\nGenerated {playlist_filename} with {len(acestream_data)} entries.")
        
        logging.info(f"Waiting for {update_interval / 3600} hours before next update...\n")
        time.sleep(update_interval)

if __name__ == "__main__":
    main()
