import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from services.filter_service import FilterService
from services.youtube_service import YouTubeService

load_dotenv()

app = Flask(__name__)
app.config["YOUTUBE_API_KEY"] = os.getenv("YOUTUBE_API_KEY")
app.config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

youtube_service = YouTubeService(app.config["YOUTUBE_API_KEY"])
filter_service = FilterService(app.config["OPENAI_API_KEY"], youtube_service)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    query = request.json.get("query", "")
    if not query:
        return jsonify({"error": "Query is required"}), 400

    videos = youtube_service.search_videos(query)
    filtered_videos = filter_service.filter_videos(videos)

    return jsonify({"videos": filtered_videos})


if __name__ == "__main__":
    app.run(debug=True)
