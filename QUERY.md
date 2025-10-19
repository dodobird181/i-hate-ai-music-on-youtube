# AI Detection Query Template

## Instructions
This prompt template is used to analyze YouTube video comments to detect if music is AI-generated.
The placeholders {video_title}, {channel_name}, and {comments} will be automatically filled.

## Prompt

Analyze the following YouTube music video to determine if it contains AI-generated music.

**Video Title:** {video_title}
**Channel:** {channel_name}

**Comments:**
```
{comments}
```

### Detection Criteria

Look for indirect evidence in the comments such as:
- Comments mentioning "AI", "artificial intelligence", "AI-generated", "bot music"
- Comments about the music sounding "soulless", "generic", or "computer-generated"
- Discussions about the channel mass-producing content
- Comments questioning if it's real music or made by humans
- Patterns of suspicious positive comments that seem automated
- Lack of genuine engagement or specific musical discussion
- Comments about repetitive or formulaic song structures

### What NOT to flag:
- Use of AI for mixing/mastering (common production tool)
- AI-assisted artwork or thumbnails
- Comments about voice filters or autotune
- General music criticism unrelated to AI generation

Respond with ONLY one word: "HUMAN" if the music appears to be human-made, or "AI" if evidence suggests AI-generated content.
