import os
import sys
import subprocess
from flask import Flask, render_template, request, Response, send_from_directory, send_file

# Try to load environment variables from a .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)

# Ensure the threads directory exists
os.makedirs("threads", exist_ok=True)

@app.route("/")
def index():
    """Render the main Scraper Control Panel UI."""
    return render_template("scraper_ui.html")

@app.route("/explorer")
def explorer():
    """Serve the root index.html Thread Explorer."""
    if os.path.exists("index.html"):
        return send_file("index.html")
    return "Error: Root 'index.html' not found in workspace.", 404

@app.route("/threads.json")
def threads_json():
    """Serve the global threads registry metadata JSON."""
    if os.path.exists("threads.json"):
        return send_file("threads.json")
    return "[]", 200

@app.route("/threads.js")
def threads_js():
    """Serve the global threads registry fallback JS."""
    if os.path.exists("threads.js"):
        return send_file("threads.js")
    return "window.threadData = [];", 200

@app.route("/threads/<path:filename>")
def serve_threads_files(filename):
    """Serve static files (comments, images, subfolders) inside threads directory."""
    return send_from_directory("threads", filename)

@app.route("/api/scrape-stream")
def scrape_stream():
    """Spawn the scrape_voz.py scraper as a subprocess and stream logs via SSE."""
    url = request.args.get("url")
    if not url:
        return Response("data: [Error] Missing required URL parameter.\n\n", mimetype="text/event-stream")

    start_page = request.args.get("start_page")
    end_page = request.args.get("end_page")
    download_images = request.args.get("download_images")
    fetch_reactions = request.args.get("fetch_reactions")
    force = request.args.get("force")

    # Build python scraper subprocess CLI arguments
    cmd = [sys.executable, "-u", "scrape_voz.py", "--url", url]

    if start_page and start_page.strip().isdigit():
        cmd.extend(["--start-page", start_page.strip()])
    
    if end_page and end_page.strip().isdigit():
        cmd.extend(["--end-page", end_page.strip()])

    if download_images == "true":
        cmd.append("--download-images")

    if fetch_reactions == "true":
        cmd.append("--fetch-reactions")

    if force == "true":
        cmd.append("--force")

    def generate_logs():
        yield f"data: [System] Spawning scraper subprocess: {' '.join(cmd)}\n\n"
        
        # Merge stderr to stdout to catch all exceptions and warnings
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line-buffered
            encoding="utf-8",
            errors="replace"
        )

        try:
            # Iteratively stream stdout lines
            for line in iter(process.stdout.readline, ""):
                stripped_line = line.rstrip("\r\n")
                yield f"data: {stripped_line}\n\n"

            process.stdout.close()
            return_code = process.wait()

            if return_code == 0:
                yield "data: PROCESS COMPLETED SUCCESSFULLY\n\n"
            else:
                yield f"data: PROCESS TERMINATED WITH ERROR (Exit code: {return_code})\n\n"

        except GeneratorExit:
            # Client aborted/closed browser connection - terminate the subprocess
            yield "data: [System] Client connection interrupted. Terminating scraper process...\n\n"
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
        except Exception as e:
            yield f"data: PROCESS TERMINATED WITH ERROR: {str(e)}\n\n"

    response = Response(generate_logs(), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response

@app.route("/api/delete-thread", methods=["POST"])
def delete_thread():
    """Delete a thread from the disk, images, and remove it from the threads.json registry."""
    import shutil
    import json
    
    thread_id = request.args.get("id")
    if not thread_id:
        return {"status": "error", "message": "Missing required thread ID"}, 400

    registry_path = "threads.json"
    js_path = "threads.js"
    
    if not os.path.exists(registry_path):
        return {"status": "error", "message": "No registry found on server"}, 404
        
    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)
    except Exception as e:
        return {"status": "error", "message": f"Failed to load registry: {str(e)}"}, 500

    # Find the thread by ID
    target_thread = None
    updated_registry = []
    for t in registry:
        if str(t.get("id")) == str(thread_id):
            target_thread = t
        else:
            updated_registry.append(t)
            
    if not target_thread:
        return {"status": "error", "message": f"Thread with ID {thread_id} not found in registry"}, 404

    folder_name = target_thread.get("folder_name")
    if not folder_name:
        return {"status": "error", "message": "No folder name associated with thread in registry"}, 404

    thread_dir = os.path.join("threads", folder_name)
    
    # 1. Delete the thread folder and all its contents (comments.json, index.html, comments.js, images/)
    if os.path.exists(thread_dir):
        try:
            shutil.rmtree(thread_dir)
            print(f"[Info] Deleted thread folder: {thread_dir}")
        except Exception as e:
            return {"status": "error", "message": f"Failed to delete thread folder '{folder_name}': {str(e)}"}, 500
    else:
        print(f"[Warning] Thread folder '{folder_name}' not found on disk, but removing from registry anyway.")

    # 2. Save the updated threads.json registry
    try:
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(updated_registry, f, ensure_ascii=False, indent=2)
            
        # 3. Update the threads.js static fallback file
        with open(js_path, "w", encoding="utf-8") as f:
            f.write("window.threadsData = ")
            json.dump(updated_registry, f, ensure_ascii=False, indent=2)
            f.write(";")
            
        print(f"[Info] Removed thread ID {thread_id} from registry successfully")
        return {"status": "success", "message": "Thread deleted successfully"}
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to update registry files: {str(e)}"}, 500

if __name__ == "__main__":
    print("--------------------------------------------------")
    print("Voz Scraper Flask Server is starting...")
    print("Access Scraper Panel:  http://127.0.0.1:5000/")
    print("Access Thread Explorer: http://127.0.0.1:5000/explorer")
    print("--------------------------------------------------")
    app.run(host="127.0.0.1", port=5000, debug=True)
