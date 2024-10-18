// data.js
export let cachedAnimeData = null;
export let cachedLineageData = null;

export async function fetchLineageData() {
    if (cachedLineageData) return cachedLineageData;
    const response = await fetch('/lineage_data');
    cachedLineageData = await response.json();
    return cachedLineageData;
}

export async function fetchAnimes() {
    if (cachedAnimeData) return cachedAnimeData;
    const response = await fetch('/animes');
    cachedAnimeData = await response.json();
    return cachedAnimeData;
}

export async function refreshUserData() {
    await fetch('/refresh_user_list_status');
    console.log('refreshed MAL user list data, 1 API call made')
}
