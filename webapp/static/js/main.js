// main.js
import { fetchLineageData, fetchAnimes, cachedLineageData } from './data.js';
import { parseAnimeData } from './parser.js';
import { addEventListeners } from './events.js';

window.addEventListener('DOMContentLoaded', async () => {
    await Promise.all([fetchLineageData(), fetchAnimes()]);
    applyInitialFilters();
    addEventListeners();
});

function applyInitialFilters() {
    const selectedWatchStatuses = Array.from(document.querySelectorAll('input[name="watch_status"]:checked')).map(cb => cb.value);
    const selectedAiringStatuses = Array.from(document.querySelectorAll('input[name="airing_status"]:checked')).map(cb => cb.value);

    parseAnimeData(cachedLineageData, selectedWatchStatuses, selectedAiringStatuses);
}
