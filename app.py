import json
import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request

from services.filter_service import FilterService
from services.youtube_service import YouTubeService

load_dotenv()

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai._base_client").setLevel(logging.WARNING)
logging.getLogger("googleapiclient.http").setLevel(
    # 403s on videos with comments disabled show up as WARNINGS
    logging.ERROR
)

app = Flask(__name__)
app.config["YOUTUBE_API_KEY"] = os.getenv("YOUTUBE_API_KEY")
app.config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

app.config["MAX_VIDEOS_SEARCH_RESULTS"] = 5
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
    if not query:
        return jsonify({"error": "Query is required"}), 400

    def generate():
        try:
            videos = youtube_service.search_videos(query, max_results=app.config["MAX_VIDEOS_SEARCH_RESULTS"])

            count = 0
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

            yield f"data: {json.dumps({'type': 'done', 'count': count})}\n\n"

        except Exception as e:
            logging.error(f"Error during search: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(debug=True)
