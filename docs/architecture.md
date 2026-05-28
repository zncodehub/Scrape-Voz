# Architecture Document - Voz Thread Scraper & Explorer

This document maps out the system architecture, data models, file layouts, and execution pipelines of the Voz Thread Scraper & Explorer application.

---

## 1. Directory Structure & File Roles

```
Scrape-Voz/
├── app.py                      (Flask server - manages GUI routes, SSE log stream, and deletion API)
├── requirements.txt            (Lists Python dependencies: requests, bs4, python-dotenv, Flask)
├── .env                        (Sensitive environment variables - stores BROWSERLESS_TOKEN)
├── index.html                  (Root landing explorer page - reads registries, lists downloaded threads)
├── thread_viewer.html          (Comments viewer template cloned dynamically into thread subfolders)
├── threads.json                (Static registry database listing all successfully scraped threads)
├── threads.js                  (Offline-fallback JS script generating window.threadsData registry)
├── templates/
│   └── scraper_ui.html         (Flask templates - provides the retro glassmorphic Control Panel)
└── threads/                    (Scraped library - ignored from Git version control)
    └── [thread_folder]/        (Named using convention: <thread_id>_<20_char_slug>…)
        ├── index.html          (Copy of thread_viewer.html cloned post-scraping)
        ├── comments.json       (JSON array containing all comments data)
        ├── comments.js         (Offline-fallback JS script generating window.threadData variable)
        └── images/             (Directory containing all concurrently downloaded, MD5-hashed images)
```

---

## 2. Dynamic CORS-Free Offline Fallback System

### The Problem
Security policies (CORS) in modern browsers strictly block local `fetch()` calls or XMLHttpRequests pointing to local JSON files (`threads.json`, `comments.json`) when pages are launched via the offline `file://` protocol. 

### The Solution
The system generates **dual output files** during scraping:
1.  **Standard JSON databases** (`comments.json`, `threads.json`): Useful for structured program access or data parsing.
2.  **Executable JS fallback scripts** (`comments.js`, `threads.js`): These files contain the exact same database wrapped inside global window variables:
    *   `threads.js` -> `window.threadsData = [ ... ];`
    *   `comments.js` -> `window.threadData = { ... };`

The HTML files contain static script loading tags in their headers pointing to these files. If the page is opened offline (`file://`), the scripts load instantly, bypassing CORS blocks and populating variables. The page checks if `window.threadData` is present, rendering it instantly:

```javascript
// Check for pre-loaded offline data script
if (window.threadData) {
    threadData = window.threadData;
    renderUI();
} else {
    // Fallback to fetch if served over HTTP
    fetch('comments.json')...
}
```

---

## 3. Web Control Panel & SSE Execution Pipeline

The Flask server `app.py` acts as a graphical orchestration layer for `scrape_voz.py`:

```
+--------------+                   +------------+                   +----------------+
|  Scraper UI  | -- SSE Request -> |  Flask App | -- subprocess --> | scrape_voz.py  |
| (Control)    | <--- SSE Stream - |  (app.py)  | <--- stdout/err - |  (Unbuffered)  |
+--------------+                   +------------+                   +----------------+
```

### Unbuffered Streaming
If a standard Python subprocess runs, standard output buffering prevents the terminal from getting logs in real-time. The server spawns `sys.executable` (using `.venv`'s python) with the `-u` unbuffered flag (`python -u scrape_voz.py`). 

### Real-Time Event Stream
The Flask endpoint `/api/scrape-stream` spawns `subprocess.Popen` with combined stdout/stderr (`stderr=subprocess.STDOUT`). It reads the process output stream line-by-line and yields Server-Sent Events (SSE):

```python
for line in iter(process.stdout.readline, ""):
    yield f"data: {line.rstrip()}\n\n"
```

### Clean Subprocess Termination
If the client closes the browser or terminates the socket, a `GeneratorExit` exception triggers inside Flask. The server catches this exception and terminates the background scraper subprocess immediately (`process.terminate()`), preventing orphaned processes from consuming system resources.

---

## 4. Folder Deletion & Registry Synchronization Flow

The deletion pipeline runs inside `/api/delete-thread` using a secure POST request:

1.  **ID validation**: Flask reads the query argument `?id=...`.
2.  **Registry check**: Reads `threads.json` and locates the entry matching the ID.
3.  **Physical deletion**: Extracts the `folder_name` property and deletes the subfolder at `threads/<folder_name>` recursively using `shutil.rmtree(thread_dir)`.
4.  **Sync registry**: Filters the deleted item out of the registry and rewrites both `threads.json` and the static `threads.js` file to ensure the list remains unified.
5.  **UI update**: The Explorer's JS receives the success response, filters the local array, and re-renders the DOM table row in-place without reloading the page.
