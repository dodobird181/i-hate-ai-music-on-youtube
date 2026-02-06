import json
import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request

from models import Comment, Video
from predictions import predict
from youtube import OfficialYouTubeService

load_dotenv()

logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logging.getLogger("services.youtube_service").setLevel(logging.DEBUG)
logging.getLogger("services.filter_service").setLevel(logging.DEBUG)

app = Flask(__name__)
app.config["YOUTUBE_API_KEY"] = os.getenv("YOUTUBE_API_KEY")

app.config["MAX_VIDEOS_SEARCH_RESULTS"] = 5
app.config["EXCLUDE_VIDEOS_UNDER_N_COMMENTS"] = 50
app.config["MAX_COMMENTS_TO_ASSESS_PER_VIDEO"] = 100
app.config["PRE_AI_CUTOFF_DATE"] = datetime(2022, 5, 1, tzinfo=timezone.utc)

youtube = OfficialYouTubeService.build_from_env(origin=Video.Origin.APP)


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
            max_pages_to_fetch = 50  # Safety limit to prevent infinite loops

            pages_fetched = 0

            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Searching...'})}\n\n"

            # Keep fetching until we have enough videos (for initial load) or fetched one page (for pagination)
            while True:
                videos_response = youtube.videos(
                    query,
                    max_results=app.config["MAX_VIDEOS_SEARCH_RESULTS"],
                    page_token=current_page_token,
                )
                pages_fetched += 1

                human_videos = []
                videos = [x for x in videos_response.videos if x.comments >= 50 and x.duration_seconds > 60]
                for video in videos:

                    # Save video
                    if Video.filter(id=video.id).select().count() == 0:
                        video.save(force_insert=True)
                    else:
                        video.save()

                    # Download and save video comments
                    comments = youtube.get_comments(video_id=str(video.id), max_results=100)
                    for comment in comments:
                        if Comment.filter(id=comment.id).select().count() == 0:
                            comment.save(force_insert=True)
                        else:
                            comment.save()

                    # Predict human or ai
                    if predict(video, threshold=0.95) == Video.Label.HUMAN:
                        human_videos.append(video)
                        video.label = Video.Label.HUMAN.value  # type: ignore
                    else:
                        video.label = Video.Label.AI.value  # type: ignore

                    # Save video again (to save the human/ai label)
                    if Video.filter(id=video.id).select().count() == 0:
                        video.save(force_insert=True)
                    else:
                        video.save()

                for video in human_videos:
                    count += 1
                    video_data = {
                        "video_id": video.id,
                        "title": video.title,
                        "url": video.url,
                        "thumbnail": video.thumbnail_url,
                        "channel": video.channel_name,
                        "channel_id": video.channel_id,
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
                if videos_response.next_page_token is None:
                    break
                if pages_fetched >= max_pages_to_fetch:
                    logging.warning(f"Reached max pages ({max_pages_to_fetch}) while searching for videos")
                    break

                # Continue to next page
                current_page_token = videos_response.next_page_token

            yield f"data: {json.dumps({'type': 'done', 'count': count, 'nextPageToken': videos_response.next_page_token})}\n\n"

        except Exception as e:
            logging.error(f"Error during search!", exc_info=e)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(debug=True)
