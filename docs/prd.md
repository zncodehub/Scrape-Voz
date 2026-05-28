# Product Requirement Document (PRD) - Voz Thread Scraper & Explorer

## 1. Product Vision & Goals
Voz.vn is one of the largest forums in Vietnam, hosting decades of rich discussions, stories, reviews, and community knowledge. However, threads are frequently deleted, modified, or become inaccessible when offline. 

The **Voz Thread Scraper & Explorer** is a high-performance, resilient, and visually premium offline archiving suite. Its goal is to allow users to preserve, explore, search, and read any Voz thread completely offline with a modern desktop-class reading experience, bypassing standard browser security barriers without requiring technical setups.

---

## 2. Core User Personas
*   **The Archivist**: Users who want to download long, legendary Voz threads (such as f17 novels, reviews, or historical discussions) and save them permanently on their hard drives, including all high-quality embedded images.
*   **The Offline Reader**: Users who read threads during flights, commutes, or in areas with poor internet connection, wanting an instant page-load experience with zero network requests.
*   **The Casual Collector**: Users who maintain a library of multiple threads and want a clean, searchable dashboard to manage their archives graphically.

---

## 3. Key Product Requirements

### R1: High-Fidelity XenForo Re-rendering
*   The offline viewer must resemble a premium, modern XenForo theme.
*   Must support styled user cards, timestamps, post content, blockquotes, deep nested quote boxes, lazy-loaded images, and interactive reaction summaries.

### R2: 100% Offline-Safe Operations (Zero CORS Blocks)
*   The application must support offline double-clicking of local `.html` files straight from Windows Explorer (the `file://` protocol).
*   Standard AJAX fetches of local `.json` databases are blocked by modern browser security policies under the `file://` origin. The system must save dual databases: a standard `.json` backup and an executable `.js` fallback script that populates global window variables.

### R3: Robust, Rate-Limit Aware Scraper Pipeline
*   Must handle pagination automatically, detecting the total page count from any single page URL.
*   Must support thread pools for accelerated concurrent scraping.
*   Must handle rate-limiting errors (like HTTP 429) gracefully using exponential backoff retries.
*   Must execute incremental resumes: checking existing comments, skipping completed pages, and automatically re-scraping active/incomplete pages to fetch new comments.

### R4: Central Thread Explorer
*   A root landing page that aggregates all scraped threads dynamically.
*   Features a responsive, searchable table displaying thread numbers, names, page counts, comment metrics, and scrape timestamps.

### R5: Unified Web Control Panel
*   Exposes a Flask-based local web app to configure, run, and delete thread archives graphically.
*   Includes a real-time terminal output widget streaming subprocess stdout/stderr.
*   Displays a fluid progress bar showing page completions.

---

## 4. Key Constraints & Non-Functional Requirements
*   **No Database Server Needed**: The application must run without databases like MySQL, PostgreSQL, or SQLite. All storage must reside in flat-file JSON and JS scripts.
*   **No Complex Web Server Installation**: The explorer and viewer must operate perfectly either via a local double-click (`file://`) or a simple Flask dev server.
*   **Strict Security**: API keys must reside inside an ignored `.env` file, never hardcoded or pushed to remote repositories.
*   **Filename Ellipsis Handling**: Folders must be named using a clean `<thread_id>_<slug>` convention. To satisfy Windows directory naming limitations, any name truncation must end with a Unicode ellipsis (`…`) rather than standard periods, preventing silent filesystem truncation.
