import json
import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request

from services.filter_service import FilterService
from services.youtube_service import YouTubeService

load_dotenv()

logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logging.getLogger("services.youtube_service").setLevel(logging.DEBUG)
logging.getLogger("services.filter_service").setLevel(logging.DEBUG)

app = Flask(__name__)
app.config["YOUTUBE_API_KEY"] = os.getenv("YOUTUBE_API_KEY")
app.config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

app.config["MAX_VIDEOS_SEARCH_RESULTS"] = 20
app.config["EXCLUDE_VIDEOS_UNDER_N_COMMENTS"] = 50
app.config["MAX_COMMENTS_TO_ASSESS_PER_VIDEO"] = 100
app.config["PRE_AI_CUTOFF_DATE"] = datetime(2022, 5, 1, tzinfo=timezone.utc)

youtube_service = YouTubeService(app.config["YOUTUBE_API_KEY"])
filter_service = FilterService(app, app.config["OPENAI_API_KEY"], youtube_service)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query", "")
    page_token = request.args.get("pageToken", None)
    if not query:
        return jsonify({"error": "Query is required"}), 400

    def generate():
        try:
            count = 0
            current_page_token = page_token
            is_initial_load = page_token is None
            min_videos_for_initial_load = 15
            max_pages_to_fetch = 10  # Safety limit to prevent infinite loops

            pages_fetched = 0

            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Searching...'})}\n\n"

            # Keep fetching until we have enough videos (for initial load) or fetched one page (for pagination)
            while True:
                videos, next_page_token = youtube_service.search_videos(
                    query, max_results=app.config["MAX_VIDEOS_SEARCH_RESULTS"], page_token=current_page_token
                )
                pages_fetched += 1

                for video in filter_service.filter_videos_streaming(videos):
                    count += 1
                    video_data = {
                        "video_id": video.id,
                        "title": video.title,
                        "url": video.url,
                        "thumbnail": video.thumbnail_url,
                        "channel": video.channel.title,
                        "channel_id": video.channel.id,
                    }
                    yield f"data: {json.dumps({'type': 'video', 'data': video_data})}\n\n"

                    # Send status update with count
                    plural = "s" if count != 1 else ""
                    status_msg = f"Found {count} video{plural}..."
                    yield f"data: {json.dumps({'type': 'status', 'message': status_msg})}\n\n"

                # Stop conditions:
                # 1. For pagination requests: always stop after one page
                # 2. For initial load: stop if we have enough videos, no more pages, or hit safety limit
                if not is_initial_load:
                    break
                if count >= min_videos_for_initial_load:
                    break
                if next_page_token is None:
                    break
                if pages_fetched >= max_pages_to_fetch:
                    logging.warning(f"Reached max pages ({max_pages_to_fetch}) while searching for videos")
                    break

                # Continue to next page
                current_page_token = next_page_token

            yield f"data: {json.dumps({'type': 'done', 'count': count, 'nextPageToken': next_page_token})}\n\n"

        except Exception as e:
            logging.error(f"Error during search: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(debug=True)
