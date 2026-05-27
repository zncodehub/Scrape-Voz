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
    import urllib.parse
    ext = "jpg"
    
    # URL decode in case it's a proxy link
    decoded_url = urllib.parse.unquote(img_url)
    
    # If it's a proxy, check the unquoted parameters for nested extensions
    if "proxy.php" in decoded_url:
        for p in ["png", "jpg", "jpeg", "gif", "webp", "svg"]:
            if f".{p}" in decoded_url.lower():
                ext = p
                break
    else:
        # Simple extension detection
        if "." in decoded_url.split("/")[-1]:
            parts = decoded_url.split("/")[-1].split("?")[0].split(".")
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
    """Normalize the URL by removing trailing slashes and page suffixes."""
    url = url.strip()
    while url.endswith("/"):
        url = url[:-1]
    import re
    # Strip page suffixes like /page-123
    url = re.sub(r'/page-\d+$', '', url)
    return url

def extract_thread_id(url):
    """Extract thread ID from normalized URL."""
    import re
    import hashlib
    # Find the last segment
    last_segment = url.split('/')[-1]
    
    # If standard XenForo format: title-slug.1236656 or just digits
    if '.' in last_segment:
        last_part = last_segment.split('.')[-1]
        if last_part.isdigit():
            return last_part
    elif last_segment.isdigit():
        return last_segment
        
    # Search for digits at the end
    match = re.search(r'\b(\d+)\b', last_segment)
    if match:
        return match.group(1)
        
    # Fallback to MD5 hash prefix
    return hashlib.md5(url.encode('utf-8')).hexdigest()[:8]

def slugify_vietnamese(text, max_chars=10):
    """Normalize Vietnamese text to an ASCII slug with a length limit of original characters."""
    import re
    import unicodedata
    if not text:
        return "thread"
    
    # Slice the first max_chars characters
    truncated = text[:max_chars]
    
    # Map Vietnamese specific characters to ASCII equivalents
    vietnamese_map = {
        'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'đ': 'd',
        'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
        'À': 'a', 'Á': 'a', 'Ả': 'a', 'Ã': 'a', 'Ạ': 'a',
        'Ă': 'a', 'Ằ': 'a', 'Ắ': 'a', 'Ẳ': 'a', 'Ẵ': 'a', 'Ặ': 'a',
        'Â': 'a', 'Ầ': 'a', 'Ấ': 'a', 'Ẩ': 'a', 'Ẫ': 'a', 'Ậ': 'a',
        'Đ': 'd',
        'È': 'e', 'E': 'e', 'Ẻ': 'e', 'Ẽ': 'e', 'Ẹ': 'e',
        'Ê': 'e', 'Ề': 'e', 'Ế': 'e', 'Ể': 'e', 'Ễ': 'e', 'Ệ': 'e',
        'Ì': 'i', 'Í': 'i', 'Ỉ': 'i', 'Ĩ': 'i', 'Ị': 'i',
        'Ò': 'o', 'Ó': 'o', 'Ỏ': 'o', 'Õ': 'o', 'Ọ': 'o',
        'Ô': 'o', 'Ồ': 'o', 'Ố': 'o', 'Ổ': 'o', 'Ỗ': 'o', 'Ộ': 'o',
        'Ơ': 'o', 'Ờ': 'o', 'Ớ': 'o', 'Ở': 'o', 'Ỡ': 'o', 'Ợ': 'o',
        'Ù': 'u', 'Ú': 'u', 'Ủ': 'u', 'Ũ': 'u', 'Ụ': 'u',
        'Ư': 'u', 'Ừ': 'u', 'Ứ': 'u', 'Ử': 'u', 'Ữ': 'u', 'Ự': 'u',
        'Ỳ': 'y', 'Ý': 'y', 'Ỷ': 'y', 'Ỹ': 'y', 'Ỵ': 'y'
    }
    
    # Replace Vietnamese chars
    char_list = []
    for c in truncated:
        char_list.append(vietnamese_map.get(c, c))
    converted = "".join(char_list)
    
    # Decompose unicode to further strip remaining diacritics
    nfkd_form = unicodedata.normalize('NFKD', converted)
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('ASCII')
    
    # Lowercase and convert non-alphanumeric to hyphens
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', only_ascii.lower())
    
    # Clean leading/trailing hyphens
    slug = slug.strip('-')
    
    return slug or "thread"

