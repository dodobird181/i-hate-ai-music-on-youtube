import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from services.filter_service import FilterService
from services.youtube_service import YouTubeService

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

app = Flask(__name__)
app.config["YOUTUBE_API_KEY"] = os.getenv("YOUTUBE_API_KEY")
app.config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

app.config["MAX_VIDEOS_SEARCH_RESULTS"] = 50
app.config["EXCLUDE_VIDEOS_UNDER_N_COMMENTS"] = 50
app.config["MAX_COMMENTS_TO_ASSESS_PER_VIDEO"] = 100
app.config["PRE_AI_CUTOFF_DATE"] = datetime(2022, 5, 1, tzinfo=timezone.utc)

youtube_service = YouTubeService(app.config["YOUTUBE_API_KEY"])
filter_service = FilterService(app.config["OPENAI_API_KEY"], youtube_service)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    if not request.json:
        return jsonify({"error": "Expected JSON payload."}), 400
    query = request.json.get("query", "")
    if not query:
        return jsonify({"error": "Query is required"}), 400

    videos = youtube_service.search_videos(query, max_results=app.config["MAX_VIDEOS_SEARCH_RESULTS"])
    filtered_videos = filter_service.filter_videos(videos)

    return jsonify({"videos": filtered_videos})


if __name__ == "__main__":
    app.run(debug=True)
