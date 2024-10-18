// filters.js
import { cachedLineageData } from './data.js';
import { parseAnimeData } from './parser.js';

export function applyFilters() {
    const selectedWatchStatuses = getSelectedValues('watch_status');
    const selectedAiringStatuses = getSelectedValues('airing_status');

    // Save selected filters to localStorage
    saveFiltersToLocalStorage(selectedWatchStatuses, selectedAiringStatuses);

    parseAnimeData(cachedLineageData, selectedWatchStatuses, selectedAiringStatuses);
}

// Helper function to get selected checkbox values
function getSelectedValues(name) {
    return Array.from(document.querySelectorAll(`input[name="${name}"]:checked`)).map(cb => cb.value);
}

// Function to save filters to localStorage
function saveFiltersToLocalStorage(watchStatuses, airingStatuses) {
    const filters = {
        watchStatuses,
        airingStatuses
    };
    localStorage.setItem('selectedFilters', JSON.stringify(filters));
}
