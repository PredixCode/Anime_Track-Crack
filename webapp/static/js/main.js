// main.js
import { fetchLineageData, fetchAnimes, cachedLineageData, refreshUserData } from './data.js';
import { parseAnimeData } from './parser.js';
import { addEventListeners } from './events.js';

window.addEventListener('DOMContentLoaded', async () => {
    await Promise.all([fetchLineageData(), fetchAnimes()]);
    await refreshUserData();
    loadFiltersFromLocalStorage(); // Load saved filters
    applyInitialFilters();         // Apply filters after loading them
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
