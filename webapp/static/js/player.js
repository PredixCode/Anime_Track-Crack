// player.js

let hlsInstance = null; // Global HLS instance
let currentResolution = null; // Track current resolution

/**
 * API Endpoints
 */
const API_BASE_URL = '/api';

/**
 * Saves the current playback time to the server session.
 * @param {number} malAnimeId - The unique ID of the anime.
 * @param {number} episodeNumber - The episode number.
 * @param {number} currentTime - The current playback time in seconds.
 */
async function savePlaybackTime(malAnimeId, episodeNumber, currentTime) {
    try {
        const response = await fetch(`${API_BASE_URL}/save_playback_time`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ malAnimeId, episodeNumber, currentTime })
        });

        if (response.ok) {
            console.log(`Playback time saved: ${currentTime} seconds for Anime ID ${malAnimeId}, Episode ${episodeNumber}`);
        } else {
            console.error('Failed to save playback time.');
        }
    } catch (error) {
        console.error('Error saving playback time:', error);
    }
}

/**
 * Retrieves the saved playback time from the server session.
 * @param {number} malAnimeId - The unique ID of the anime.
 * @param {number} episodeNumber - The episode number.
 * @returns {number|null} - The saved playback time in seconds or null if not found.
 */
async function getSavedPlaybackTime(malAnimeId, episodeNumber) {
    try {
        const response = await fetch(`${API_BASE_URL}/get_playback_time?malAnimeId=${malAnimeId}&episodeNumber=${episodeNumber}`);
        if (response.ok) {
            const data = await response.json();
            return data.currentTime !== undefined ? parseFloat(data.currentTime) : null;
        } else {
            console.error('Failed to retrieve playback time.');
            return null;
        }
    } catch (error) {
        console.error('Error retrieving playback time:', error);
        return null;
    }
}

/**
 * Removes the saved playback time from the server session.
 * @param {number} malAnimeId - The unique ID of the anime.
 * @param {number} episodeNumber - The episode number.
 */
async function removePlaybackTime(malAnimeId, episodeNumber) {
    try {
        const response = await fetch(`${API_BASE_URL}/remove_playback_time`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ malAnimeId, episodeNumber })
        });

        if (response.ok) {
            console.log(`Playback time removed for Anime ID ${malAnimeId}, Episode ${episodeNumber}`);
        } else {
            console.error('Failed to remove playback time.');
        }
    } catch (error) {
        console.error('Error removing playback time:', error);
    }
}

/**
 * Saves the last watched episode details to the server session.
 * @param {number} malAnimeId - The unique ID of the anime.
 * @param {number} episodeNumber - The episode number.
 */
async function saveLastWatchedEpisode(malAnimeId, episodeNumber) {
    try {
        const response = await fetch(`${API_BASE_URL}/save_last_watched`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ malAnimeId, episodeNumber })
        });

        if (response.ok) {
            console.log(`Last watched episode saved: Anime ID ${malAnimeId}, Episode ${episodeNumber}`);
        } else {
            console.error('Failed to save last watched episode.');
        }
    } catch (error) {
        console.error('Error saving last watched episode:', error);
    }
}

/**
 * Retrieves the last watched episode details from the server session.
 * @param {number} malAnimeId - The unique ID of the anime.
 * @returns {object|null} - The saved episode details or null if not found.
 */
async function getLastWatchedEpisode(malAnimeId) {
    try {
        const response = await fetch(`${API_BASE_URL}/get_last_watched?malAnimeId=${malAnimeId}`);
        if (response.ok) {
            const data = await response.json();
            return data.lastWatched || null;
        } else {
            console.error('Failed to retrieve last watched episode.');
            return null;
        }
    } catch (error) {
        console.error('Error retrieving last watched episode:', error);
        return null;
    }
}

/**
 * Clears the last watched episode details from the server session.
 * @param {number} malAnimeId - The unique ID of the anime.
 */
async function clearLastWatchedEpisode(malAnimeId) {
    try {
        const response = await fetch(`${API_BASE_URL}/clear_last_watched`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ malAnimeId })
        });

        if (response.ok) {
            console.log(`Last watched episode cleared for Anime ID ${malAnimeId}`);
        } else {
            console.error('Failed to clear last watched episode.');
        }
    } catch (error) {
        console.error('Error clearing last watched episode:', error);
    }
}

export async function clearAllLastWatchedEpisodes() {
    try {
        const response = await fetch('/api/clear_all_last_watched', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            console.log('All last watched episodes cleared.');
        } else {
            console.error('Failed to clear all last watched episodes.', response.error);
        }
    } catch (error) {
        console.error('Error clearing all last watched episodes:', error);
    }
}

/**
 * Downloads the specified anime episode.
 * @param {number} malAnimeId - The MAL ID of the anime.
 * @param {number} episodeNumber - The episode number.
 * @param {string} animeTitle - The title of the anime.
 */