def update_threads_registry(thread_id, thread_folder, title, url, total_comments):
    """Update the root-level threads.json registry with the scraped thread metadata."""
    from datetime import datetime
    registry_path = "threads.json"
    
    registry = []
    if os.path.exists(registry_path):
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                registry = json.load(f)
                if not isinstance(registry, list):
                    registry = []
        except Exception:
            registry = []
            
    # Find if thread already exists in registry
    existing_entry = None
    for entry in registry:
        if entry.get("id") == thread_id or entry.get("folder_name") == thread_folder:
            existing_entry = entry
            break
            
    last_scraped = datetime.now().astimezone().isoformat()
    
    if existing_entry:
        existing_entry["title"] = title
        existing_entry["url"] = url
        existing_entry["total_comments"] = total_comments
        existing_entry["last_scraped"] = last_scraped
        existing_entry["folder_name"] = thread_folder
    else:
        registry.append({
            "id": thread_id,
            "folder_name": thread_folder,
            "title": title,
            "url": url,
            "total_comments": total_comments,
            "last_scraped": last_scraped
        })
        
    try:
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)
            
        # Also save as a .js file containing a global variable for offline/file:// CORS bypass
        js_path = registry_path.replace(".json", ".js")
        with open(js_path, "w", encoding="utf-8") as f:
            f.write("window.threadsData = ")
            json.dump(registry, f, ensure_ascii=False, indent=2)
            f.write(";")
            
        print(f"Updated threads registry '{registry_path}' successfully.")
    except Exception as e:
        print(f"[Warning] Failed to update threads registry: {str(e)}")

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
                    
                # Prefer proxy.php URLs over direct data-url links to bypass hotlink blocks
                img_src = img.get("src") or ""
                img_data_src = img.get("data-src") or ""
                img_data_url = img.get("data-url") or ""
                
                src = None
                if "proxy.php" in img_src:
                    src = img_src
                elif "proxy.php" in img_data_src:
                    src = img_data_src
                else:
                    src = img_data_url or img_data_src or img_src
                    
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

# Magic byte signatures for common image formats
_IMAGE_MAGIC = [
    b"\x89PNG",          # PNG
    b"\xff\xd8\xff",     # JPEG
    b"GIF8",             # GIF
    b"RIFF",             # WebP (RIFF....WEBP)
    b"<svg",             # SVG
    b"<?xml",            # SVG via XML declaration
    b"\x00\x00\x01\x00", # ICO
]

def extract_original_url_from_proxy(url):
    """Extract the original direct image URL from a XenForo proxy.php link."""
    import urllib.parse
    try:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        if "image" in params:
            original = params["image"][0]
            if original.startswith("//"):
                original = "https:" + original
            return original
    except Exception:
        pass
    return None

