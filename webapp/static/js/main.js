// main.js
import { fetchLineageData, fetchAnimes, cachedLineageData, refreshUserData } from './data.js';
import { parseAnimeData } from './parser.js';
import { addEventListeners, markUnavailableEpisodes } from './events.js';

window.addEventListener('DOMContentLoaded', async () => {
    await Promise.all([fetchLineageData(), fetchAnimes()]);
    await refreshUserData();
    loadFiltersFromLocalStorage(); // Load saved filters
    applyInitialFilters();         // Apply filters after loading them
    loadAvailableEpisodesFromLocalStorage();
    addEventListeners();
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
                    console.log(`Loaded available episodes for Anime ID ${animeId} from localStorage.`);
                }
            } catch (error) {
                console.error(`Error parsing episodes for Anime ID ${animeId}:`, error);
            }
        }
    }
}