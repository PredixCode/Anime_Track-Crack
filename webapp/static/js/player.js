// player.js

/**
 * Generates a unique key for storing playback time based on animeId and episodeNumber.
 * @param {number} malAnimeId - The unique ID of the anime.
 * @param {number} episodeNumber - The episode number.
 * @returns {string} - The generated localStorage key.
 */
function getPlaybackKey(malAnimeId, episodeNumber) {
    return `watched_${malAnimeId}_${episodeNumber}`;
}

/**
 * Saves the current playback time to localStorage.
 * @param {number} malAnimeId - The unique ID of the anime.
 * @param {number} episodeNumber - The episode number.
 * @param {number} currentTime - The current playback time in seconds.
 */
function savePlaybackTime(malAnimeId, episodeNumber, currentTime) {
    const key = getPlaybackKey(malAnimeId, episodeNumber);
    localStorage.setItem(key, currentTime);
}

/**
 * Retrieves the saved playback time from localStorage.
 * @param {number} malAnimeId - The unique ID of the anime.
 * @param {number} episodeNumber - The episode number.
 * @returns {number|null} - The saved playback time in seconds or null if not found.
 */
function getSavedPlaybackTime(malAnimeId, episodeNumber) {
    const key = getPlaybackKey(malAnimeId, episodeNumber);
    const time = localStorage.getItem(key);
    return time ? parseFloat(time) : null;
}

/**
 * Removes the saved playback time from localStorage.
 * @param {number} malAnimeId - The unique ID of the anime.
 * @param {number} episodeNumber - The episode number.
 */
function removePlaybackTime(malAnimeId, episodeNumber) {
    const key = getPlaybackKey(malAnimeId, episodeNumber);
    localStorage.removeItem(key);
}

/**
 * Generates a unique key for storing last watched episode based on animeId.
 * @param {number} malAnimeId - The unique ID of the anime.
 * @returns {string} - The generated localStorage key.
 */
function getLastWatchedKey(malAnimeId) {
    return `last_watched_${malAnimeId}`;
}

/**
 * Saves the last watched episode details to localStorage.
 * @param {number} malAnimeId - The unique ID of the anime.
 * @param {number} episodeNumber - The episode number.
 */
function saveLastWatchedEpisode(malAnimeId, episodeNumber) {
    const key = getLastWatchedKey(malAnimeId);
    const data = {
        episodeNumber: episodeNumber,
        timestamp: Date.now()
    };
    localStorage.setItem(key, JSON.stringify(data));
}

/**
 * Retrieves the last watched episode details from localStorage.
 * @param {number} malAnimeId - The unique ID of the anime.
 * @returns {object|null} - The saved episode details or null if not found.
 */
function getLastWatchedEpisode(malAnimeId) {
    const key = getLastWatchedKey(malAnimeId);
    const data = localStorage.getItem(key);
    return data ? JSON.parse(data) : null;
}

/**
 * Clears the last watched episode details from localStorage.
 * @param {number} malAnimeId - The unique ID of the anime.
 */
function clearLastWatchedEpisode(malAnimeId) {
    const key = getLastWatchedKey(malAnimeId);
    localStorage.removeItem(key);
}

export function playAnime(malAnimeId, episodeNumber) {
    const video = document.getElementById('video-player');
    const videoModal = document.getElementById('video-modal');
    const videoSrc = `/watch_anime/${malAnimeId}/${episodeNumber}`;

    // Save the last watched episode details
    saveLastWatchedEpisode(malAnimeId, episodeNumber);

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
            setupVideoPlayer(video, videoSrc, malAnimeId, episodeNumber);
        })
        .catch(error => {
            console.error('Error fetching video:', error);
            showErrorPopup('An unexpected error occurred.');
            videoModal.style.display = 'none';
        });
}

