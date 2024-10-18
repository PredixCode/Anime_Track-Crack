// events.js
import { applyFilters } from './filters.js';
import { playAnime, downloadAnime } from './player.js';

let selectedMalAnimeId = null;
let selectedEpisodeNumber = null;
let selectedAnimeTitle = null;

export function addEventListeners() {
    // Apply filters immediately when checkboxes change
    const filterCheckboxes = document.querySelectorAll('input[name="watch_status"], input[name="airing_status"]');
    filterCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', applyFilters);
    });

    // Video Modal Close
    document.getElementById('close-modal').addEventListener('click', closeVideoModal);

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

    document.getElementById('action-modal-text').innerText = `What do you want to do with Episode ${episodeNumber}?`;
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

