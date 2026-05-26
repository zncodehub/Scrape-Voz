import sys
import os
import csv
import json
import time
import argparse
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

# Try to load environment variables from a .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_image_filename(img_url):
    """Generate a unique local filename based on MD5 hash of image URL to prevent duplicate downloads."""
    ext = "jpg"
    # Simple extension detection
    if "." in img_url.split("/")[-1]:
        parts = img_url.split("/")[-1].split("?")[0].split(".")
        if len(parts) > 1 and len(parts[-1]) <= 4:
            ext = parts[-1]
    url_hash = hashlib.md5(img_url.encode("utf-8")).hexdigest()
    return f"{url_hash}.{ext}"

# Ensure console supports UTF-8 characters (useful on Windows)
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

# Default settings
DEFAULT_TOKEN = os.getenv("BROWSERLESS_TOKEN", "")
BROWSERLESS_API = "https://production-sfo.browserless.io/smart-scrape"

def clean_url(url):
    """Normalize the URL by removing trailing slashes."""
    url = url.strip()
    if url.endswith("/"):
        url = url[:-1]
    return url

def get_page_url(base_url, page_num):
    """Generate the URL for a specific page number."""
    if page_num == 1:
        return f"{base_url}/"
    else:
        return f"{base_url}/page-{page_num}"

def fetch_page_content(api_token, url):
    """Fetch HTML content from a URL using Browserless Smart Scrape REST API."""
    api_url = f"{BROWSERLESS_API}?token={api_token}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "url": url,
        "formats": ["html"]
    }
    
    # Try with retries
    max_retries = 3
    backoff = 2
    for attempt in range(max_retries):
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get("ok") and "content" in result:
                    return result["content"], result.get("strategy")
                else:
                    error_msg = result.get("message") or "Unknown API error"
                    print(f"[Warning] API returned error for {url}: {error_msg}")
            else:
                print(f"[Warning] HTTP {response.status_code} on attempt {attempt+1} for {url}")
        except Exception as e:
            print(f"[Warning] Request failed on attempt {attempt+1} for {url}: {str(e)}")
        
        if attempt < max_retries - 1:
            time.sleep(backoff * (attempt + 1))
            
    return None, None

def fetch_post_reactions(numeric_post_id):
    """Fetch the complete list of all users who reacted to a post."""
    url = f"https://voz.vn/p/{numeric_post_id}/reactions"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    users = []
    icons = []
    
    # Try twice with standard polite requests
    for attempt in range(2):
        try:
            # Minimal stagger sleep (50ms) to prevent server blast
            time.sleep(0.05)
            res = requests.get(url, headers=headers, timeout=6)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                member_items = soup.find_all("li", class_="block-row")
                for item in member_items:
                    username_el = item.find("a", class_="username") or item.find("span", class_="username")
                    if username_el:
                        users.append(username_el.text.strip())
                    
                    reaction_el = item.find("span", class_="reaction")
                    if reaction_el:
                        reaction_img = reaction_el.find("img")
                        if reaction_img and reaction_img.get("alt"):
                            icons.append(reaction_img["alt"])
                        else:
                            classes = reaction_el.get("class", [])
                            for cls in classes:
                                if cls.startswith("reaction--"):
                                    icons.append(cls.split("--")[-1])
                break
        except Exception:
            pass
            
    return list(set(users)), list(set(icons))

