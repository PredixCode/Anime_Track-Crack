// player.js
export function playAnime(malAnimeId, episodeNumber) {
    const video = document.getElementById('video-player');
    const videoSrc = `/watch_anime/${malAnimeId}/${episodeNumber}`;
    document.getElementById('video-modal').style.display = 'block';

    fetch(videoSrc)
        .then(response => {
            if (!response.ok) {
                handleVideoError(response.status);
                return;
            }
            setupVideoPlayer(video, videoSrc);
        })
        .catch(error => {
            console.error('Error fetching video:', error);
            showErrorPopup('An unexpected error occurred.');
        });
}

export async function downloadAnime(malAnimeId, episodeNumber, animeTitle) {
    try {
        const response = await fetch(`/download_anime/${malAnimeId}/${episodeNumber}`);
        if (response.ok) {
            alert(`Started downloading: ${animeTitle} Episode ${episodeNumber}`);
        } else {
            alert(`Failed to download: ${animeTitle} Episode ${episodeNumber}`);
        }
    } catch (error) {
        console.error('Error downloading anime:', error);
        alert('An unexpected error occurred while downloading.');
    }
}

// Helper Functions
function setupVideoPlayer(video, videoSrc) {
    if (Hls.isSupported()) {
        const hls = new Hls();
        hls.loadSource(videoSrc);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED, () => video.play());
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = videoSrc;
        video.addEventListener('loadedmetadata', () => video.play());
    } else {
        showErrorPopup('Your browser does not support HLS streaming.');
    }
}

function handleVideoError(status) {
    const errorMessages = {
        404: 'Video not found.',
        500: 'Internal server error. Please try again later.'
    };
    showErrorPopup(errorMessages[status] || 'An error occurred while fetching the video.');
    document.getElementById('video-modal').style.display = 'none';
}

function showErrorPopup(message) {
    const popup = document.createElement('div');
    popup.className = 'error-popup';
    popup.innerText = message;
    document.body.appendChild(popup);

    setTimeout(() => {
        popup.remove();
    }, 5000);
}
