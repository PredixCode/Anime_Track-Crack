// dom.js
import { getAiringStatus, getAnimeTitle, createElement } from './utils.js';


export function buildAnimeElement(animeObj, colorClass, showActionModal) {
    const element = createElement('div', `anime-element ${colorClass}`);
    element.id = animeObj.id;

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
    const airingStatus = createElement('ul', null, `<li>Airing Status: ${getAiringStatus(animeObj).replace('_', ' ').toUpperCase()}</li>`);
    details.appendChild(watchStatus);
    details.appendChild(airingStatus);
    element.appendChild(details);

    // Episodes
    const episodeContainer = createElement('div', 'episode-container');
    const numEpisodes = animeObj.num_episodes || 12;
    const watchedEpisodes = animeObj.my_list_status?.num_episodes_watched || 0;

    for (let i = 1; i <= numEpisodes; i++) {
        const episodeButton = createElement('button', 'episode-button', `Episode ${i}`);
        if (i <= watchedEpisodes) episodeButton.classList.add('finished');
        episodeButton.dataset.malAnimeId = animeObj.id;
        episodeButton.dataset.episodeNumber = i;
        episodeButton.addEventListener('click', (e) => {
            e.stopPropagation();
            showActionModal(animeObj.id, i, getAnimeTitle(animeObj));
        });
        episodeContainer.appendChild(episodeButton);
    }

    element.appendChild(episodeContainer);

    // Toggle Episode List
    element.addEventListener('click', () => {
        element.classList.toggle('expanded');
    });

    return element;
}
