Used blocklist of AI youtube channels from: https://surasshu.com/blocklist-for-ai-music-on-youtube/.

# Project Idea:
Create an indexed search / website for youtube specifically targeting people who want to listen to music on youtube that isn't made with AI.
## Methodology:
Use youtube's API to scrape comments and feed them to an LLM that searches for indirect evidence that the music is AI-generated. Or, maybe, train my own custom LLM using hand-picked examples of youtube comments and accounts / videos.
## Speed-ups:
1. Keep a database of youtube accounts; if they post >= 3 AI suspected videos, blacklist all of their other videos.
2. Ignore livestreams.
3. Don't grab comments for videos posted before May of 2022 and automatically greenlight them to be included in the search terms (since this was before LLMS were a thing and the internet was cleaner).
## Pitfalls:
This is clearly an imperfect / proxied way to identify AI-generated music in youtube videos and comes with some obvious pitfalls:
1. Unpopular / new youtube videos with low comment counts --> lower accuracy reading, will probably need to simply filter these videos out. Threshold will be around 50 comments which is usually around 8K views.
2. Livestreams may have a different commenting meta and should probably be excluded to preserve accuracy.
3. As time goes on people might say less about AI videos, commenting rules may change, etc., which may decrease accuracy over time.
