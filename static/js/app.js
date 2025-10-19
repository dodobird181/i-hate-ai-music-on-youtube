const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const loading = document.getElementById('loading');
const results = document.getElementById('results');

let eventSource = null;

searchButton.addEventListener('click', handleSearch);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleSearch();
    }
});

function handleSearch() {
    const query = searchInput.value.trim();
    if (!query) return;

    if (eventSource) {
        eventSource.close();
    }

    loading.textContent = 'Searching and filtering results...';
    loading.classList.remove('hidden');
    results.innerHTML = '';

    let videoCount = 0;

    eventSource = new EventSource(`/search?query=${encodeURIComponent(query)}`);

    eventSource.onmessage = (event) => {
        const message = JSON.parse(event.data);

        if (message.type === 'video') {
            videoCount++;
            loading.textContent = `Found ${videoCount} video${videoCount !== 1 ? 's' : ''}...`;
            addVideoToResults(message.data);
        } else if (message.type === 'done') {
            eventSource.close();
            eventSource = null;
            loading.classList.add('hidden');

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

function addVideoToResults(video) {
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
