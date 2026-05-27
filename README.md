# Voz.vn Thread Scraper & Explorer

A robust, multi-threaded, and rate-limit aware Python tool to scrape posts/comments from any thread on `voz.vn` using the **Browserless Smart Scrape API**, combined with a stunning local landing dashboard to explore all your offline-saved threads.

This tool leverages the smart capabilities of Browserless to fetch pages efficiently (escalating to headless browsers and proxies automatically only when blocked), extracts comments and body images using `BeautifulSoup4`, and saves the results into self-contained directories. The entire application is fully optimized for offline usage, allowing you to double-click pages in Windows Explorer and read threads instantly without any CORS issues or local web server requirements.

---

## Key Features

- **Multi-Thread Directory Architecture**: Organizes scraped threads inside a global `threads/` folder. Threads are named using a normalized alphanumeric slug of the first 10 characters of their title together with their thread ID (e.g. `threads/1236656_28-tuoi-da/`).
- **Zero-Setup Offline CORS Bypass**: Saves scraped data as executable local scripts (`comments.js` in thread folders, and `threads.js` in the root folder) in addition to `.json` databases. The HTML files load these scripts dynamically, completely bypassing local browser origin security policy (CORS) blocks under the `file://` protocol.
- **Root Thread Explorer Landing Dashboard (`index.html`)**: A premium XenForo-style landing dashboard that auto-loads all downloaded threads in a clean, filterable table showing numberings, titles, total comment counts, and last scraped times.
- **Self-Contained Thread Viewer**: Copies a master template into `threads/<folder>/index.html` after every scrape. Clicking a thread link inside the explorer instantly opens the thread viewer locally to display posts, reaction overlays, and embedded media.
- **Automatic Thread Title & Pagination Detection**: Simply pass the thread URL, and the tool dynamically identifies the total number of pages and the topic title.
- **Concurrently Accelerated Scraping**: Fetch multiple pages simultaneously using a configurable thread pool.
- **Resilient Retry Mechanism**: Automatically detects errors (such as HTTP 429 rate-limiting responses) and performs backoff retries to ensure no page is left behind.
- **Incremental Resume Mode with Incomplete & Last-Page Auto-checking**: Scans the existing `comments.json` on startup and skips fully scraped pages. It automatically detects and re-scrapes incomplete pages (with fewer than 20 comments) and the highest active page to fetch new comments, deleted comments, edits, or updated reactions without scraping everything again.
- **Immediate Save & Background Image Pipeline**: Saves comments to the output JSON and JS *first* (so they are immediately viewable), then runs concurrent image downloads in the background, updating final local file path maps afterwards.
- **Unique Image Deduplication via MD5 Hashing**: Deduplicates image downloads using URL hashing to prevent downloading identical files (like forum graphics and user badges) multiple times. Safely bypasses base64 / SVG data URIs.
- **Failed Pages Logging**: Automatically writes failed page numbers to `scrape_failed_pages.log` for easy troubleshooting, and automatically deletes the log once a run completes with zero failures.
- **Interactive Reactions Bar & Modal Overlay**: Scrapes post reactions (including user lists and reaction types) and displays them inside a premium, clickable in-page modal popup overlay with auto-numbering.
- **Unicode-safe output**: Exports clean, fully formatted Vietnamese characters to standard JSON, JS, or CSV (using UTF-8 with BOM for correct Microsoft Excel display).
- **Custom Range Control**: Allows scraping specific page sub-ranges.
- **Adaptive Image Fitting & Dynamic Viewer Fallbacks**: Displays comments with native browser `loading="lazy"` to fetch assets on-demand. Includes an `onerror` handler to dynamically direct broken or missing local images back to their absolute online URLs on `voz.vn`. Post images are styled to fit perfectly inside the comment containers without overflowing.

---

## Directory Structure

```
Scrape-Voz/
├── index.html                  (Stunning Root Thread Explorer landing page)
├── threads.js                  (Statically loaded root database index)
├── threads.json                (Index database backup file)
├── thread_viewer.html          (Master XenForo comments/reactions viewer template)
└── threads/
    └── [thread_folder]/        (Named as <thread_id>_<normalized_title_slug>)
        ├── index.html          (Self-contained viewer copy)
        ├── comments.js         (Statically loaded thread database script)
        ├── comments.json       (Thread posts database backup)
        └── images/             (Concurrently downloaded, MD5-deduplicated post images)
```

---

## Installation

Ensure you have Python 3 installed. Then install the required dependencies:

```bash
pip install requests beautifulsoup4 python-dotenv
```

---

## Quick Testing Commands

To quickly test the application, run these preconfigured commands:

### 1. Test Scrape (Pages 1 to 2, No Image Downloads)
Fetches pages 1 and 2, parsing comments and image URLs into `comments.json` and `comments.js`:
```bash
python scrape_voz.py --url "https://voz.vn/t/28-tuoi-da-bi-coi-la-mat-gia-khi-phu-nu-bi-dinh-gia-bang-so-tuoi.1236656/" --start-page 1 --end-page 2
```

### 2. Test Scrape with Image Downloads (Pages 1 to 2)
Fetches pages 1 and 2, parses them, and downloads all post body images concurrently into the thread folder's `images/` directory:
```bash
python scrape_voz.py --url "https://voz.vn/t/28-tuoi-da-bi-coi-la-mat-gia-khi-phu-nu-bi-dinh-gia-bang-so-tuoi.1236656/" --start-page 1 --end-page 2 --download-images
```

### 3. Open Thread Explorer
After running one of the above commands, open the root `index.html` in your browser. It automatically detects and displays all your scraped threads. Click the thread title link to open the comments viewer instantly and automatically!

---

## Usage (Full Scrape)

### Simple Scrape (All Pages)
Run the script passing the base/first page URL of the thread:

```bash
python scrape_voz.py --url "https://voz.vn/t/28-tuoi-da-bi-coi-la-mat-gia-khi-phu-nu-bi-dinh-gia-bang-so-tuoi.1236656/" --download-images
```

*This will automatically detect the total number of pages (e.g. 103), scrape all of them, download all embedded images to `threads/<folder>/images/`, generate `comments.js`, copy the viewer template, and save everything.*

### Advanced Options

You can customize the scraping behavior using command-line arguments:

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
| `--token` | Your Browserless API key token. | *(Pre-filled with your provided token)* |
| `--start-page` | The page number to start scraping from. | `1` |
| `--end-page` | The page number to stop scraping (inclusive). | *Auto-detected last page* |
| `--output` | Destination file name inside the thread directory. Supports `.json` and `.csv` formats. | `comments.json` |
| `--concurrency` | Number of parallel page fetches. Adjust lower if encountering heavy rate-limiting. | `5` |
| `--download-images` | If passed, downloads all parsed post images concurrently into the thread folder's `images/` directory. | `False` |
| `--fetch-reactions` | If passed, fetches the complete list of all reacted users from Voz concurrently (slows down scraping). | `False` |
| `--force` | If passed, forces a fresh scrape of all requested pages, completely overwriting the existing local cache. | `False` |