export function downloadAnime(malAnimeId, episodeNumber, animeTitle) {
    const downloadUrl = `/download_anime/${malAnimeId}/${episodeNumber}`;
    
    // Create a temporary link element
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `${animeTitle}_episode_${episodeNumber}.ts`; // This may be overridden by server headers
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Helper Functions
function setupVideoPlayer(video, videoSrc, malAnimeId, episodeNumber) {
    if (Hls.isSupported()) {
        const hlsConfig = {
            maxBufferLength: 2.5 * 60,           // 2.5 minutes
            maxMaxBufferLength: 5 * 60,          // 5 minutes
            maxBufferSize: 1000 * 1000 * 1000,   // 1GB
            maxBufferHole: 0.5,                  // 0.5 seconds
            startPosition: -1,
            startMaxNotBuffered: 10,
        };

        const hls = new Hls(hlsConfig);
        hls.loadSource(videoSrc);
        hls.attachMedia(video);

        hls.on(Hls.Events.MANIFEST_PARSED, () => {
            // Check for saved playback time
            const savedTime = getSavedPlaybackTime(malAnimeId, episodeNumber);
            if (savedTime !== null && savedTime > 0) {
                video.currentTime = savedTime;
                console.log(`Resuming playback at ${savedTime} seconds.`);
            }
            video.play();
        });


        hls.on(Hls.Events.BUFFER_FULL, () => {
            console.log('Buffer is full.');
        });

        // Handle errors
        hls.on(Hls.Events.ERROR, function (event, data) {
            if (data.fatal) {
                switch (data.type) {
                    case Hls.ErrorTypes.NETWORK_ERROR:
                        console.error('Network error encountered, trying to recover...');
                        hls.startLoad();
                        break;
                    case Hls.ErrorTypes.MEDIA_ERROR:
                        console.error('Media error encountered, trying to recover...');
                        hls.recoverMediaError();
                        break;
                    default:
                        hls.destroy();
                        break;
                }
            }
        });

        // Event listener to save playback time periodically
        const saveInterval = 5000; // Save every 5 seconds
        let saveTimer = setInterval(() => {
            if (!video.paused && !video.ended) {
                savePlaybackTime(malAnimeId, episodeNumber, video.currentTime);
                console.log(`Saved playback time: ${video.currentTime} seconds.`);
            }
        }, saveInterval);

        // Clear the interval when video is paused or ended
        video.addEventListener('pause', () => {
            clearInterval(saveTimer);
            saveTimer = null;
            savePlaybackTime(malAnimeId, episodeNumber, video.currentTime);
            console.log(`Video paused. Saved playback time: ${video.currentTime} seconds.`);
        });

        video.addEventListener('ended', () => {
            clearInterval(saveTimer);
            saveTimer = null;
            removePlaybackTime(malAnimeId, episodeNumber);
            clearLastWatchedEpisode(malAnimeId); // Clear last watched details
            console.log(`Video ended. Removed saved playback time and last watched details.`);
        });

    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = videoSrc;
        video.addEventListener('loadedmetadata', () => {
            // Check for saved playback time
            const savedTime = getSavedPlaybackTime(malAnimeId, episodeNumber);
            if (savedTime !== null && savedTime > 0) {
                video.currentTime = savedTime;
                console.log(`Resuming playback at ${savedTime} seconds.`);
            }
            video.play();
        });

        // Event listener to save playback time periodically
        const saveInterval = 5000; // Save every 5 seconds
        let saveTimer = setInterval(() => {
            if (!video.paused && !video.ended) {
                savePlaybackTime(malAnimeId, episodeNumber, video.currentTime);
                console.log(`Saved playback time: ${video.currentTime} seconds.`);
            }
        }, saveInterval);

        // Clear the interval when video is paused or ended
        video.addEventListener('pause', () => {
            clearInterval(saveTimer);
            saveTimer = null;
            savePlaybackTime(malAnimeId, episodeNumber, video.currentTime);
            console.log(`Video paused. Saved playback time: ${video.currentTime} seconds.`);
        });

        video.addEventListener('ended', () => {
            clearInterval(saveTimer);
            saveTimer = null;
            removePlaybackTime(malAnimeId, episodeNumber);
            clearLastWatchedEpisode(malAnimeId); // Clear last watched details
            console.log(`Video ended. Removed saved playback time and last watched details.`);
        });

    } else {
        showErrorPopup('Your browser does not support HLS streaming.');
    }
}

function showErrorPopup(message, status = null) {
    const popup = document.createElement('div');
    popup.className = 'error-popup';
    popup.innerText = message;
    if (status) {
        popup.innerText += ` (Status: ${status})`;
    }
    document.body.appendChild(popup);

    setTimeout(() => {
        popup.remove();
    }, 5000);
}

// Export utility functions for last watched episode management
export {
    getLastWatchedKey,
    saveLastWatchedEpisode,
    getLastWatchedEpisode,
    clearLastWatchedEpisode
};
