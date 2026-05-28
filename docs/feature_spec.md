# Feature Specifications - Voz Thread Scraper & Explorer

This document details the technical specifications, data models, algorithms, and logic behind the core features of the Voz Thread Scraper & Explorer application.

---

## 1. Incremental Resume Mode Algorithm

To prevent wasteful API requests and duplicate page scrapes, the scraper uses an incremental resuming logic:

### Page Classification
On startup, the scraper loads any existing `comments.json` file inside the target thread folder:
*   **Complete Page**: A page index containing exactly 20 comments. (Skip during scraping).
*   **Incomplete Page**: A page index containing fewer than 20 comments. (Requires re-scraping to fetch late posts).
*   **Active Page**: The highest recorded page index. (Always re-scraped to catch new additions).

### The Scrape Queue
The script constructs the queue of pages to scrape as follows:
$$\text{Pages to Scrape} = \text{Requested Range} \cap (\text{Incomplete Pages} \cup \text{Active Page} \cup \text{New Pages})$$

---

## 2. Post Reactions Modal Specification

To clone XenForo's user reactions visually without requiring users to log in, the application implements a reaction scraping and rendering pipeline:

### Scraping Phase (`scrape_voz.py`)
1.  **Overlays Extraction**: If `--fetch-reactions` is enabled, the scraper concurrently sends requests (`max_workers=10`) to the post's XenForo overlay route `/posts/<post_id>/reactions?reaction_id=0`.
2.  **Payload Map**: Extracts user lists and reaction icon segments:
    ```json
    "reactions": {
        "text": "brian20, Mr.A, và 15 người khác",
        "users": [
            {"username": "brian20", "type": "like"},
            {"username": "Mr.A", "type": "love"}
        ],
        "icons": ["like", "love"]
    }
    ```

### Rendering Phase (`thread_viewer.html`)
1.  **Reactions Bar**: Renders a pill underneath each post displaying the summary text and active reaction icons.
2.  **Modal Overlay**: Clicking the reactions bar displays a custom-designed XenForo-style modal popup overlay:
    *   Lists all reacted users with corresponding reaction icons.
    *   Includes a scrollable list with custom scrollbar styling.
    *   Features dynamic numbering next to each user in the modal table list for easy tracking.

---

## 3. MD5 Hashed Image Deduplication Pipeline

Embedded images are hosted on third-party CDNs, which are prone to hotlink blocking or deletions. The scraper downloads images into a local subfolder with strict deduplication:

### Filename Hashing
To prevent downloading duplicate graphics or user badges, each image URL is hashed using MD5:
$$\text{Filename} = \text{MD5}(\text{Image URL}) + \text{Extension}$$
If `proxy.php` is detected in the URL, the script unquotes and parses nested query parameters to identify the correct extension (e.g. `.jpg`, `.png`, `.webp`, `.gif`).

### Concurrency
Downloads run concurrently using a `ThreadPoolExecutor` (`max_workers=20`) with thread-local sessions for maximum speed, skipping files that already exist on disk with file sizes greater than `0`.

---

## 4. Gallery Mode & Jump-to-Post Flow

### Visual Grid Card Layout
Displays a grid matching `.gallery-grid` using CSS grids (`grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))`). Each card displays:
*   The first image in the post as the cover photo.
*   A corner badge showing additional images count (e.g. `+3 ảnh`).
*   User details, post timestamps, and cleaned content text snippets.

### Jump-to-Post Navigation (`goToPost`)
Clicking a gallery card triggers `goToPost(postId, pageNum)`:
1.  **Page calculation**:
    *   If active search filters are present, it locates the comment index inside the filtered array and calculates the pagination index:
        $$\text{Target Page} = \lfloor \text{Filtered Index} / 20 \rfloor + 1$$
    *   If no search query is present, it directly switches to `pageNum`.
2.  **UI Transition**: Toggles `isGalleryMode = false`, rendering the standard reading view.
3.  **Smooth Scrolling**: Selects the anchor `#post-<postId>` and invokes:
    ```javascript
    postCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    ```
4.  **Attention Focus Highlight**: Applies the `.highlighted-post` class to add a temporary cyan border glow that fades out after 2 seconds.
