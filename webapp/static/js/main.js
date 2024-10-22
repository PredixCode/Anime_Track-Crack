// main.js
import { fetchLineageData, fetchAnimes, cachedLineageData, refreshUserData } from './data.js';
import { parseAnimeData } from './parser.js';
import { addEventListeners, markUnavailableEpisodes } from './events.js';
import { playAnime, clearLastWatchedEpisode } from './player.js';


window.addEventListener('DOMContentLoaded', async () => {
    await Promise.all([refreshUserData(), fetchLineageData(), fetchAnimes()]);
    loadFiltersFromLocalStorage();
    applyInitialFilters();        
    loadAvailableEpisodesFromLocalStorage();
    addEventListeners();
    resumeLastWatchedEpisode();
});

function applyInitialFilters() {
    const selectedWatchStatuses = getSelectedValues('watch_status');
    const selectedAiringStatuses = getSelectedValues('airing_status');

    parseAnimeData(cachedLineageData, selectedWatchStatuses, selectedAiringStatuses);
}

// Helper function to get selected checkbox values
function getSelectedValues(name) {
    return Array.from(document.querySelectorAll(`input[name="${name}"]:checked`)).map(cb => cb.value);
}

// Function to load filters from localStorage and set checkboxes
function loadFiltersFromLocalStorage() {
    const savedFilters = localStorage.getItem('selectedFilters');
    if (savedFilters) {
        const { watchStatuses, airingStatuses } = JSON.parse(savedFilters);

        // Set the watch status checkboxes
        document.querySelectorAll('input[name="watch_status"]').forEach(cb => {
            cb.checked = watchStatuses.includes(cb.value);
        });

        // Set the airing status checkboxes
        document.querySelectorAll('input[name="airing_status"]').forEach(cb => {
            cb.checked = airingStatuses.includes(cb.value);
        });
    }
}


/**
 * Loads available episodes for each anime from localStorage and updates the UI accordingly.
 */
async function loadAvailableEpisodesFromLocalStorage() {
    // Iterate through all keys in localStorage
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);

        // Check if the key matches the pattern 'available_episodes_{mal_id}'
        if (key.startsWith('available_episodes_')) {
            const animeId = key.replace('available_episodes_', '');
            const episodesJSON = localStorage.getItem(key);

            try {
                const availableEpisodes = JSON.parse(episodesJSON);

                if (Array.isArray(availableEpisodes)) {
                    // Update the UI to mark unavailable episodes based on localStorage data
                    markUnavailableEpisodes(animeId, availableEpisodes);
                }
            } catch (error) {
                console.error(`Error parsing episodes for Anime ID ${animeId}:`, error);
            }
        }
    }
}

/**
 * Resumes the last watched episode if available.
 */
function resumeLastWatchedEpisode() {
    // Iterate through all keys in localStorage to find the last watched
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);

        // Check if the key matches the pattern 'last_watched_{malAnimeId}'
        if (key.startsWith('last_watched_')) {
            const malAnimeId = key.replace('last_watched_', '');
            const lastWatched = getLastWatchedEpisode(malAnimeId);

            if (lastWatched) {
                const { episodeNumber, timestamp } = lastWatched;

                // Optionally, check how recent the last watch was
                const now = Date.now();
                const timeDiff = now - timestamp;
                const maxTimeDiff = 7 * 24 * 60 * 60 * 1000; // 7 days

                if (timeDiff <= maxTimeDiff) {
                    // Optionally, prompt the user for confirmation
                    const resume = confirm(`Do you want to resume watching "${malAnimeId}", Episode ${episodeNumber}?`);
                    if (resume) {
                        playAnime(malAnimeId, episodeNumber);
                        console.log(`Resumed last watched Anime ID ${malAnimeId}, Episode ${episodeNumber}.`);
                    } else {
                        // User chose not to resume; optionally clear the last watched
                        clearLastWatchedEpisode(malAnimeId);
                        console.log(`User chose not to resume Anime ID ${malAnimeId}, Episode ${episodeNumber}.`);
                    }
                } else {
                    clearLastWatchedEpisode(malAnimeId);
                    console.log(`Last watched Anime ID ${malAnimeId} is too old. Cleared from storage.`);
                }

                // Assuming only one last watched episode; exit the loop
                break;
            }
        }
    }
}


/**
 * Retrieves the last watched episode details from localStorage.
 * @param {string} malAnimeId - The unique ID of the anime.
 * @returns {object|null} - The saved episode details or null if not found.
 */
function getLastWatchedEpisode(malAnimeId) {
    const key = `last_watched_${malAnimeId}`;
    const data = localStorage.getItem(key);
    return data ? JSON.parse(data) : null;
}