import requests
from bs4 import BeautifulSoup
import time
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

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
    # logging.info(f"Testing {acestream_title}")
    test_url = f"http://{server_ip}/ace/manifest.m3u8?id={acestream_id}"
    # logging.info(f"URL: {test_url}")
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
    # create empty file
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

def generate_index_html(filename):
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HLS Video Player</title>
<link href="https://vjs.zencdn.net/7.14.3/video-js.css" rel="stylesheet">
<script src="https://vjs.zencdn.net/7.14.3/video.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/videojs-contrib-hls/5.15.0/videojs-contrib-hls.min.js"></script>
</head>
<body>
<video id="hls-video" class="video-js vjs-default-skin" controls preload="auto" width="640" height="360">
    <source src="{filename}" type="application/x-mpegURL">
</video>

<script>
    var player = videojs('hls-video');
</script>
</body>
</html>
"""
    with open("index.html", "w") as f:
        f.write(html_content)
    
def main():
    logging.info("\n" + "*" * 50)
    logging.info("Starting AceStream playlist generator...")
    logging.info("*" * 50 + "\n")
    
    search_queries = os.getenv('SEARCH_QUERIES', '[US],[UK],DAZN,Eleven').split(',')
    update_interval = int(os.getenv('UPDATE_INTERVAL', 360)) * 60
    server_ip = os.getenv('SERVER_IP', '10.10.10.5:6878')
    playlist = os.getenv('PLAYLIST_FILENAME', 'output.m3u8')
    test_delay = int(os.getenv('TEST_DELAY', 5))
    timeout = int(os.getenv('TIMEOUT', 10))

    while True:
        all_acestream_data = []
        for query in search_queries:
            acestream_data = collect_acestream_ids(query)
            all_acestream_data.extend(acestream_data)

        all_acestream_data.sort(key=lambda x: x[1])

        logging.info(f"Found {len(all_acestream_data)} links. Estimated time to test: {len(all_acestream_data) * test_delay} seconds.\n")

        working_acestream_data = [data for data in all_acestream_data if test_acestream_link(data[0], data[1], server_ip, timeout, test_delay)]

        generate_m3u8_file(working_acestream_data, playlist, server_ip)
        logging.info(f"\nGenerated {playlist} with {len(working_acestream_data)} entries.")
        
        generate_index_html(playlist)
        logging.info(f"Generated index.html for web player.\n")
        
        logging.info(f"Waiting for {update_interval /3600} hourse before next update...\n")
        time.sleep(update_interval)

if __name__ == "__main__":
    main()
