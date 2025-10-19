const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const loading = document.getElementById('loading');
const loadingText = document.getElementById('loadingText');
const results = document.getElementById('results');
const loadingMore = document.getElementById('loadingMore');

let eventSource = null;
let currentQuery = '';
let nextPageToken = null;
let isLoadingMore = false;
let displayedVideoIds = new Set();

searchButton.addEventListener('click', handleSearch);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleSearch();
    }
});

window.addEventListener('scroll', () => {
    if (isLoadingMore || !nextPageToken || !currentQuery) return;

    const scrollPosition = window.innerHeight + window.scrollY;
    const threshold = document.documentElement.scrollHeight - 500;

    if (scrollPosition >= threshold) {
        loadMoreVideos();
    }
});

function handleSearch() {
    const query = searchInput.value.trim();
    if (!query) return;

    if (eventSource) {
        eventSource.close();
    }

    currentQuery = query;
    nextPageToken = null;
    loadingMore.classList.add('hidden');
    displayedVideoIds.clear();

    loadingText.textContent = 'Searching and filtering results...';
    loading.classList.remove('hidden');
    results.innerHTML = '';

    let videoCount = 0;

    eventSource = new EventSource(`/search?query=${encodeURIComponent(query)}`);

    eventSource.onmessage = (event) => {
        const message = JSON.parse(event.data);

        if (message.type === 'video') {
            videoCount++;
            loadingText.textContent = `Found ${videoCount} video${videoCount !== 1 ? 's' : ''}...`;
            addVideoToResults(message.data);
        } else if (message.type === 'done') {
            eventSource.close();
            eventSource = null;
            loading.classList.add('hidden');

            nextPageToken = message.nextPageToken || null;

            if (videoCount === 0) {
                results.innerHTML = '<p style="text-align: center; color: #aaa;">No AI-free videos found.</p>';
            }
        } else if (message.type === 'error') {
            eventSource.close();
            eventSource = null;
            loading.classList.add('hidden');
            results.innerHTML = `<p class="error">Error: ${escapeHtml(message.message)}</p>`;
        }
    };

    eventSource.onerror = () => {
        eventSource.close();
        eventSource = null;
        loading.classList.add('hidden');

        if (videoCount === 0) {
            results.innerHTML = '<p class="error">An error occurred. Please try again.</p>';
        }
    };
}

function loadMoreVideos() {
    if (!nextPageToken || !currentQuery || isLoadingMore) return;

    isLoadingMore = true;
    loadingMore.classList.remove('hidden');

    if (eventSource) {
        eventSource.close();
    }

    let videoCount = 0;
    const url = `/search?query=${encodeURIComponent(currentQuery)}&pageToken=${encodeURIComponent(nextPageToken)}`;
    eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
        const message = JSON.parse(event.data);

        if (message.type === 'video') {
            videoCount++;
            addVideoToResults(message.data);
        } else if (message.type === 'done') {
            eventSource.close();
            eventSource = null;
            loadingMore.classList.add('hidden');
            isLoadingMore = false;

            nextPageToken = message.nextPageToken || null;
        } else if (message.type === 'error') {
            eventSource.close();
            eventSource = null;
            loadingMore.classList.add('hidden');
            isLoadingMore = false;
        }
    };

    eventSource.onerror = () => {
        eventSource.close();
        eventSource = null;
        loadingMore.classList.add('hidden');
        isLoadingMore = false;
    };
}

function addVideoToResults(video) {
    // Check for duplicates
    if (displayedVideoIds.has(video.video_id)) {
        console.log(`Skipping duplicate video: ${video.video_id}`);
        return;
    }

    displayedVideoIds.add(video.video_id);

    const videoCard = document.createElement('div');
    videoCard.className = 'video-card';
    videoCard.innerHTML = `
        <a href="${video.url}" target="_blank" rel="noopener noreferrer">
            <div class="thumbnail-container">
                <img src="${video.thumbnail}" alt="${escapeHtml(video.title)}">
            </div>
            <div class="video-info">
                <div class="video-title">${escapeHtml(video.title)}</div>
                <div class="video-channel">${escapeHtml(video.channel)}</div>
            </div>
        </a>
    `;
    results.appendChild(videoCard);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
