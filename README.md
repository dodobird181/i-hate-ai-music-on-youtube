# Project Idea:
Create an indexed search / website for youtube specifically targeting people who want to listen to music on youtube that isn't made with AI.
## Methodology:
Use youtube's API to scrape comments and feed them to an LLM that searches for indirect evidence that the music is AI-generated. Or, maybe, train my own custom LLM using hand-picked examples of youtube comments and accounts / videos.
## Speed-ups:
1. Keep a database of youtube accounts; if they post >= 3 AI suspected videos, blacklist all of their other videos.
2. Ignore livestreams.
3. Don't grab comments for videos posted before May of 2022 and automatically greenlight them to be included in the search terms (since this was before LLMS were a thing and the internet was cleaner). 
