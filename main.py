import requests
from bs4 import BeautifulSoup
import time
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    logging.info(f"Testing {acestream_title}")
    test_url = f"http://{server_ip}/ace/manifest.m3u8?id={acestream_id}"
    logging.info(f"URL: {test_url}")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(test_url, timeout=timeout)
            if response.status_code == 200:
                logging.info(f"{acestream_title} is ✅")
                return True
            else:
                logging.warning(f"❌ ConnectionError: {acestream_title}, Status code: {response.status_code}")
        except requests.RequestException as e:
            logging.error(f"❌ RequestException: {acestream_title}, Exception: {e}")
        time.sleep(delay)
    return False

def generate_m3u8_file(acestream_data, filename, server_ip):
    base_url = f"http://{server_ip}/ace/getstream?id="
    with open(filename, 'w') as f:
        f.write("#EXTM3U\n")
        for acestream_id, text_content in acestream_data:
            f.write(f"#EXTINF:-1,{text_content}\n")
            f.write(f"{base_url}{acestream_id}\n")

def check_acestream_version(server_ip):
    url = f"http://{server_ip}/webui/api/service?method=get_version"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('result', {}).get('version')
    except requests.RequestException as e:
        logging.error(f"Error checking AceStream version: {e}")
        return None

def main():
    logging.info("Starting AceStream playlist generator...")
    
    search_queries = os.getenv('SEARCH_QUERIES', '[US],[UK], DAZN').split(',')
    update_interval = int(os.getenv('UPDATE_INTERVAL', 360)) * 60
    server_ip = os.getenv('SERVER_IP', '10.10.10.5:6878')
    output_filename = os.getenv('OUTPUT_FILENAME', 'playlist/output.m3u8')
    test_delay = int(os.getenv('TEST_DELAY', 5))
    timeout = int(os.getenv('TIMEOUT', 10))

    while True:
        version = check_acestream_version(server_ip)
        if version:
            logging.info(f"AceStream is ready! Version: {version}")
            break
        else:
            logging.info("AceStream is not ready yet. Retrying in 5 seconds...")
            time.sleep(5)

    while True:
        all_acestream_data = []
        for query in search_queries:
            acestream_data = collect_acestream_ids(query)
            all_acestream_data.extend(acestream_data)

        all_acestream_data.sort(key=lambda x: x[1])

        logging.info(f"Found {len(all_acestream_data)} links. Estimated time to test: {len(all_acestream_data) * test_delay} seconds.")

        working_acestream_data = [data for data in all_acestream_data if test_acestream_link(data[0], data[1], server_ip, timeout, test_delay)]

        generate_m3u8_file(working_acestream_data, output_filename, server_ip)

        logging.info(f"Generated {output_filename} with {len(working_acestream_data)} entries.")
        
        time.sleep(update_interval)

if __name__ == "__main__":
    main()
