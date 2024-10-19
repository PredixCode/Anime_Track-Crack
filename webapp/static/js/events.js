// events.js
import { applyFilters } from './filters.js';
import { playAnime, downloadAnime } from './player.js';
import { refreshUserData, checkEpisodes } from './data.js';

let selectedMalAnimeId = null;
let selectedEpisodeNumber = null;
let selectedAnimeTitle = null;

export async function addEventListeners() {
    // Apply filters immediately when checkboxes change
    const filterCheckboxes = document.querySelectorAll('input[name="watch_status"], input[name="airing_status"]');
    filterCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', applyFilters);
    });

    // Video Modal Close
    document.getElementById('close-video-modal').addEventListener('click', () => {
        const video = document.getElementById('video-player');
        const malAnimeId = video.dataset.malAnimeId; // Ensure you set this data attribute when playing
        const episodeNumber = video.dataset.episodeNumber;
    
        if (malAnimeId && episodeNumber) {
            saveLastWatchedEpisode(malAnimeId, episodeNumber);
        }
    
        closeVideoModal();
    });

    // Minimize Video on Scroll
    window.addEventListener('scroll', toggleVideoMinimize);

    // Action Modal Buttons
    document.getElementById('action-watch-button').addEventListener('click', () => {
        closeActionModal();
        playAnime(selectedMalAnimeId, selectedEpisodeNumber);
    });

    document.getElementById('action-download-button').addEventListener('click', () => {
        closeActionModal();
        downloadAnime(selectedMalAnimeId, selectedEpisodeNumber, selectedAnimeTitle);
    });

    // Close Action Modal
    document.getElementById('close-action-modal').addEventListener('click', closeActionModal);
}

export function showActionModal(malAnimeId, episodeNumber, animeTitle) {
    selectedMalAnimeId = malAnimeId;
    selectedEpisodeNumber = episodeNumber;
    selectedAnimeTitle = animeTitle;

    document.getElementById('action-modal-text').innerText = `What do you want to do with Episode ${episodeNumber} of ${animeTitle}?`;
    document.getElementById('action-modal').style.display = 'block';
}

function closeActionModal() {
    document.getElementById('action-modal').style.display = 'none';
}

function closeVideoModal() {
    const video = document.getElementById('video-player');
    video.pause();
    video.src = '';
    const videoModal = document.getElementById('video-modal');
    videoModal.style.display = 'none';
    videoModal.classList.remove('cinema-mode', 'minimized');

    // Remove cinema mode class from body
    document.body.classList.remove('cinema-mode-active');
}

function toggleVideoMinimize() {
    const videoModal = document.getElementById('video-modal');
    if (!videoModal || videoModal.style.display !== 'block') return;

    const scrollThreshold = 200;
    if (window.scrollY > scrollThreshold) {
        // Switch to mini-player mode
        videoModal.classList.add('minimized');
        videoModal.classList.remove('cinema-mode');

        // Remove cinema mode class from body
        document.body.classList.remove('cinema-mode-active');
    } else {
        // Switch to cinema mode
        videoModal.classList.add('cinema-mode');
        videoModal.classList.remove('minimized');

        // Add cinema mode class to body
        document.body.classList.add('cinema-mode-active');
    }
}

/**
 * Marks unavailable episodes by adding the 'unavailable' class.
 * Extracts episode numbers from the availableEpisodes URLs.
 * @param {number} malAnimeId - The MAL Anime ID.
 * @param {string[]} availableEpisodes - Array of available episode URLs.
 */
export function markUnavailableEpisodes(malAnimeId, availableEpisodes) {
    if (!Array.isArray(availableEpisodes)) {
        console.error('availableEpisodes is not an array:', availableEpisodes);
        return;
    }

    // Extract episode numbers from URLs
    const availableEpisodeNumbers = availableEpisodes.map(url => {
        try {
            const urlObj = new URL(url);
            const params = new URLSearchParams(urlObj.search);
            const n = params.get('n');
            return parseInt(n, 10);
        } catch (error) {
            console.error('Error parsing URL:', url, error);
            return null;
        }
    }).filter(n => Number.isInteger(n));

    const availableSet = new Set(availableEpisodeNumbers);

    // Select all episode buttons for the given MAL Anime ID
    const episodeButtons = document.querySelectorAll(`.episode-button[data-mal-anime-id="${malAnimeId}"]`);

    episodeButtons.forEach(button => {
        const episodeNumber = parseInt(button.dataset.episodeNumber, 10);

        // If the episode is not in the availableEpisodes array and not finished, mark as unavailable
        const isFinished = button.classList.contains('finished');
        const isAvailable = availableSet.has(episodeNumber);

        if (!isAvailable && !isFinished) {
            button.classList.add('unavailable');
            button.disabled = true; // Disable the button to prevent clicks
            button.title = 'Episode Unavailable'; // Optional tooltip
        } else {
            button.classList.remove('unavailable');
            button.disabled = false;
            button.title = ''; // Remove tooltip if any
        }
    });
}

/**
 * Displays an error popup to the user.
 * @param {string} message - The error message to display.
 */
export function showErrorPopup(message) {
    const existingPopup = document.querySelector('.error-popup');
    if (existingPopup) {
        existingPopup.remove(); // Remove existing popup if any
    }

    const popup = document.createElement('div');
    popup.classList.add('error-popup');
    popup.innerText = message;

    document.body.appendChild(popup);

    // Remove the popup after 5 seconds
    setTimeout(() => {
        popup.remove();
    }, 5000);
}