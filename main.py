import requests
from bs4 import BeautifulSoup
import time
import os

def collect_acestream_ids(search_query):
    print(f"Search for {search_query}")
    url = f"https://acestreamsearch.net/en/?q={search_query}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Ensure we notice bad responses
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for query '{search_query}': {e}")
        return []

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

# Define the function to test if an AceStream link works with timeout and delay
def test_acestream_link(acestream_id, server_ip, timeout, delay):
    print(f"Testing {acestream_id}")
    test_url = f"http://{server_ip}/ace/manifest.m3u8?id={acestream_id}"
    print(f"Testing URL:\n{test_url}")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(test_url, timeout=timeout)
            if response.status_code == 200:
                print(f"{test_url} is ✅")
                return True
            else:
                print(f"❌Failed: {acestream_id}\nStatus code:\n{response.status_code}")
        except requests.RequestException as e:
            print(f"❌Failed: {acestream_id}\nException:\n{e}")
        time.sleep(delay)
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
    search_queries = os.getenv('SEARCH_QUERIES', 'sport,sky,f1').split(',')
    update_interval = int(os.getenv('UPDATE_INTERVAL', 360)) * 60  # Default to 6 hours (converted to seconds)
    server_ip = os.getenv('SERVER_IP', '10.10.10.5:6878')  # Default IP
    output_filename = os.getenv('OUTPUT_FILENAME', 'playlist/output.m3u8')  # Default output filename
    test_delay = int(os.getenv('TEST_DELAY', 5))  # Default delay between tests is 5 seconds
    timeout = int(os.getenv('TIMEOUT', 10))  # Default timeout for testing links is 10 seconds

    while True:
        all_acestream_data = []
        for query in search_queries:
            acestream_data = collect_acestream_ids(query)
            all_acestream_data.extend(acestream_data)

        all_acestream_data.sort(key=lambda x: x[1])

        print(f"Found {len(all_acestream_data)} links. Estimated time to test: {len(all_acestream_data) * test_delay} seconds.")

        working_acestream_data = [data for data in all_acestream_data if test_acestream_link(data[0], server_ip, timeout, test_delay)]

        generate_m3u8_file(working_acestream_data, output_filename, server_ip)

        print(f"Generated {output_filename} with {len(working_acestream_data)} entries.")
        
        time.sleep(update_interval)

if __name__ == "__main__":
    main()
