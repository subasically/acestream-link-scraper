[![Publish to Docker Hub](https://github.com/subasically/acestream-link-scraper/actions/workflows/main.yaml/badge.svg)](https://github.com/subasically/acestream-link-scraper/actions/workflows/main.yaml)

# AceStream Link Scraper

The AceStream Link Scraper is a Python script that collects AceStream IDs based on search queries and generates an `.m3u8` playlist file. It periodically tests the working status of AceStream links and updates the playlist.

## Usage

1. **Install the required dependencies**:
   ```bash
   pip install requests beautifulsoup4
   ```

2. **Set environment variables**:
   - `SEARCH_QUERIES`: Comma-separated search queries (e.g., "sport,sky,f1").
   - `UPDATE_INTERVAL`: Update interval in seconds (default: 3600 seconds).
   - `SERVER_IP`: AceStream server IP and port (default: "10.10.10.5:32768").

3. **Run the script**:
   ```bash
   python acestream_playlist.py
   ```

The generated `.m3u8` playlist will be saved in the `output` directory.

## Quick Start

Using Docker Compose is a three-step process:
1. Define your app's environment with a `Dockerfile` so it can be reproduced anywhere.
2. Define the services that make up your app in `compose.yaml` so they can be run together in an isolated environment.
3. Run `docker compose up`, and Compose will start and run your entire app.

A sample `compose.yaml` file looks like this:

```yaml
services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - .:/code
  redis:
    image: redis
```

## Contributing

Want to help develop Docker Compose? Check out our [contributing documentation](https://github.com/docker/compose/blob/v2/CONTRIBUTING.md). If you find an issue, please report it on the [issue tracker](https://github.com/docker/compose/issues).

---

Feel free to customize the script and adapt it to your requirements! If you have any questions or need further assistance, feel free to ask. 😊🐳