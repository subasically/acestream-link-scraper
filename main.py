import requests
from bs4 import BeautifulSoup
import time
import os


def collect_acestream_ids(search_query):
    print(f"Search for {search_query}")
    url = f"https://acestreamsearch.net/en/?q={search_query}"
    response = requests.get(url)
    response.raise_for_status()  # Ensure we notice bad responses
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all links containing "acestream://"
    acestream_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith('acestream://'):
            acestream_id = href.replace('acestream://', '')
            text_content = link.get_text(strip=True)
            acestream_links.append((acestream_id, text_content))
    
    return acestream_links

# Define the function to test if an AceStream link works with timeout
def test_acestream_link(acestream_id, server_ip, timeout=10):
    print(f"Testing {acestream_id}")
    test_url = f"http://{server_ip}/ace/manifest.m3u8?id={acestream_id}"
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(test_url, timeout=timeout)
            if response.status_code == 200:
                return True
            else:
                print(f"Failed: {acestream_id}, Status code: {response.status_code}")
        except requests.RequestException as e:
            print(f"Failed: {acestream_id}, Exception: {e}")
        time.sleep(5)  # Optional: Wait a bit before retrying
    return False

# Define the function to generate the .m3u8 file
def generate_m3u8_file(acestream_data, filename, server_ip):
    base_url = f"http://{server_ip}/ace/manifest.m3u8?id="
    with open(filename, 'w') as f:
        f.write("#EXTM3U\n")
        for acestream_id, text_content in acestream_data:
            f.write(f"#EXTINF:-1,{text_content}\n")
            f.write(f"{base_url}{acestream_id}\n")

def main():
    print("AceStream Link Scraper starting...")
    search_queries = os.getenv('SEARCH_QUERIES', 'sport,sky,f1').split(',')
    update_interval = int(os.getenv('UPDATE_INTERVAL', 3600))  # Default to 1 hour
    server_ip = os.getenv('SERVER_IP', '10.10.10.5:6768')  # Default IP

    while True:
        all_acestream_data = []
        for query in search_queries:
            acestream_data = collect_acestream_ids(query)
            all_acestream_data.extend(acestream_data)

        all_acestream_data.sort(key=lambda x: x[1])
        working_acestream_data = [data for data in all_acestream_data if test_acestream_link(data[0], server_ip)]

        output_filename = 'output/output.m3u8'
        generate_m3u8_file(working_acestream_data, output_filename, server_ip)

        print(f"Generated {output_filename} with {len(working_acestream_data)} entries.")
        
        time.sleep(update_interval)

if __name__ == "__main__":
    main()
