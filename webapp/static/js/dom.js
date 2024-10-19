// dom.js
import { getAiringStatus, getAnimeTitle, createElement } from './utils.js';
import { checkEpisodes } from './data.js'; // Ensure checkEpisodes is imported
import { markUnavailableEpisodes, showErrorPopup } from './events.js'; // Ensure these functions are imported

export function buildAnimeElement(animeObj, colorClass, showActionModal) {
    const element = createElement('div', `anime-element ${colorClass}`);
    element.id = `anime-${animeObj.id}`; // Prefix to ensure uniqueness if needed

    // Anime Image
    const animeImage = createElement('img');
    animeImage.src = animeObj.main_picture.large;
    animeImage.alt = `Cover image of ${animeObj.title}`;
    element.appendChild(animeImage);

    // Title
    const title = createElement('h3');
    const titleLink = createElement('a', null, getAnimeTitle(animeObj));
    titleLink.href = animeObj.mal_url;
    title.appendChild(titleLink);
    element.appendChild(title);

    // Details
    const details = createElement('div', 'anime-details');
    const watchStatus = createElement('ul', null, `<li>User Status: ${animeObj.my_list_status?.status?.replace('_', ' ').toUpperCase() || 'None'}</li>`);

    let airingStatus_text = '';
    if (getAiringStatus(animeObj) === 'finished_airing') {
        airingStatus_text = `<li>Airing Status: ${animeObj.status.replace('_', ' ').toUpperCase() + ' in ' + animeObj.start_season['year'] + ', ' + animeObj.start_season['season'].toUpperCase()}</li>`;
    } else {
        airingStatus_text = `<li>Airing Status: ${getAiringStatus(animeObj).replace('_', ' ').toUpperCase()}</li>`;
    }
    const airingStatus = createElement('ul', null, airingStatus_text);

    details.appendChild(watchStatus);
    details.appendChild(airingStatus);
    element.appendChild(details);

    // Episodes
    const episodeContainer = createElement('div', 'episode-container');
    const numEpisodes = animeObj.num_episodes || 12;
    const watchedEpisodes = animeObj.my_list_status?.num_episodes_watched || 0;

    for (let i = 1; i <= numEpisodes; i++) {
        let epButtonText =  `Ep ${i}`;
        if (i <= 9) {
            epButtonText =  `Ep 0${i}`;
        }

        const episodeButton = createElement('button', 'episode-button', epButtonText);

        if (i <= watchedEpisodes) episodeButton.classList.add('finished');
        episodeButton.dataset.malAnimeId = animeObj.id;
        episodeButton.dataset.episodeNumber = i;
        episodeButton.addEventListener('click', (e) => {
            e.stopPropagation();
            showActionModal(animeObj.id, i, getAnimeTitle(animeObj));
        });
        episodeContainer.appendChild(episodeButton);
    }

    if (animeObj.status !== 'finished_airing') {
        // Refresh Available Episodes Button
        let availableEpisodeRefreshButton = createElement('button', 'episode-button refresh-episodes-button', 'Refresh Available Episodes');
        // Assign a data attribute to store the animeId
        availableEpisodeRefreshButton.dataset.animeId = animeObj.id;

        // Attach event listener to the refresh button
        availableEpisodeRefreshButton.addEventListener('click', async (e) => {
            e.stopPropagation(); // Prevent triggering parent click events if any

            const animeId = e.currentTarget.dataset.animeId;
            try {
                // Optional: Provide user feedback (e.g., loading spinner)
                availableEpisodeRefreshButton.disabled = true;
                availableEpisodeRefreshButton.textContent = 'Refreshing...';

                // Fetch available episodes (from backend and cache)
                const episodes_available = await checkEpisodes(animeId);
                markUnavailableEpisodes(animeId, episodes_available);

                // Restore button state
                availableEpisodeRefreshButton.disabled = false;
                availableEpisodeRefreshButton.textContent = 'Refresh Available Episodes';
            } catch (error) {
                console.error('Error fetching episodes:', error);
                showErrorPopup('Could not fetch available episodes for anime: ' + animeId);

                // Restore button state even if there's an error
                availableEpisodeRefreshButton.disabled = false;
                availableEpisodeRefreshButton.textContent = 'Refresh Available Episodes';
            }
        });

        episodeContainer.appendChild(availableEpisodeRefreshButton);
    }
    
    element.appendChild(episodeContainer);

    // Toggle Episode List
    element.addEventListener('click', () => {
        element.classList.toggle('expanded');
    });

    return element;
}
