# Voz.vn Thread Scraper & Explorer

A robust, multi-threaded, and rate-limit aware Python tool to scrape posts/comments from any thread on `voz.vn` using the **Browserless Smart Scrape API**, combined with a stunning Web Control Panel and a central landing dashboard to explore all your offline-saved threads.

This tool leverages the smart capabilities of Browserless to fetch pages efficiently (escalating to headless browsers and proxies automatically only when blocked), extracts comments and body images using `BeautifulSoup4`, and saves the results into self-contained directories. The entire application is fully optimized for offline usage, allowing you to double-click pages in Windows Explorer and read threads instantly without any CORS issues, or host them locally under a unified origin.

---

## Key Features

- **Retro Glassmorphic Web Control Panel**: A premium, highly responsive graphical dashboard to trigger, customize, and monitor scraper runs from your web browser.
- **Dynamic CLI-to-UI Mapping**: Choose options like "Tải Ảnh Đính Kèm" (Download Images), "Thu Thập Phản Hồi" (Fetch Reactions), and "Ghi Đè Toàn Bộ" (Force Overwrite) via simple tick boxes and specify scraping page ranges inside input boxes.
- **Unbuffered Live Subprocess Terminal Console**: Streams command-line outputs (stdout and stderr) line-by-line in real-time to the web terminal console widget utilizing Server-Sent Events (SSE).
- **Real-Time Progress Bar Tracking**: Automatically parses scraper progress headers in the logs to render fluid progress bar percentages.
- **Unified Origin Thread Explorer**: Serves both the scraper control panel and the static explorer landing page under the same local address (`http://127.0.0.1:5000` and `/explorer`), natively satisfying all browser local security policies (CORS) when loading dynamic comments databases.
- **Multi-Thread Directory Architecture**: Organizes scraped threads inside a global `threads/` folder. Threads are named using a normalized alphanumeric slug of the first 20 characters of their title together with their thread ID, using a Unicode horizontal ellipsis (`…`) for titles longer than 20 characters (e.g. `threads/1236656_28-tuoi-da-bi-coi-la…/`).
- **Zero-Setup Offline CORS Bypass**: Saves scraped data as executable local scripts (`comments.js` in thread folders, and `threads.js` in the root folder) in addition to `.json` databases. The HTML files load these scripts dynamically, completely bypassing local browser origin security policy (CORS) blocks under the `file://` protocol.
- **Root Thread Explorer Landing Dashboard (`index.html`)**: A premium XenForo-style landing dashboard that auto-loads all downloaded threads in a clean, filterable table showing numberings, titles, page metrics (downloaded vs total pages), total comment counts, and last scraped times.
- **Self-Contained Thread Viewer**: Copies a master template into `threads/<folder>/index.html` after every scrape. Clicking a thread link inside the explorer instantly opens the thread viewer locally to display posts, reaction overlays, and embedded media.
- **Automatic Thread Title & Pagination Detection**: Simply pass the thread URL, and the tool dynamically identifies the total number of pages and the topic title.
- **Concurrently Accelerated Scraping**: Fetch multiple pages simultaneously using a configurable thread pool.
- **Resilient Retry Mechanism**: Automatically detects errors (such as HTTP 429 rate-limiting responses) and performs backoff retries to ensure no page is left behind.
- **Incremental Resume Mode with Incomplete & Last-Page Auto-checking**: Scans the existing `comments.json` on startup and skips fully scraped pages. It automatically detects and re-scrapes incomplete pages (with fewer than 20 comments) and the highest active page to fetch new comments, deleted comments, edits, or updated reactions without scraping everything again.
- **Unique Image Deduplication via MD5 Hashing**: Deduplicates image downloads using URL hashing to prevent downloading identical files (like forum graphics and user badges) multiple times.
- **Failed Pages Logging**: Automatically writes failed page numbers to `scrape_failed_pages.log` for easy troubleshooting, and automatically deletes the log once a run completes with zero failures.
- **Interactive Reactions Bar & Modal Overlay**: Scrapes post reactions (including user lists and reaction types) and displays them inside a premium, clickable in-page modal popup overlay with auto-numbering.

