# Voz.vn Thread Scraper

A robust, multi-threaded, and rate-limit aware Python tool to scrape posts/comments from any thread on `voz.vn` using the **Browserless Smart Scrape API**.

This tool leverages the smart capabilities of Browserless to fetch pages efficiently (escalating to headless browsers and proxies automatically only when blocked), extracts comments and body images using `BeautifulSoup4`, and saves the results directly into structured `JSON` or `CSV` formats.

## Key Features

- **Automatic Thread Title & Pagination Detection**: Simply pass the thread URL, and the tool dynamically identifies the total number of pages and the topic title.
- **Concurrently Accelerated Scraping**: Fetch multiple pages simultaneously using a configurable thread pool.
- **Resilient Retry Mechanism**: Automatically detects errors (such as HTTP 429 rate-limiting responses) and performs backoff retries to ensure no page is left behind.
- **Image URL Extraction & Downloading**: Automatically parses image URLs within post bodies (excluding smilies). Download them locally with a dedicated flag.
- **Interactive Reactions Bar & Modal Overlay**: Scrapes post reactions (including user lists and reaction types) and displays them inside a premium, clickable in-page modal popup overlay just like the real Voz forum.
- **Unicode-safe output**: Exports clean, fully formatted Vietnamese characters to standard JSON or CSV (using UTF-8 with BOM for correct Microsoft Excel display).
- **Custom Range Control**: Allows scraping specific page sub-ranges.

## Installation

Ensure you have Python 3 installed. Then install the required dependencies:

```bash
pip install requests beautifulsoup4
```

## Quick Testing Commands

To quickly test the application, run these preconfigured commands:

### 1. Test Scrape (Pages 1 to 2, No Image Downloads)
Fetches pages 1 and 2, parsing comments and image URLs into `comments.json`:
```bash
python scrape_voz.py --url "https://voz.vn/t/28-tuoi-da-bi-coi-la-mat-gia-khi-phu-nu-bi-dinh-gia-bang-so-tuoi.1236656/" --start-page 1 --end-page 2
```

### 2. Test Scrape with Image Downloads (Pages 1 to 2)
Fetches pages 1 and 2, parses them, and downloads all post body images concurrently into the `images/` directory:
```bash
python scrape_voz.py --url "https://voz.vn/t/28-tuoi-da-bi-coi-la-mat-gia-khi-phu-nu-bi-dinh-gia-bang-so-tuoi.1236656/" --start-page 1 --end-page 2 --download-images
```

### 3. Open Thread Viewer
After running one of the above commands, open `index.html` in your browser. It automatically detects and displays the posts from the scraped `comments.json`. If you enabled `--download-images`, it seamlessly displays the downloaded local copies!

---

## Usage (Full Scrape)

### Simple Scrape (All Pages)
Run the script passing the base/first page URL of the thread:

```bash
python scrape_voz.py --url "https://voz.vn/t/28-tuoi-da-bi-coi-la-mat-gia-khi-phu-nu-bi-dinh-gia-bang-so-tuoi.1236656/" --download-images
```

*This will automatically detect the total number of pages (e.g. 103), scrape all of them, download all embedded images to the `images` folder, and save everything into `comments.json`.*

### Advanced Options

You can customize the scraping behavior using command-line arguments:

```bash
python scrape_voz.py --url <THREAD_URL> \
  --token <YOUR_BROWSERLESS_TOKEN> \
  --start-page 1 \
  --end-page 10 \
  --output "voz_comments.csv" \
  --concurrency 5 \
  --download-images
```

### Argument Reference

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--url` | **(Required)** The URL of the thread's first page or the base thread URL. | - |
| `--token` | Your Browserless API key token. | *(Pre-filled with your provided token)* |
| `--start-page` | The page number to start scraping from. | `1` |
| `--end-page` | The page number to stop scraping (inclusive). | *Auto-detected last page* |
| `--output` | Destination file name. Supports `.json` and `.csv` formats. | `comments.json` |
| `--concurrency` | Number of parallel page fetches. Adjust lower if encountering heavy rate-limiting. | `5` |
| `--download-images` | If passed, downloads all parsed post images concurrently into a local `images` folder. | `False` |
