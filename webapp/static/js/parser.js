// parser.js
import { cachedAnimeData } from './data.js';
import { buildAnimeElement } from './dom.js';;
import { getWatchStatus, getAiringStatus } from './utils.js';

export function parseAnimeData(lineageData, selectedWatchStatuses, selectedAiringStatuses) {
    const lineageContainer = document.getElementById('lineage');
    lineageContainer.innerHTML = ''; // Clear existing content

    for (const lineage of Object.values(lineageData)) {
        const lineageDiv = document.createElement('div');
        lineageDiv.className = 'anime-lineage';

        let hasAnime = false; // Flag to check if any anime were added to this lineage

        lineage.forEach((animeId) => {
            const animeObj = cachedAnimeData[animeId];

            const watchStatus = getWatchStatus(animeObj);
            const airingStatus = getAiringStatus(animeObj);

            if (!selectedWatchStatuses.includes(watchStatus) || !selectedAiringStatuses.includes(airingStatus)) {
                return;
            }

            const colorClass = getColorClass(watchStatus);
            const animeElement = buildAnimeElement(animeObj, colorClass);
            lineageDiv.appendChild(animeElement);
            hasAnime = true; // Mark that this lineage has at least one anime
        });

        if (hasAnime) {
            lineageContainer.appendChild(lineageDiv);
        }
    }
}

function getColorClass(watchStatus) {
    switch (watchStatus) {
        case 'completed':
            return 'anime-green';
        case 'watching':
            return 'anime-yellow';
        case 'plan_to_watch':
            return 'anime-orange';
        default:
            return 'anime-red';
    }
}
