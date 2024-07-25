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
  server:
    image: ghcr.io/martinbjeldbak/acestream-http-proxy
    container_name: acestream-http-proxy
    ports:
      - "6878:80"

  app:
    image: ghcr.io/subasically/acestream-link-scraper
    container_name: acestream-link-scraper
    environment:
      - UPDATE_INTERVAL=60
      - SERVER_IP=server:6878
      - SEARCH_QUERIES=[UK],[US],DAZN,Eleven
      - PLAYLIST_FILENAME=output.m3u8
      - TEST_DELAY=1
      - TIMEOUT=10
      - TZ=America/Chicago
      - MAX_RETRIES=30
      - RETRY_DELAY=5
    volumes:
      - /home/subasically/appdata/acestream-link-scraper:/usr/src/app
```