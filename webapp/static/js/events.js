// events.js
import { refreshUserData } from './data.js';
import { applyFilters } from './filters.js';
import { playAnime, downloadAnime } from './player.js';

let selectedMalAnimeId = null;
let selectedEpisodeNumber = null;
let selectedAnimeTitle = null;

export function addEventListeners() {
    document.getElementById('refresh-button').addEventListener('click', async () => {
        await refreshUserData();
        applyFilters();
    });

    document.getElementById('apply-filters-button').addEventListener('click', applyFilters);

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
    videoModal.classList.remove('cinema-mode', 'minimized'); // Remove classes when closing
}

function toggleVideoMinimize() {
    const videoModal = document.getElementById('video-modal');
    if (!videoModal || videoModal.style.display !== 'block') return;

    const scrollThreshold = 200;
    if (window.scrollY > scrollThreshold) {
        // Switch to mini-player mode
        videoModal.classList.add('minimized');
        videoModal.classList.remove('cinema-mode');
    } else {
        // Switch to cinema mode
        videoModal.classList.add('cinema-mode');
        videoModal.classList.remove('minimized');
    }
}
