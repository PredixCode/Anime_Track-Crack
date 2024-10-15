// filters.js
import { cachedLineageData } from './data.js';
import { parseAnimeData } from './parser.js';

export function applyFilters() {
    const selectedWatchStatuses = Array.from(document.querySelectorAll('input[name="watch_status"]:checked')).map(cb => cb.value);
    const selectedAiringStatuses = Array.from(document.querySelectorAll('input[name="airing_status"]:checked')).map(cb => cb.value);

    parseAnimeData(cachedLineageData, selectedWatchStatuses, selectedAiringStatuses);
}