def download_image(url, folder, filename, session=None):
    """Download an image from url and save to folder/filename.
    
    Uses streaming to validate magic bytes from the first chunk before writing,
    avoiding loading entire large images into memory upfront.
    Accepts an optional requests.Session for connection reuse.
    
    Includes robust fallback: if downloading from a proxy.php link fails (e.g. HTTP 404/500
    or connection errors), it automatically extracts and attempts download from the original
    direct source URL.
    """
    filepath = os.path.join(folder, filename)
    # Skip files that are already downloaded and non-empty
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        return filepath
    
    requester = session or requests
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://voz.vn/"
        }
        with requester.get(url, headers=headers, timeout=15, stream=True) as res:
            if res.status_code != 200:
                print(f"[Warning] Failed to download image (HTTP {res.status_code}): {url}")
                
                # Check for XenForo proxy fallback opportunity
                if "proxy.php" in url:
                    original_url = extract_original_url_from_proxy(url)
                    if original_url:
                        print(f"[Info] Proxy error. Attempting fallback to original source URL: {original_url}")
                        return download_image(original_url, folder, filename, session)
                return None
            
            content_type = res.headers.get("Content-Type", "").lower()
            if any(t in content_type for t in ("text/html", "text/plain", "application/json")):
                print(f"[Warning] Skipping non-image response for {url} (Content-Type: {content_type})")
                return None
            
            # Validate magic bytes from the first chunk before writing anything
            # Use iter_content to support automatic gzip/deflate stream decompression
            first_chunk = next(res.iter_content(chunk_size=12), b"")
            if not first_chunk:
                print(f"[Warning] Empty response for {url}. Skipping.")
                return None
            
            header = first_chunk.lstrip()
            is_image = content_type.startswith("image/") or any(header.startswith(m) for m in _IMAGE_MAGIC)
            if not is_image:
                print(f"[Warning] Non-image content for {url}. Skipping.")
                return None
            
            os.makedirs(folder, exist_ok=True)
            with open(filepath, "wb") as f:
                f.write(first_chunk)  # Write the already-read header
                for chunk in res.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
            return filepath
    except Exception as e:
        print(f"[Warning] Failed to download image {url}: {str(e)}")
        # Check for XenForo proxy fallback on exception
        if "proxy.php" in url:
            original_url = extract_original_url_from_proxy(url)
            if original_url:
                print(f"[Info] Exception occurred. Attempting fallback to original source URL: {original_url}")
                return download_image(original_url, folder, filename, session)
                
        # Remove partial file if write was interrupted
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
    return None

