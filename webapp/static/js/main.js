// main.js
import { fetchLineageData, fetchAnimes, cachedLineageData, refreshUserData } from './data.js';
import { parseAnimeData } from './parser.js';
import { addEventListeners, markUnavailableEpisodes } from './events.js';
import { playAnime } from './player.js';
import { initializeCountdown } from './dom.js'

window.addEventListener('DOMContentLoaded', async () => {
    await Promise.all([refreshUserData(), fetchLineageData(), fetchAnimes()]);
    loadFiltersFromLocalStorage();
    applyInitialFilters();        
    await loadAllEpisodeData(); // Newly added function
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
 * Loads all episode data from the server session and updates the UI accordingly.
 */
async function loadAllEpisodeData() {
    try {
        const response = await fetch('/api/get_all_episode_data');
        if (response.ok) {
            const data = await response.json();
            // Process and update the UI based on all available episode data
            for (const [key, value] of Object.entries(data)) {
                if (key.startsWith("available_episodes_")) {
                    const animeId = key.split("_").pop();
                    markUnavailableEpisodes(animeId, value);
                }
                // Add other data handling logic as needed
            }
        } else {
            console.error('Failed to load all episode data from server.');
        }
    } catch (error) {
        console.error('Error loading all episode data:', error);
    }
    await loadNextAiringEpisodeDate();
}

/**
 * Loads next episode airing date from the server session and updates the UI accordingly.
 */
async function loadNextAiringEpisodeDate() {
    try {
        const response = await fetch('/api/get_all_episode_data');
        if (response.ok) {
            const data = await response.json();
            // Process and update the UI based on next airing date data
            for (const [key, value] of Object.entries(data)) {
                if (key.startsWith("next_airing_")) {
                    const animeId = key.split("_")[2];
                    const episodeNumber = key.split("_")[3];
                    const nextAiringDate = value;
                    const animeElement = document.getElementById(`anime-${animeId}`);
                    if (animeElement) {
                        initializeCountdown(animeId, nextAiringDate, animeElement);
                    }
                }
            }
        } else {
            console.error('Failed to load next airing episode data from server.');
        }
    } catch (error) {
        console.error('Error loading next airing episode data:', error);
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
                            await clearLastWatchedEpisode(malAnimeId); // TODO: Implement this function!!!
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
