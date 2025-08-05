
# Scraper

This repository contains Python scripts for automated retrieval and analysis of sitemaps from [OpenCorporates](https://opencorporates.com/).

P.S site aggresively bans multiple requests from same IP, so use of proxy is preferred.

## Contents
- `requirements.txt` — list of required Python libraries
- `worker.py` — temporal worker
- `client.py` — module for connection to Temporal Server
- `Dockerfile` — worker image build
- `docker-compose.yml` — workers queue and amount configuration
- `utils` — helper functions
- `activities` — Temporal activities
- `workflows` — Temporal workflows

## Installation

1. **Clone the repository:**
   ```bash
   git@github.com:shwachko/opencorporates-parser.git
   cd opencorporates-parser
   ```

2. **(Recommended) Create and activate a virtual environment:**
   ```bash
   python -m venv scraper_env
   # For Windows:
   .\scraper_env\Scripts\activate
   # For Linux/Mac:
   source scraper_env/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Create worker image:**
```bash 
docker build -t worker:latest .
```

2. **Run local Temporal Server:**
```bash 
temporal server start-dev
```

3. **Run docker-compose.yml with needed workers amount:**
```bash 
docker compose up --build --scale worker-fetch=10
```
4. **Go to Temporal UI or use Temporal CLI to start ParseSitemapLinksWorkflow with fetch-queue queue and such input:**
```bash 
{
  "main_link": "https://opencorporates.com/sitemap.xml.gz"
}
```
## How it works
- The `fetch_and_parse_gz_xml.py` activity automatically attempts to bypass protections (Cloudflare, Turnstile, math challenges) to retrieve the sitemap from OpenCorporates.
- After successfully obtaining a sitemap index, CrawlXMLWorkflow child workflows are created for each link to count US links, this number is returned to ParseSitemapLinksWorkflow which returns a total amount of US links.