def resolve_proxy_images(comments):
    """Re-parse stored content HTML to replace hotlink-blocked URLs in images[] with proxy.php URLs.
    
    For existing scraped data where images[] may contain direct (blocked) external URLs,
    this function extracts any voz.vn/proxy.php URLs from data-src attributes in the content
    HTML and uses them in place of the blocked direct URLs.
    """
    import urllib.parse
    
    updated_count = 0
    for comment in comments:
        content = comment.get("content", "")
        if not content:
            continue
        
        # Parse the stored content HTML to find all img tags with data-src proxy URLs
        soup = BeautifulSoup(content, "html.parser")
        imgs = soup.find_all("img")
        
        # Build a mapping from blocked direct URL → proxy URL
        # by matching data-url (direct) with data-src (proxy) on the same img tag
        proxy_map = {}  # direct_url → proxy_url
        for img in imgs:
            img_data_src = img.get("data-src", "")
            img_data_url = img.get("data-url", "")
            if "proxy.php" in img_data_src and img_data_url:
                proxy_map[img_data_url] = img_data_src
                
        if not proxy_map:
            continue
            
        # Replace direct URLs in images[] with their corresponding proxy URLs
        original_images = comment.get("images", [])
        new_images = []
        for img_url in original_images:
            if img_url in proxy_map:
                new_images.append(proxy_map[img_url])
                updated_count += 1
            else:
                new_images.append(img_url)
        comment["images"] = new_images
        
    if updated_count:
        print(f"Resolved {updated_count} blocked image URL(s) to proxy URLs.")
    return comments

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
    """Save scraped comments to output JSON or CSV file and a .js file for CORS-free local loading."""
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
            
        data = {
            "thread_title": title,
            "thread_url": base_url,
            "total_comments": len(all_comments),
            "comments": all_comments
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        # Also save as a .js file containing a global variable for offline/file:// CORS bypass
        js_path = output_path.replace(".json", ".js")
        try:
            with open(js_path, "w", encoding="utf-8") as f:
                f.write("window.threadData = ")
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write(";")
        except Exception as e:
            print(f"[Warning] Failed to save .js fallback: {str(e)}")
            
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
        
    # 1. Extract thread ID
    thread_id = extract_thread_id(base_url)

    # 2. Detect thread details first to determine title
    title, detected_total = detect_thread_info(api_token, base_url)
    if not title:
        if args.end_page:
            title = "Unknown Voz Thread"
        else:
            sys.exit(1)
        
    # 3. Create target directory
    thread_slug = slugify_vietnamese(title, max_chars=10)
    thread_folder = f"{thread_id}_{thread_slug}"
    thread_dir = os.path.join("threads", thread_folder)
    os.makedirs(thread_dir, exist_ok=True)
    
    # 4. Determine output path
    filename = os.path.basename(args.output)
    if not filename.lower().endswith(".json") and not filename.lower().endswith(".csv"):
        filename += ".json"
    output_path = os.path.join(thread_dir, filename)
        
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
    
    # Replace any hotlink-blocked direct image URLs with their proxy.php equivalents
    # extracted from the content HTML (covers both freshly scraped and previously stored data)
    all_comments = resolve_proxy_images(all_comments)
    
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
        images_dir = os.path.join(thread_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        # Track unique image URLs and map them to their local filenames
        unique_images = {}  # url -> local_filename
        
        # Prepare unique mapping and local filenames for all comments in memory
        for comment in all_comments:
            comment["local_images"] = []
            for img_url in comment.get("images", []):
                if img_url not in unique_images:
                    filename = get_image_filename(img_url)
                    unique_images[img_url] = filename
                comment["local_images"].append(unique_images[img_url])
        
        # Only queue images that are not already downloaded
        image_downloads = [
            (url, images_dir, fname)
            for url, fname in unique_images.items()
            if not (os.path.exists(os.path.join(images_dir, fname)) and os.path.getsize(os.path.join(images_dir, fname)) > 0)
        ]
        already_count = len(unique_images) - len(image_downloads)
        if already_count:
            print(f"Skipping {already_count} already-downloaded image(s).")
                
        if image_downloads:
            print(f"\nDownloading {len(image_downloads)} image(s) concurrently (workers=20)...")
            downloaded_count = 0
            skipped_count = 0
            
            # Shared session per thread (thread-local) for HTTP connection reuse
            import threading
            thread_local = threading.local()
            def get_session():
                if not hasattr(thread_local, "session"):
                    thread_local.session = requests.Session()
                    thread_local.session.headers.update({
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                        "Referer": "https://voz.vn/"
                    })
                return thread_local.session
            
            def download_with_session(item):
                url, folder, filename = item
                return download_image(url, folder, filename, session=get_session())
            
            with ThreadPoolExecutor(max_workers=20) as img_executor:
                img_futures = {
                    img_executor.submit(download_with_session, item): item
                    for item in image_downloads
                }
                for fut in as_completed(img_futures):
                    local_path = fut.result()
                    if local_path:
                        downloaded_count += 1
                    else:
                        skipped_count += 1
                        
            print(f"Downloaded: {downloaded_count}  |  Failed/skipped: {skipped_count}  |  Already had: {already_count}")
            
            # Re-save the final JSON with local_images populated in comments
            save_output_data(output_path, all_comments, title, base_url)
        else:
            print("\nAll images already downloaded. Nothing new to fetch.")
            save_output_data(output_path, all_comments, title, base_url)

    # Copy thread_viewer.html template to index.html in the thread folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_paths = [
        os.path.join(script_dir, "thread_viewer.html"),
        "thread_viewer.html"
    ]
    template_copied = False
    for t_path in template_paths:
        if os.path.exists(t_path):
            import shutil
            shutil.copy(t_path, os.path.join(thread_dir, "index.html"))
            template_copied = True
            print(f"Copied viewer template to {os.path.join(thread_dir, 'index.html')}")
            break
            
    if not template_copied:
        print("[Warning] Could not find 'thread_viewer.html' template to copy.")

    # Update threads.json registry
    update_threads_registry(thread_id, thread_folder, title, base_url, len(all_comments))

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
