// utils.js
export function getAnimeTitle(animeObj) {
    let title = animeObj.alternative_titles?.en || animeObj.title;

    if (animeObj.my_list_status['score'] !== undefined && animeObj.my_list_status['score'] >= 1) {
        return title + ` (${animeObj.my_list_status['score']})`;
    }
    return title;
    
    
}

export function getWatchStatus(animeObj) {
    return animeObj.my_list_status?.status || 'not_in_list';
}

export function getAiringStatus(animeObj) {
    return animeObj.status || 'unknown';
}

export function createElement(tag, className, innerHTML = '') {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (innerHTML) element.innerHTML = innerHTML;
    return element;
}
