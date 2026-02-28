from src.embeddings import VideoTitleEmbedding
from src.training import save_training_videos_with_data

save_training_videos_with_data(
    lambda video: {
        "title_embedding": VideoTitleEmbedding(video).get(),
        "label": video.label,
    },
    "data_science/tmp_data/sam_test_video_title_data.csv",
)
