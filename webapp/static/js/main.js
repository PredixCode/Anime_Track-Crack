// main.js
import { fetchLineageData, fetchAnimes, cachedLineageData, refreshUserData } from './data.js';
import { parseAnimeData } from './parser.js';
import { addEventListeners, markUnavailableEpisodes } from './events.js';
import { playAnime } from './player.js';

window.addEventListener('DOMContentLoaded', async () => {
    await Promise.all([refreshUserData(), fetchLineageData(), fetchAnimes()]);
    loadFiltersFromLocalStorage();
    applyInitialFilters();        
    await loadAvailableEpisodes(); // Updated function
    addEventListeners();
    await resumeLastWatchedEpisode(); // Updated function
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
 * Loads available episodes for each anime from the server session and updates the UI accordingly.
 */
async function loadAvailableEpisodes() {
    try {
        const response = await fetch('/api/get_available_episodes');
        if (response.ok) {
            const data = await response.json();
            // data should be an object with malAnimeId as keys and arrays of unavailable episodes
            for (const [animeId, availableEpisodes] of Object.entries(data.availableEpisodes)) {
                if (Array.isArray(availableEpisodes)) {
                    // Update the UI to mark unavailable episodes based on session data
                    markUnavailableEpisodes(animeId, availableEpisodes);
                }
            }
        } else {
            console.error('Failed to load available episodes from server.');
        }
    } catch (error) {
        console.error('Error loading available episodes:', error);
    }
}

/**
 * Resumes the last watched episode if available by fetching from the server session.
 */
async function resumeLastWatchedEpisode() {
    try {
        const response = await fetch('/api/get_last_watched_all');
        if (response.ok) {
            const data = await response.json();
            // data should be an object with malAnimeId as keys and lastWatched objects as values
            for (const [malAnimeId, lastWatched] of Object.entries(data.lastWatched)) {
                if (lastWatched) {
                    const { episodeNumber, timestamp } = lastWatched;

                    // Optionally, check how recent the last watch was
                    const now = Date.now();
                    const timeDiff = now - timestamp;
                    const maxTimeDiff = 7 * 24 * 60 * 60 * 1000; // 7 days

                    if (timeDiff <= maxTimeDiff) {
                        // Optionally, prompt the user for confirmation
                        const resume = confirm(`Do you want to resume watching Anime ID ${malAnimeId}, Episode ${episodeNumber}?`);
                        if (resume) {
                            await playAnime(malAnimeId, episodeNumber);
                            console.log(`Resumed last watched Anime ID ${malAnimeId}, Episode ${episodeNumber}.`);
                        } else {
                            // User chose not to resume; optionally clear the last watched
                            await clearLastWatchedEpisode(malAnimeId);
                            console.log(`User chose not to resume Anime ID ${malAnimeId}, Episode ${episodeNumber}.`);
                        }
                    } else {
                        await clearLastWatchedEpisode(malAnimeId);
                        console.log(`Last watched Anime ID ${malAnimeId} is too old. Cleared from session.`);
                    }

                    // Assuming only one last watched episode; exit the loop
                    break;
                }
            }
        } else {
            console.error('Failed to retrieve last watched episodes from server.');
        }
    } catch (error) {
        console.error('Error resuming last watched episode:', error);
    }
}
