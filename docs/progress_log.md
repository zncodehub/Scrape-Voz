# Progress Log - Voz Thread Scraper & Explorer

This document lists the complete chronological history of changes, milestones, and updates completed on the Voz Thread Scraper & Explorer application.

---

## Phase 1: Multiple Threads Directory Scaling & Central Explorer
*   **Goal**: Scale the application from a single-thread downloader to a multiple-thread archiving explorer.
*   **Milestones**:
    *   **Folder Naming Normalization**: Updated `scrape_voz.py` to extract thread IDs and normalize thread titles into clean slugs (first 20 alphanumeric characters).
    *   **Ellipsis Handling**: Implemented a Unicode horizontal ellipsis (`…`) suffix for folder titles longer than 20 characters, preventing Windows file system truncation issues.
    *   **Self-Healing Folder Migration**: Added startup routines inside the scraper to scan the disk for legacy formats, rename folders to the new unicode ellipsis standard, and rewrite registries automatically.
    *   **Root Thread Explorer Landing Dashboard (`index.html`)**: Transformed the root page into a XenForo-style registry explorer. Added columns for search filtering, page progress ratios (downloaded/total pages), comment counts, and local timezone formats.
    *   **CORS-Free Fallback System**: Added dynamic `threads.js` and `comments.js` writers, wrapping databases in script files to bypass local file browser origin blocks.

---

## Phase 2: Python Flask Web Control Panel & SSE Streaming
*   **Goal**: Create a graphical web interface to configure options and view logs in real-time.
*   **Milestones**:
    *   **Server Core (`app.py`)**: Created the Flask application mapping routes for the Control Panel (`/`), Explorer (`/explorer`), static thread indexes, and static assets directory routing under a unified origin.
    *   **Dashboard Template (`templates/scraper_ui.html`)**: Designed a glassmorphic dashboard equipped with URL input fields, start/end range inputs, and slider toggles mapping to CLI scraper flags.
    *   **Real-time Subprocess Piping**: Run the process in unbuffered mode (`python -u`) merging stdout and stderr.
    *   **SSE Logs Stream (`/api/scrape-stream`)**: Developed an EventSource stream delivering terminal prints line-by-line. Added `GeneratorExit` handlers to terminate background processes immediately on browser disconnection.
    *   **Fluid Progress Tracking**: Built a regex parser inside the UI to capture progress lines (e.g. `[2/10] Page scraped successfully`) and fill the progress bar dynamically.

---

## Phase 3: Clickable Home Buttons & Thread Deletions
*   **Goal**: Allow quick home navigation and in-app thread cleaning.
*   **Milestones**:
    *   **Clickable Header Logos**: Wrapped headers in `index.html` and `thread_viewer.html` inside clickable links pointing to the Explorer `/explorer`.
    *   **Offline Fallback Links**: Added a JavaScript checker to rewrite the header logo link to `../../index.html` if running locally under the `file://` protocol.
    *   **Thread Deletion Endpoint (`/api/delete-thread`)**: Built a secure POST deletion route that cleans up subfolders recursively using `shutil.rmtree`, synchronizing `threads.json` and `threads.js` in a single transaction.
    *   **Explorer UI Deletion Button**: Inserted a red-highlighted "🗑️ Xóa" action button inside the Explorer table. Features confirmation warnings and local `file://` security fallbacks.
    *   **In-Place DOM Sync**: The Explorer filters the deleted item out of the state array and re-renders the table row in-place without page reloads.

---

## Phase 4: Image Gallery View Integration
*   **Goal**: Add visual grid views for image-heavy thread archives.
*   **Milestones**:
    *   **Thư Viện Ảnh (Gallery Mode)**: Integrated a toggle button isolating posts containing images inside a visual grid card module.
    *   **Visual Grid Cards**: Cards feature lazy-loaded cover images, image totals badges, username headers, avatar initials, and reaction tallies.
    *   **Jump-To-Post Smooth Scroll**: Clicking an image card dynamically flips the view back to reading mode, calculates page ratios, switches to the correct paginated view, and smoothly scrolls to the target card with a temporary glowing fade overlay.