def parse_comments(html_content, page_num):
    """Parse comments/posts from raw HTML content."""
    soup = BeautifulSoup(html_content, "html.parser")
    posts = soup.find_all("article", class_="message--post")
    
    parsed_posts = []
    for post in posts:
        author = post.get("data-author", "Unknown")
        post_id = post.get("id", "Unknown")
        
        # Content is inside a div with class "bbWrapper"
        content_div = post.find("div", class_="bbWrapper")
        
        # Parse images inside the post body, filtering out XenForo smilies
        image_urls = []
        if content_div:
            # First, normalize all relative URLs to absolute so links and resources work offline
            for a in content_div.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/"):
                    a["href"] = "https://voz.vn" + href
                    
            for img in content_div.find_all("img"):
                classes = img.get("class", [])
                
                # Normalize relative src/data-url/data-src links
                for attr in ["src", "data-url", "data-src"]:
                    val = img.get(attr)
                    if val:
                        if val.startswith("//"):
                            img[attr] = "https:" + val
                        elif val.startswith("/"):
                            img[attr] = "https://voz.vn" + val
                
                if "smilie" in classes or "emoji" in classes:
                    continue
                    
                src = img.get("data-url") or img.get("data-src") or img.get("src")
                if src:
                    if src.startswith("data:"):
                        continue
                    image_urls.append(src)
                    
        content = content_div.decode_contents().strip() if content_div else ""
        
        # Parse reactions at the bottom of the comment (likes, etc.)
        reactions = {}
        reactions_bar = post.find("div", class_="reactionsBar")
        if reactions_bar:
            # Try both .reactionsBar-link (Voz XenForo default) and .reactionsBar-text
            text_elem = reactions_bar.find("a", class_="reactionsBar-link") or reactions_bar.find("span", class_="reactionsBar-text")
            if text_elem:
                reactions["text"] = text_elem.text.strip().replace("\n", " ").replace("  ", " ")
                reactions["users"] = [el.text.strip() for el in (text_elem.find_all("bdi") or text_elem.find_all("a"))]
            
            # Extract distinct types of reactions from bar
            icons = []
            for span in reactions_bar.find_all("span", class_="reaction"):
                alt = span.find("img")
                if alt and alt.get("alt"):
                    icons.append(alt["alt"])
                else:
                    classes = span.get("class", [])
                    for cls in classes:
                        if cls.startswith("reaction--"):
                            icons.append(cls.split("--")[-1])
            reactions["icons"] = list(set(icons))
            
        # Time is inside a time element with class "u-dt" or standard datetime attribute
        time_elem = post.find("time", class_="u-dt")
        time_str = "Unknown"
        if time_elem:
            time_str = time_elem.get("datetime") or time_elem.text.strip()
            
        parsed_posts.append({
            "page": page_num,
            "post_id": post_id,
            "author": author,
            "time": time_str,
            "content": content,
            "images": image_urls,
            "reactions": reactions
        })
        
    return parsed_posts

def download_image(url, folder, filename):
    """Download an image from url and save to folder/filename."""
    try:
        # Use simple headers to mimic a browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=15, stream=True)
        if res.status_code == 200:
            os.makedirs(folder, exist_ok=True)
            filepath = os.path.join(folder, filename)
            with open(filepath, "wb") as f:
                for chunk in res.iter_content(1024):
                    f.write(chunk)
            return filepath
        else:
            print(f"[Warning] Failed to download image (HTTP {res.status_code}): {url}")
    except Exception as e:
        print(f"[Warning] Failed to download image {url}: {str(e)}")
    return None

def detect_thread_info(api_token, base_url):
    """Fetch first page to determine title and total page count."""
    print(f"Detecting thread details from {base_url}...")
    html, strategy = fetch_page_content(api_token, get_page_url(base_url, 1))
    if not html:
        print("[Error] Failed to load the first page of the thread. Cannot proceed.")
        return None, 1
        
    soup = BeautifulSoup(html, "html.parser")
    
    # Title
    title_elem = soup.find("h1", class_="p-title-value")
    title = title_elem.text.strip() if title_elem else "Unknown Voz Thread"
    
    # Page Navigation
    total_pages = 1
    page_nav = soup.find("ul", class_="pageNav-main")
    if page_nav:
        pages = page_nav.find_all("li")
        if pages:
            try:
                total_pages = int(pages[-1].text.strip())
            except ValueError:
                # Try fallback: sometimes XenForo has pagination dots or links
                pass
                
    print(f"Thread Title: '{title}'")
    print(f"Detected Total Pages: {total_pages} (Fetched via strategy: {strategy})")
    return title, total_pages

def save_output_data(output_path, all_comments, title, base_url):
    """Save scraped comments to output JSON or CSV file."""
    if output_path.lower().endswith(".csv"):
        # Explicit CSV requested
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["page", "post_id", "author", "time", "content"])
            writer.writeheader()
            writer.writerows(all_comments)
    else:
        # Default to JSON
        if not output_path.lower().endswith(".json"):
            output_path += ".json"
            
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "thread_title": title,
                "thread_url": base_url,
                "total_comments": len(all_comments),
                "comments": all_comments
            }, f, ensure_ascii=False, indent=2)
    print(f"Results saved to: {os.path.abspath(output_path)}")

