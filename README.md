# AceStream Link Scraper

AceStream Link Scraper is a Python-based tool that scrapes AceStream links from a specified website, tests the validity of each link, and generates an M3U8 playlist file. This tool is packaged in a Docker container and can be configured using environment variables.

## Features

- Scrapes AceStream links from a specified search website.
- Tests each AceStream link to ensure it's working.
- Generates an M3U8 playlist file with valid AceStream links.
- Configurable through environment variables for flexible usage.
- Packaged in a Docker container for easy deployment.

## Requirements

- Docker
- Docker Compose

## Environment Variables

- `UPDATE_INTERVAL`: Interval (in minutes) between updates (default: 360 minutes / 6 hours).
- `SERVER_IP`: The server IP for testing AceStream links (default: `10.10.10.5:32768`).
- `SEARCH_QUERIES`: Comma-separated list of search queries (default: `sport,sky,f1`).
- `PLAYLIST_FILENAME`: The name of the output M3U8 file (default: `output.m3u8`).
- `TEST_DELAY`: Delay (in seconds) between testing each link (default: 5 seconds).
- `TIMEOUT`: Timeout (in seconds) for testing each link (default: 10 seconds).

## Usage

1. **Clone the repository**:
    ```bash
    git clone https://github.com/subasically/acestream-link-scraper.git
    cd acestream-link-scraper
    ```

2. **Build the Docker image**:
    ```bash
    docker-compose build
    ```

3. **Run the Docker container**
    ```bash
    docker-compose up
    ```

## Compose

```yaml
services:
  http-proxy:
    image: ghcr.io/martinbjeldbak/acestream-http-proxy
    ports:
      - '6878:80'
  link-scraper:
    depends_on:
      - http-proxy
    image: subasically/acestream-link-scraper
    environment:
      - UPDATE_INTERVAL=360  # Time in minutes between updates (default: 6 hours)
      - SERVER_IP=10.10.10.5:32768  # Default server IP
      - SEARCH_QUERIES=sport,sky,f1  # Default search queries
      - PLAYLIST_FILENAME=output.m3u8  # Default output filename
      - TEST_DELAY=5  # Default delay between tests in seconds
      - TIMEOUT=10  # Default timeout for testing links in seconds
    volumes:
      - /home/directory/:/usr/src/app # Change home directory to your local directory
```