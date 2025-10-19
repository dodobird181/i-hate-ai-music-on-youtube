const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const loading = document.getElementById('loading');
const results = document.getElementById('results');

searchButton.addEventListener('click', handleSearch);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleSearch();
    }
});

async function handleSearch() {
    const query = searchInput.value.trim();
    if (!query) return;

    loading.classList.remove('hidden');
    results.innerHTML = '';

    try {
        const response = await fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
        });

        const data = await response.json();

        if (data.error) {
            results.innerHTML = `<p class="error">${data.error}</p>`;
            return;
        }

        displayResults(data.videos);
    } catch (error) {
        results.innerHTML = '<p class="error">An error occurred. Please try again.</p>';
    } finally {
        loading.classList.add('hidden');
    }
}

function displayResults(videos) {
    if (!videos || videos.length === 0) {
        results.innerHTML = '<p style="text-align: center; color: #aaa;">No results found.</p>';
        return;
    }

    results.innerHTML = videos.map(video => `
        <div class="video-card">
            <a href="${video.url}" target="_blank" rel="noopener noreferrer">
                <div class="thumbnail-container">
                    <img src="${video.thumbnail}" alt="${escapeHtml(video.title)}">
                </div>
                <div class="video-info">
                    <div class="video-title">${escapeHtml(video.title)}</div>
                    <div class="video-channel">${escapeHtml(video.channel)}</div>
                    ${video.pre_ai_era ? '<span class="badge">Pre-AI Era</span>' : ''}
                </div>
            </a>
        </div>
    `).join('');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