def main():
    parser = argparse.ArgumentParser(description="Scrape comments from a Voz.vn thread using Browserless Smart Scrape API.")
    parser.add_argument("--url", required=True, help="First page or base URL of the Voz.vn thread")
    parser.add_argument("--token", default=DEFAULT_TOKEN, help="Browserless API Token. Can also be configured via BROWSERLESS_TOKEN in a .env file.")
    parser.add_argument("--start-page", type=int, default=1, help="Page number to start scraping from")
    parser.add_argument("--end-page", type=int, help="Page number to stop scraping (inclusive). If not set, automatically detects last page.")
    parser.add_argument("--output", default="comments.json", help="Output file name (supports .json and .csv, defaults to JSON)")
    parser.add_argument("--concurrency", type=int, default=5, help="Number of concurrent pages to fetch (default: 5)")
    parser.add_argument("--download-images", action="store_true", help="Download images embedded in comments to a local 'images' folder")
    parser.add_argument("--fetch-reactions", action="store_true", help="Fetch the complete list of all reacted users from Voz (slows down scraping)")
    parser.add_argument("--force", action="store_true", help="Force a fresh scrape of all pages, overwriting existing records.")
    
    args = parser.parse_args()
    
    base_url = clean_url(args.url)
    api_token = args.token
    
    if not api_token:
        print("[Error] Browserless API Token is missing.")
        print("Please either:")
        print("  1. Create a '.env' file based on '.env.example' and set BROWSERLESS_TOKEN.")
        print("  2. Pass the token directly using the --token command-line argument.")
        sys.exit(1)
        
    output_path = args.output
    if not output_path.lower().endswith(".json") and not output_path.lower().endswith(".csv"):
        output_path += ".json"
        
    # Load existing comments if file exists and we are not in force mode (Incremental Resume Mode)
    existing_comments = []
    existing_pages = set()
    incomplete_pages = set()
    if not args.force and os.path.exists(output_path) and output_path.lower().endswith(".json"):
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                existing_comments = old_data.get("comments", [])
                
                # Count comments per page to find incomplete ones
                page_counts = {}
                for c in existing_comments:
                    if "page" in c:
                        p = int(c["page"])
                        page_counts[p] = page_counts.get(p, 0) + 1
                
                existing_pages = set(page_counts.keys())
                
                # Pages with fewer than 20 comments are incomplete
                for p, count in page_counts.items():
                    if count < 20:
                        incomplete_pages.add(p)
                        
                # Always re-check the highest existing page number to catch new comments
                if existing_pages:
                    incomplete_pages.add(max(existing_pages))
                    
            print(f"Loaded {len(existing_comments)} existing comments from '{output_path}'")
            print(f"  - Completed pages: {sorted(list(existing_pages - incomplete_pages))}")
            if incomplete_pages:
                print(f"  - Active/Incomplete pages to re-check: {sorted(list(incomplete_pages))}")
        except Exception as e:
            print(f"[Warning] Failed to load existing comments file: {str(e)}")

    # Detect thread details
    title, detected_total = detect_thread_info(api_token, base_url)
    if not title and not args.end_page:
        sys.exit(1)
        
    start_page = max(1, args.start_page)
    end_page = args.end_page if args.end_page else detected_total
    
    if start_page > end_page:
        print(f"[Error] Start page ({start_page}) cannot be greater than end page ({end_page}).")
        sys.exit(1)
        
    requested_pages = list(range(start_page, end_page + 1))
    pages_to_scrape = [p for p in requested_pages if p not in existing_pages or p in incomplete_pages]
    total_pages_count = len(pages_to_scrape)
    
    new_comments = []
    failed_pages = []
    
    if total_pages_count == 0:
        print("All requested pages are already scraped. Skipping scrape phase...")
    else:
        print(f"Preparing to scrape {total_pages_count} pages (from page {start_page} to {end_page}, skipping already scraped pages)...")
        
        # Fetch using ThreadPoolExecutor for concurrency
        def scrape_single_page(page_num):
            page_url = get_page_url(base_url, page_num)
            # Add a small polite stagger delay to reduce sudden peak load
            time.sleep((page_num % args.concurrency) * 0.2)
            
            html, strategy = fetch_page_content(api_token, page_url)
            if html:
                posts = parse_comments(html, page_num)
                return page_num, posts, strategy
            return page_num, None, None

        print(f"Scraping thread using concurrency level of {args.concurrency}...")
        with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
            futures = {executor.submit(scrape_single_page, p): p for p in pages_to_scrape}
            
            completed = 0
            for future in as_completed(futures):
                page_num, posts, strategy = future.result()
                completed += 1
                if posts is not None:
                    new_comments.extend(posts)
                    print(f"[{completed}/{total_pages_count}] Page {page_num} scraped successfully ({len(posts)} comments, strategy: {strategy})")
                else:
                    failed_pages.append(page_num)
                    print(f"[{completed}/{total_pages_count}] Page {page_num} FAILED to scrape")

    # Filter out old comments from the pages we just successfully scraped
    scraped_pages_set = set(pages_to_scrape) - set(failed_pages)
    filtered_existing_comments = [c for c in existing_comments if int(c.get("page", 0)) not in scraped_pages_set]
    
    # Merge new comments with existing comments and de-duplicate by post_id
    combined_comments = filtered_existing_comments + new_comments
    seen_post_ids = set()
    deduped_comments = []
    for c in combined_comments:
        if c.get("post_id") and c["post_id"] not in seen_post_ids:
            seen_post_ids.add(c["post_id"])
            deduped_comments.append(c)
            
    all_comments = deduped_comments
    all_comments.sort(key=lambda x: (x["page"], x["post_id"]))
    
    # Fetch all post reactions concurrently if requested
    fetch_reactions = args.fetch_reactions
    if fetch_reactions:
        comments_to_fetch = []
        for c in all_comments:
            if c.get("reactions") and "js-post-" in c.get("post_id", ""):
                numeric_post_id = c["post_id"].replace("js-post-", "")
                if numeric_post_id.isdigit():
                    comments_to_fetch.append((numeric_post_id, c))
                    
        if comments_to_fetch:
            print(f"\nResolving full reaction member overlays for {len(comments_to_fetch)} posts concurrently...")
            
            def populate_worker(item):
                num_id, comment = item
                full_users, full_icons = fetch_post_reactions(num_id)
                if full_users:
                    comment["reactions"]["users"] = full_users
                if full_icons:
                    comment["reactions"]["icons"] = full_icons
            
            completed = 0
            # Use a pool of 10 workers for concurrent anonymous reaction requests
            with ThreadPoolExecutor(max_workers=10) as rx_executor:
                rx_futures = {rx_executor.submit(populate_worker, item): item for item in comments_to_fetch}
                for fut in as_completed(rx_futures):
                    completed += 1
                    if completed % 5 == 0 or completed == len(comments_to_fetch):
                        print(f"  --> Resolved reactions list: {completed}/{len(comments_to_fetch)} posts")
    
    # Save the output initially so comments are immediately viewable
    save_output_data(output_path, all_comments, title, base_url)
    
    # Download images concurrently if requested
    if args.download_images:
        image_downloads = []
        os.makedirs("images", exist_ok=True)
        
        # Track unique image URLs and map them to their local filenames
        unique_images = {} # url -> local_filename
        
        # Prepare unique mapping and local filenames for all comments in memory
        for comment in all_comments:
            comment["local_images"] = []
            for img_url in comment.get("images", []):
                if img_url not in unique_images:
                    filename = get_image_filename(img_url)
                    unique_images[img_url] = filename
                    image_downloads.append((img_url, "images", filename))
                comment["local_images"].append(unique_images[img_url])
                
        if image_downloads:
            print(f"\nDownloading {len(image_downloads)} unique images concurrently...")
            downloaded_count = 0
            with ThreadPoolExecutor(max_workers=5) as img_executor:
                img_futures = {
                    img_executor.submit(download_image, item[0], item[1], item[2]): item
                    for item in image_downloads
                }
                
                for fut in as_completed(img_futures):
                    url, folder, filename = img_futures[fut]
                    local_path = fut.result()
                    if local_path:
                        downloaded_count += 1
                        
            print(f"Successfully downloaded {downloaded_count}/{len(image_downloads)} images to the 'images' folder.")
            
            # Re-save the final JSON with local_images populated in comments
            save_output_data(output_path, all_comments, title, base_url)
        else:
            print("\nNo new unique images found in comments to download.")

    print("\n--- Scraping complete! ---")
    print(f"Total comments successfully scraped: {len(all_comments)}")
    
    # Save a failed pages log file
    log_path = "scrape_failed_pages.log"
    if failed_pages:
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                for p in sorted(failed_pages):
                    f.write(f"{p}\n")
            print(f"[Warning] Recorded {len(failed_pages)} failed pages in '{log_path}'.")
        except Exception as e:
            print(f"[Warning] Failed to write failed pages log: {str(e)}")
    else:
        # Clear log if successful
        if os.path.exists(log_path):
            try:
                os.remove(log_path)
            except Exception:
                pass

if __name__ == "__main__":
    main()
