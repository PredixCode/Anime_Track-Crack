// utils.js
export function getAnimeTitle(animeObj) {
    return animeObj.alternative_titles?.en || animeObj.title;
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