export async function downloadAnime(malAnimeId, episodeNumber, animeTitle) { // TODO: export to different .js file
    const downloadUrl = `/download_anime/${malAnimeId}/${episodeNumber}`;

    // Create a temporary link element
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `${animeTitle}_episode_${episodeNumber}.ts`; // This may be overridden by server headers
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Plays the specified anime episode.
 * @param {number} malAnimeId - The MAL ID of the anime.
 * @param {number} episodeNumber - The episode number.
 */
export async function playAnime(malAnimeId, episodeNumber, resolution = '1080p') {
    const video = document.getElementById('video-player');
    const videoModal = document.getElementById('video-modal');
    let videoSrc =  `/watch_anime/${malAnimeId}/${episodeNumber}`;

    if (resolution) {
        videoSrc += `?resolution=${resolution}`;
    }

    // Clear all saved playback times and last watched episodes
    await clearAllLastWatchedEpisodes();

    // Save the last watched episode details
    await saveLastWatchedEpisode(malAnimeId, episodeNumber);

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

    // Before initializing a new player, destroy any existing HLS instance
    if (hlsInstance) {
        hlsInstance.destroy();
        hlsInstance = null;
        console.log('Previous HLS instance destroyed.');
    }

    try {
        const response = await fetch(videoSrc);
        if (!response.ok) {
            const errorMessage = await response.text();
            showErrorPopup(errorMessage, response.status);
            videoModal.style.display = 'none';
            throw new Error('Failed to fetch video source URL');
        }
        setupVideoPlayer(video, videoSrc, malAnimeId, episodeNumber);
        currentResolution = resolution; // Set current resolution
        await populateResolutionSelector(malAnimeId, episodeNumber, resolution);
    } catch (error) {
        console.error('Error fetching video:', error);
        showErrorPopup('An unexpected error occurred.');
        videoModal.style.display = 'none';
    }
}

// Helper Functions

/**
 * Populates the resolution selector dropdown with available options.
 * @param {number} malAnimeId - The MAL ID of the anime.
 * @param {number} episodeNumber - The episode number.
 * @param {string} selectedResolution - The currently selected resolution.
 */
async function populateResolutionSelector(malAnimeId, episodeNumber, selectedResolution) {
    const resolutionSelector = document.getElementById('resolution');
    resolutionSelector.innerHTML = '';

    try {
        const response = await fetch(`/api/get_available_resolutions/${malAnimeId}/${episodeNumber}`);
        if (response.ok) {
            const data = await response.json();
            const resolutions = data.resolutions;

            resolutions.forEach(([resStr, resUrl]) => {
                if (!Array.from(resolutionSelector.options).some(option => option.value === resStr)) {
                    const option = document.createElement('option');
                    option.value = resStr;
                    option.text = resStr;
                    if (resStr === selectedResolution) {
                        option.selected = true;
                    }
                    resolutionSelector.appendChild(option);
                }
            });


            // Add event listener for resolution changes
            resolutionSelector.addEventListener('change', async (event) => {
                const newResolution = event.target.value;
                await switchResolution(malAnimeId, episodeNumber, newResolution);
            });
        } else {
            console.error('Failed to fetch available resolutions.');
        }
    } catch (error) {
        console.error('Error fetching available resolutions:', error);
    }
}

/**
 * Switches the video to the selected resolution.
 * @param {number} malAnimeId - The MAL ID of the anime.
 * @param {number} episodeNumber - The episode number.
 * @param {string} newResolution - The new resolution to switch to.
 */
async function switchResolution(malAnimeId, episodeNumber, newResolution) {
    const video = document.getElementById('video-player');
    const currentTime = video.currentTime;
    const isPlaying = !video.paused && !video.ended;

    // Pause the current video
    video.pause();

    // Play the new resolution
    await playAnime(malAnimeId, episodeNumber, newResolution);

    // Seek to the previous time
    video.currentTime = currentTime;

    // Resume playback if it was playing before
    if (isPlaying) {
        video.play().catch(error => {
            console.error('Error resuming video:', error);
            showErrorPopup('Failed to resume video playback.');
        });
    }
}

/**
 * Sets up the video player with the provided m3u8 link.
 * @param {HTMLVideoElement} video - The video element.
 * @param {string} videoSrc - The m3u8 link.
 * @param {number} malAnimeId - The MAL ID of the anime.
 * @param {number} episodeNumber - The episode number.
 */
async function setupVideoPlayer(video, videoSrc, malAnimeId, episodeNumber) {
    if (Hls.isSupported()) {
        const hlsConfig = {
            maxBufferLength: 2.5 * 60,           // 2.5 minutes
            maxMaxBufferLength: 5 * 60,          // 5 minutes
            maxBufferSize: 1000 * 1000 * 1000,   // 1GB
            maxBufferHole: 0.5,                  // 0.5 seconds
            startPosition: -1,
            startMaxNotBuffered: 10,
        };

        hlsInstance = new Hls(hlsConfig);
        hlsInstance.loadSource(videoSrc);
        hlsInstance.attachMedia(video);

        hlsInstance.on(Hls.Events.MANIFEST_PARSED, async () => {
            // Check for saved playback time
            const savedTime = await getSavedPlaybackTime(malAnimeId, episodeNumber);
            if (savedTime !== null && savedTime > 0) {
                video.currentTime = savedTime;
                console.log(`Resuming playback at ${savedTime} seconds.`);
            }
            video.play().then(() => {
                console.log('Video playback started.');
            }).catch(error => {
                console.error('Error playing video:', error);
                showErrorPopup('Failed to start video playback.');
            });
        });

        hlsInstance.on(Hls.Events.BUFFER_FULL, () => {
            console.log('Buffer is full.');
        });

        // Handle errors
        hlsInstance.on(Hls.Events.ERROR, function (event, data) {
            console.error('HLS Error:', data);
            if (data.fatal) {
                switch (data.type) {
                    case Hls.ErrorTypes.NETWORK_ERROR:
                        console.error('Network error encountered, trying to recover...');
                        hlsInstance.startLoad();
                        break;
                    case Hls.ErrorTypes.MEDIA_ERROR:
                        console.error('Media error encountered, trying to recover...');
                        hlsInstance.recoverMediaError();
                        break;
                    default:
                        hlsInstance.destroy();
                        showErrorPopup('An unrecoverable error occurred.');
                        removeM3u8Link(malAnimeId, episodeNumber);
                        break;
                }
            }
        });

        // Event listener to save playback time periodically
        const saveInterval = 5000; // Save every 5 seconds
        let saveTimer = setInterval(async () => {
            if (!video.paused && !video.ended) {
                await savePlaybackTime(malAnimeId, episodeNumber, video.currentTime);
                console.log(`Saved playback time: ${video.currentTime} seconds.`);
            }
        }, saveInterval);

        // Clear the interval when video is paused or ended
        const clearSaveTimer = () => {
            if (saveTimer) {
                clearInterval(saveTimer);
                saveTimer = null;
            }
        };

        video.addEventListener('pause', async () => {
            clearSaveTimer();
            await savePlaybackTime(malAnimeId, episodeNumber, video.currentTime);
            console.log(`Video paused. Saved playback time: ${video.currentTime} seconds.`);
        });

        video.addEventListener('ended', async () => {
            clearSaveTimer();
            await removePlaybackTime(malAnimeId, episodeNumber);
            await clearLastWatchedEpisode(malAnimeId); // Clear last watched details
            removeM3u8Link(malAnimeId, episodeNumber); // Clear saved m3u8 link
            console.log(`Video ended. Removed saved playback time, last watched details, and m3u8 link.`);
        });

    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = videoSrc;
        video.addEventListener('loadedmetadata', async () => {
            // Check for saved playback time
            const savedTime = await getSavedPlaybackTime(malAnimeId, episodeNumber);
            if (savedTime !== null && savedTime > 0) {
                video.currentTime = savedTime;
                console.log(`Resuming playback at ${savedTime} seconds.`);
            }
            video.play().catch(error => {
                console.error('Error playing video:', error);
                showErrorPopup('Failed to start video playback.');
            });
        });

        // Event listener to save playback time periodically
        const saveInterval = 5000; // Save every 5 seconds
        let saveTimer = setInterval(async () => {
            if (!video.paused && !video.ended) {
                await savePlaybackTime(malAnimeId, episodeNumber, video.currentTime);
                console.log(`Saved playback time: ${video.currentTime} seconds.`);
            }
        }, saveInterval);

        // Clear the interval when video is paused or ended
        const clearSaveTimer = () => {
            if (saveTimer) {
                clearInterval(saveTimer);
                saveTimer = null;
            }
        };

        video.addEventListener('pause', async () => {
            clearSaveTimer();
            await savePlaybackTime(malAnimeId, episodeNumber, video.currentTime);
            console.log(`Video paused. Saved playback time: ${video.currentTime} seconds.`);
        });

        video.addEventListener('ended', async () => {
            clearSaveTimer();
            await removePlaybackTime(malAnimeId, episodeNumber);
            await clearLastWatchedEpisode(malAnimeId); // Clear last watched details
            console.log(`Video ended. Removed saved playback time and last watched details.`);
        });

    } else {
        showErrorPopup('Your browser does not support HLS streaming.');
    }
}

/**
 * Displays an error popup to the user.
 * @param {string} message - The error message to display.
 * @param {number} [status=null] - The HTTP status code (optional).
 */
function showErrorPopup(message, status = null) {
    const existingPopup = document.querySelector('.error-popup');
    if (existingPopup) {
        existingPopup.remove(); // Remove existing popup if any
    }

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


export {
    saveLastWatchedEpisode
};
