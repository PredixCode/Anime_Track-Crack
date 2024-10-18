// player.js
export function playAnime(malAnimeId, episodeNumber) {
    const video = document.getElementById('video-player');
    const videoModal = document.getElementById('video-modal');
    const videoSrc = `/watch_anime/${malAnimeId}/${episodeNumber}`;

    // Display the video modal
    videoModal.style.display = 'block';

    // Check scroll position and set initial mode
    if (window.scrollY <= 200) {
        videoModal.classList.add('cinema-mode');
        videoModal.classList.remove('minimized');

        // Add cinema mode class to body
        document.body.classList.add('cinema-mode-active');
    } else {
        videoModal.classList.add('minimized');
        videoModal.classList.remove('cinema-mode');

        // Ensure cinema mode class is removed from body
        document.body.classList.remove('cinema-mode-active');
    }

    fetch(videoSrc)
        .then(response => {
            if (!response.ok) {
                return response.text().then(errorMessage => {
                    showErrorPopup(errorMessage, response.status);
                    videoModal.style.display = 'none';
                });
            }
            setupVideoPlayer(video, videoSrc);
        })
        .catch(error => {
            console.error('Error fetching video:', error);
            showErrorPopup('An unexpected error occurred.');
            videoModal.style.display = 'none';
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

function showErrorPopup(message) {
    const popup = document.createElement('div');
    popup.className = 'error-popup';
    popup.innerText = message;
    document.body.appendChild(popup);

    setTimeout(() => {
        popup.remove();
    }, 5000);
}
