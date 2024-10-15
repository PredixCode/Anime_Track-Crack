// parser.js
import { cachedAnimeData } from './data.js';
import { buildAnimeElement } from './dom.js';
import { showActionModal } from './events.js';
import { getWatchStatus, getAiringStatus } from './utils.js';

export function parseAnimeData(lineageData, selectedWatchStatuses, selectedAiringStatuses) {
    const lineageContainer = document.getElementById('lineage');
    lineageContainer.innerHTML = ''; // Clear existing content

    for (const lineage of Object.values(lineageData)) {
        const lineageDiv = document.createElement('div');
        lineageDiv.className = 'anime-lineage';

        lineage.forEach((animeId) => {
            const animeObj = cachedAnimeData[animeId];

            const watchStatus = getWatchStatus(animeObj);
            const airingStatus = getAiringStatus(animeObj);

            if (!selectedWatchStatuses.includes(watchStatus) || !selectedAiringStatuses.includes(airingStatus)) {
                return;
            }

            const colorClass = getColorClass(watchStatus);
            const animeElement = buildAnimeElement(animeObj, colorClass, showActionModal);
            lineageDiv.appendChild(animeElement);
        });

        lineageContainer.appendChild(lineageDiv);
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
