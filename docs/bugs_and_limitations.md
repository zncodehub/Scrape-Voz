# Bugs Tracking & Limitations - Voz Thread Scraper & Explorer

This document lists key engineering bugs resolved during development, known technical limitations, security concerns, and troubleshooting details.

---

## 1. Resolved Technical Bugs

### Bug 1: Windows Trailing Period Truncation (`FileNotFoundError`)
*   **Symptom**: When trying to save files inside folders ending with three dots (e.g. `1236656_28-tuoi-da-bi-coi-la...`), Python threw a `FileNotFoundError` or path resolution failure.
*   **Cause**: The Windows NTFS filesystem prevents directory names from ending with trailing period characters (`.`). Windows silently stripped these periods during folder creation, meaning the folder created on disk was named `1236656_28-tuoi-da-bi-coi-la`, causing subsequent Python path lookups expecting the dot suffix to fail.
*   **Resolution**: Swapped the standard ASCII periods `...` with the single Unicode horizontal ellipsis character (`…`, code point `\u2026`). Windows safely supports this character without stripping it, resolving all file path failures.

### Bug 2: Browser CORS Blocks on Local Files (`file://` protocol)
*   **Symptom**: When double-clicking `index.html` locally from Windows Explorer, the console threw a `Cross-Origin Request Blocked` error, and the list remained empty.
*   **Cause**: Modern browser local security policies block AJAX/`fetch()` requests directed to local files on disk when using the `file://` protocol.
*   **Resolution**: Developed a dual-database writer that saves files as executable scripts (`threads.js`, `comments.js`) defining global variables. Loading these scripts via standard `<script>` tags in the HTML header bypasses CORS blocks natively.

### Bug 3: Flask Subprocess stdout Logging Delays
*   **Symptom**: The Web Terminal Console remained blank during scraping, then dumped all logs in a single massive block only after the process completed.
*   **Cause**: Python buffers console output (stdout/stderr) internally when it detects that standard output is being redirected to a pipe (such as Flask's `subprocess.PIPE`) instead of a live console.
*   **Resolution**: Spawned the process in unbuffered mode using the `-u` flag (`python -u scrape_voz.py`). This forces Python to flush every print statement immediately, piping logs line-by-line to the EventSource SSE stream.

---

## 2. Active Technical Limitations & Troubleshooting

### Limitation 1: Local file:// Protocol YouTube Blocks
*   **Symptom**: Embedded YouTube video frames inside comments fail to play or show black boxes when viewed offline via `file://`.
*   **Cause**: YouTube's iframe API blocks requests coming from null origins (`file://`) to prevent domain spoofing and clickjacking.
*   **Workaround**: The page automatically detects the `file://` protocol and renders a warning banner suggesting running a local HTTP server using:
    ```bash
    python -m http.server 8000
    ```
    Alternatively, accessing the explorer through the Flask server (`http://127.0.0.1:5000/explorer`) resolves this issue natively.

### Limitation 2: Flask Debug Reloader Loops
*   **Symptom**: The Flask server occasionally restarts on its own when scraping.
*   **Cause**: Flask's debug mode utilizes a file watcher (`stat`) to restart the server when files change. If debug mode is active and files under python tracking are modified, it triggers a reload.
*   **Workaround**: We configured `.gitignore` and folder patterns, but ensuring that registry files like `threads.json` do not trigger reloader cycles is handled by running in the standard directory layout. If loops persist in production, run Flask with `debug=False` or `use_reloader=False`.

---

## 3. Critical Security Reminders
*   **API Key Compromise**: Public GitHub scrapers scan commits continuously. **Never push your `.env` file containing BROWSERLESS_TOKEN to GitHub.** 
*   **Revocation**: If a token is committed to Git history by accident, revoke it immediately at **Browserless.io** and perform history purges using `git-filter-repo` with temporary replacement files.
