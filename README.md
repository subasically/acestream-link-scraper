# AceStream Link Scraper

A comprehensive Python-based tool that scrapes AceStream links from acestreamsearch.net, generates M3U8 playlists, and provides a web-based player interface with HLS proxy support for secure HTTPS streaming.

## Features

- **Automated Scraping**: Scrapes AceStream links from acestreamsearch.net based on customizable search queries
- **Playlist Generation**: Creates M3U8 playlists and JSON channel lists with automatic deduplication
- **Web Player**: Beautiful web interface with Video.js player for browsing and watching channels
- **HLS Proxy**: Flask-based proxy server to rewrite HTTP streams to HTTPS for secure playback
- **TVmaze Integration**: Optional TV show metadata and images using TVmaze API
- **Notifications**: ntfy.sh integration for status updates and alerts
- **Multi-Service Architecture**: Runs scraper, Flask proxy, and nginx in a single container using supervisord
- **Configurable**: Flexible environment variable configuration for all aspects

## Architecture

The project consists of three main components running under supervisord:

1. **Scraper** (`main.py`): Periodically scrapes AceStream links and generates playlists
2. **Flask Proxy** (`proxy.py`): Proxies and rewrites manifest URLs from HTTP to HTTPS
3. **Nginx**: Serves the web UI and static files (playlists, JSON)

## Requirements

- Docker
- Docker Compose
- AceStream HTTP Proxy (e.g., ghcr.io/martinbjeldbak/acestream-http-proxy)

## Environment Variables

- `UPDATE_INTERVAL`: Interval (in minutes) between scraping updates (default: 360 minutes / 6 hours)
- `SERVER_IP`: The public server IP/domain for HTTPS streaming URLs
- `API_SERVER_IP`: Internal AceStream proxy server address (default: same as SERVER_IP)
- `SEARCH_QUERIES`: Comma-separated list of search queries (default: `[US],[UK],DAZN,Eleven,ESPN`)
- `TVMAZE_API_KEY`: Optional TVmaze API key for show metadata and images
- `FLASK_APP`: Flask app module (default: `proxy.py`)

## Usage

1. **Clone the repository**:
    ```bash
    git clone https://github.com/subasically/acestream-link-scraper.git
    cd acestream-link-scraper
    ```

2. **Configure environment variables**: Create a `.env` file or set environment variables for `SERVER_IP` and optionally `TVMAZE_API_KEY`

3. **Build and run with Docker Compose**:
    ```bash
    docker-compose up -d --build
    ```

4. **Access the web interface**: Open your browser to `http://localhost:8500`

## Docker Compose Example

```yaml
services:
  scraper-web:
    image: ghcr.io/subasically/acestream-link-scraper:latest
    container_name: scraper-web
    environment:
      - UPDATE_INTERVAL=4320  # 3 days in minutes
      - SERVER_IP=${SERVER_IP}  # Your public domain/IP
      - API_SERVER_IP=acestream-proxy:6878  # Internal AceStream proxy
      - SEARCH_QUERIES=[UK],[US],DAZN,Eleven,ESPN,Bein,Arena Sport,EuroSport,Nova Sport,polsat sport
      - TVMAZE_API_KEY=${TVMAZE_API_KEY}  # Optional
      - FLASK_APP=proxy.py
    ports:
      - "8500:80"    # Web UI
      - "8888:8080"  # HLS Proxy
    depends_on:
      - acestream-proxy
      
  acestream-proxy:
    image: ghcr.io/martinbjeldbak/acestream-http-proxy
    container_name: acestream-http-proxy
    ports:
      - "6878:6878"
```

## How It Works

1. **Scraping**: The scraper queries acestreamsearch.net with configured search terms and collects AceStream IDs
2. **Playlist Generation**: Creates `data/playlist.m3u8` and `data/channels.json` with all discovered channels
3. **Web Interface**: Nginx serves `index.html` which loads channels and provides a Video.js player
4. **HLS Proxy**: Flask proxy at port 8080 intercepts manifest requests, fetches from AceStream proxy, and rewrites HTTP URLs to HTTPS
5. **Metadata**: If TVMAZE_API_KEY is set, fetches show information and images for each channel

## Files Generated

- `data/playlist.m3u8`: M3U8 playlist file with all channels
- `data/channels.json`: JSON array of channel objects with IDs and titles
- `tvmaze.json`: TV show metadata (if TVmaze API key is configured)
- `index.html`: Updated with correct server IP for streaming

## Ports

- **Port 8500** (external) → 80 (container): Nginx web server serving the UI and static files
- **Port 8888** (external) → 8080 (container): Flask HLS proxy server that rewrites AceStream manifest URLs from HTTP to HTTPS
- **Port 6878**: AceStream HTTP proxy (separate container)

The Flask proxy on port 8888 is critical for secure playback - it intercepts HLS manifest requests, fetches them from the AceStream proxy, and rewrites all HTTP stream URLs to HTTPS before sending to the player.

## Notes

- The scraper runs continuously and updates playlists based on `UPDATE_INTERVAL`
- Notifications are sent via ntfy.sh when scraping completes or errors occur
- Channel mapping can be customized in `tvmaze_channel_map.json` to improve metadata matching