---

## Directory Structure

```
Scrape-Voz/
├── app.py                      (Flask Server hosting control panel, explorer, and SSE logging)
├── requirements.txt            (Project Python dependencies)
├── index.html                  (Stunning Root Thread Explorer landing page)
├── threads.js                  (Statically loaded root database index)
├── threads.json                (Index database backup file)
├── thread_viewer.html          (Master XenForo comments/reactions viewer template)
├── templates/
│   └── scraper_ui.html         (Stunning Scraper Dashboard and Live Log stream template)
└── threads/
    └── [thread_folder]/        (Named as <thread_id>_<normalized_title_slug>…)
        ├── index.html          (Self-contained viewer copy)
        ├── comments.js         (Statically loaded thread database script)
        ├── comments.json       (Thread posts database backup)
        └── images/             (Concurrently downloaded, MD5-deduplicated post images)
```

---

## Installation

Ensure you have Python 3 installed. Then install the project dependencies:

```bash
pip install -r requirements.txt
```

---

## Web Control Panel Usage (Recommended)

To start the local web application server:

```bash
python app.py
```

After launching, navigate your browser to:
- **Control Panel Dashboard**: [http://127.0.0.1:5000/](http://127.0.0.1:5000/) - Configure settings, input URLs, and run the scraper with live log streaming.
- **Thread Explorer Library**: [http://127.0.0.1:5000/explorer](http://127.0.0.1:5000/explorer) - Explore all offline-saved threads dynamically under a unified origin.

---

## Command Line Interface (CLI) Usage

You can still execute the scraper directly from your terminal.

### 1. Test Scrape (Pages 1 to 2, No Image Downloads)
```bash
python scrape_voz.py --url "https://voz.vn/t/28-tuoi-da-bi-coi-la-mat-gia-khi-phu-nu-bi-dinh-gia-bang-so-tuoi.1236656/" --start-page 1 --end-page 2
```

### 2. Test Scrape with Image Downloads (Pages 1 to 2)
```bash
python scrape_voz.py --url "https://voz.vn/t/28-tuoi-da-bi-coi-la-mat-gia-khi-phu-nu-bi-dinh-gia-bang-so-tuoi.1236656/" --start-page 1 --end-page 2 --download-images
```

### 3. Simple Scrape (All Pages)
```bash
python scrape_voz.py --url "https://voz.vn/t/28-tuoi-da-bi-coi-la-mat-gia-khi-phu-nu-bi-dinh-gia-bang-so-tuoi.1236656/" --download-images
```

### 4. Advanced CLI Options
```bash
python scrape_voz.py --url <THREAD_URL> \
  --token <YOUR_BROWSERLESS_TOKEN> \
  --start-page 1 \
  --end-page 10 \
  --output "comments.json" \
  --concurrency 5 \
  --download-images
```

### Argument Reference

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--url` | **(Required)** The URL of the thread's first page or the base thread URL. | - |
| `--token` | Your Browserless API key token. | *Pre-filled from `.env`* |
| `--start-page` | The page number to start scraping from. | `1` |
| `--end-page` | The page number to stop scraping (inclusive). | *Auto-detected last page* |
| `--output` | Destination file name inside the thread directory. Supports `.json` and `.csv`. | `comments.json` |
| `--concurrency` | Number of parallel page fetches. Adjust lower if rate-limited. | `5` |
| `--download-images` | Concurrently download embedded images into the thread folder's `images/` directory. | `False` |
| `--fetch-reactions` | Concurrently fetch the complete list of reacted users from Voz (slows down scraping). | `False` |
| `--force` | Force a fresh scrape of all pages, completely overwriting the existing cache. | `False` |
