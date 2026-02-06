from dataclasses import dataclass
from json import dumps
from re import findall, sub
from typing import List

from emoji import demojize, emoji_list
from numpy import mean, ndarray, std, triu_indices_from
from sklearn.metrics.pairwise import cosine_similarity
from textstat import textstat

from embedding import Sentence
from lists import AI_KEYWORDS, GENERIC_PRAISE
from models import Comment, Video

# Regex string that matches URLs.
URL_REGEX = r"https?://\S+|www\.\S+"


@dataclass
class VideoFeatures:

    @dataclass
    class Comments:
        average_len: int
        # Percent of comments with 6 or less words
        percent_short: float
        # Percent of comments, after cleaning, that have identical text
        percent_duplicate: float
        # The percent of emojis compared to words across all comments
        emoji_density: float
        # The percent of unique words across all comments (emojis count as words here)
        percent_unique_words: float
        # The percent of comments containing any number of generic praise phrases (these are explicitly defined)
        generic_praise_ratio: float
        # Standard deviation, variance, mean similarity, and similarity standard deviation between comment embeddings
        std: float
        variance: float
        mean_similarity: float
        similarity_std: float

        # Serialized string of all comment embeddings
        embeddings: str

    @dataclass
    class Description:
        len: int
        # Readability score produced by the textstat library
        readability_score: float
        num_links: int
        # The number of AI keywords (these are explicitly defined)
        num_ai_keywords: int
        contains_ai_keywords: bool

    description: Description
    comments: Comments
    embeddings: List[ndarray]


def _clean_comment(text: str) -> str:
    text = text.strip().lower()
    text = demojize(text)
    sub(URL_REGEX, "", text)
    return text


def _average_seconds_between_channel_uploads(self, video: Video) -> int:
    channel_videos = Video.select().where(Video.channel_id == video.channel_id)
    datetimes = [x.published_at for x in channel_videos]
    # TODO


def extract_videos(videos: List[Video]) -> List[VideoFeatures]:
    features_list = []
    for video in videos:
        comments = Comment.select().where(Comment.video == video.id)
        features = extract(video, comments)
        features_list.append(features)
    return features_list


def extract(video: Video, comments: list[Comment]) -> VideoFeatures:

    num_ai_keywords = 0
    for ai_keyword in AI_KEYWORDS:
        if ai_keyword in video.description:
            num_ai_keywords += 1

    readability = textstat.flesch_reading_ease(str(video.description))
    urls = findall(URL_REGEX, str(video.description))

    desc_features = VideoFeatures.Description(
        len=len(str(video.description)),
        readability_score=readability,
        num_links=len(urls),
        num_ai_keywords=num_ai_keywords,
        contains_ai_keywords=bool(num_ai_keywords > 0),
    )

    unique_words = set()
    dirty_comment_blob = ""
    cleaned_comment_texts = []
    num_comments = len(comments)
    num_duplicates = 0
    comment_lens = []
    num_short = 0
    num_generic_praise = 0
    embeddings = Sentence().encode([x.text for x in comments], batch_size=64, show_progress_bar=False)  # type: ignore

    if num_comments != 0:
        for comment in comments:
            dirty = str(comment.text)
            cleaned = _clean_comment(dirty)

            # Length before cleaning (since I want emojis to count as 1 character)
            comment_lens.append(len(dirty))

            # Duplicates after cleaning (since I want to exclude leading and trailing whitespace from duplicates)
            if cleaned in cleaned_comment_texts:
                num_duplicates += 1

            # Num short before cleaning (since I want emojis to count as one character)
            num_words = len(dirty.split())
            if num_words <= 6:
                num_short += 1

            # Append to cleaned comments list
            cleaned_comment_texts.append(cleaned)

            # Append to dirty comments blob
            dirty_comment_blob += f" {dirty}"

            # Append to unique words
            for word in dirty.split():
                unique_words.add(word)

            # Append to generic praise
            for generic_praise in GENERIC_PRAISE:
                if generic_praise in dirty:
                    num_generic_praise += 1

        total_words = len(dirty_comment_blob.split())
        average_len = int(sum(comment_lens) / num_comments)
        emoji_density = len(emoji_list(dirty_comment_blob)) / total_words
        generic_praise_ratio = num_generic_praise / num_comments

        sim = cosine_similarity(embeddings)
        upper = sim[triu_indices_from(sim, k=1)]

        mean_similarity = upper.mean()
        std_similarity = upper.std()
        comment_variance_score = mean(std(embeddings, axis=0))
        similarity_matrix = cosine_similarity(embeddings)
        N = similarity_matrix.shape[0]
        percent_unique_words = len(unique_words) / total_words

        sims = similarity_matrix[triu_indices_from(similarity_matrix, k=1)]
        similarity_std = float(std(sims))

        comments_features = VideoFeatures.Comments(
            average_len=average_len,
            percent_short=num_short / num_comments,
            percent_duplicate=num_duplicates / num_comments,
            emoji_density=emoji_density,
            percent_unique_words=percent_unique_words,
            generic_praise_ratio=generic_praise_ratio,
            std=float(std_similarity),
            variance=float(comment_variance_score),
            mean_similarity=float(mean_similarity),
            similarity_std=similarity_std,
            embeddings=dumps(embeddings.tolist()),
        )
    else:
        comments_features = VideoFeatures.Comments(
            average_len=0,
            percent_short=0,
            percent_duplicate=0,
            emoji_density=0,
            percent_unique_words=0,
            generic_praise_ratio=0,
            std=0,
            variance=0,
            mean_similarity=0,
            similarity_std=0,
            embeddings=embeddings,
        )

    return VideoFeatures(description=desc_features, comments=comments_features, embeddings=embeddings)
