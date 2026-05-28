# Suggestions for Future Features - Voz Thread Scraper & Explorer

This document lists recommended features, enhancements, and roadmap suggestions to expand the capabilities of the Voz Thread Scraper & Explorer application.

---

## 1. Thread Reading Experience Upgrades

### Feature 1: Dynamic Custom Tags & Bookmarks
*   **Description**: Allow users to save specific comments or highlight quotes inside the thread viewer.
*   **Use Case**: Handy for long novel threads where the user wants to bookmark their current reading progress or save a legendary quote.
*   **Implementation**: 
    *   Create a "Star" icon on each post card in `thread_viewer.html`.
    *   Store bookmarked post IDs in the browser's `localStorage` indexed by thread ID.
    *   Add a "Star" filter button next to the search input to display only bookmarked comments.

### Feature 2: Author Profile Filter Sidecard
*   **Description**: Clicking a user's avatar opens a floating side panel listing all comments posted by that specific author within the active thread, including their total post count in this thread.
*   **Use Case**: Helpful for finding only the original poster's (OP) replies in a thread filled with chat spam.
*   **Implementation**: Create an overlay sidecard triggered by avatar clicks, running a basic JavaScript filter:
    ```javascript
    const authorComments = threadData.comments.filter(c => c.author === targetAuthor);
    ```

### Feature 3: Full-Featured Lightbox Media Gallery
*   **Description**: Inside the standard thread viewer and Gallery Mode, clicking any image opens a full-screen, swipeable **Lightbox** modal with Zoom in/out, download buttons, and left/right navigation arrows to browse all images in the thread.
*   **Implementation**: Add a lightweight vanilla JS Lightbox modal module to `thread_viewer.html` that reads image arrays dynamically.

---

## 2. Advanced Control Panel & Scraper Intelligence

### Feature 1: Auto-Updater Daemon (Background Cron)
*   **Description**: A background checker that polls your bookmarked or active threads once a day and automatically runs the incremental scraper to download new comments if a thread has updated.
*   **Implementation**: Add a background scheduler route inside `app.py` or expose on the Web UI as an "Auto-Sync" toggle button next to each thread row.

### Feature 2: Forum Category Categorization
*   **Description**: Group threads inside subfolders of `threads/` based on their XenForo category (e.g. `threads/f17/` for F17 threads, `threads/f33/` for F33 threads).
*   **Implementation**: Extract the forum breadcrumb node inside `scrape_voz.py` and categorize the threads explorer landing table.

---

## 3. Media & Performance Optimizations

### Feature 1: Local WebP Image Compression
*   **Description**: Standard scraped images are often large `.jpg` or `.png` files. Compressing them to `.webp` format on the fly reduces disk usage by 50–70% and speeds up offline load times.
*   **Implementation**: Integrate Python's `pillow` library inside `scrape_voz.py`. Convert downloaded images to WebP and save them with custom compression bounds during the download pipeline step.

### Feature 2: YouTube Video Embed Downloader
*   **Description**: Many Voz posts contain embedded YouTube links that do not load offline without an internet connection.
*   **Implementation**: Scrape video descriptions and thumbnails, or provide a toggle to download audio/video clips using `yt-dlp` for absolute 100% offline-ready archives.

### Feature 3: Export as Single-File HTML / PDF Book
*   **Description**: A button to package the entire scraped thread (all comments, loaded styles, and inline-base64 encoded images) into a single, portable `.html` file or a clean `.pdf` book for easy sharing.
*   **Implementation**: Write a packaging script inside Python that bundles local images as Base64 data URIs and exports them as a single monolithic HTML file.
