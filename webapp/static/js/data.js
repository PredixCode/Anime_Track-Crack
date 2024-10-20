// data.js
export let cachedAnimeData = null;
export let cachedLineageData = null;

export async function refreshUserData() {
    await fetch('/refresh_user_list_status');
}

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



/**
 * Fetches available episodes for a given MAL Anime ID.
 * Utilizes Local Storage to cache the results and avoid redundant network requests.
 * @param {number} selectedMalAnimeId - The MAL Anime ID.
 * @returns {Promise<string[]>} - A promise that resolves to an array of available episode URLs.
 */
export async function checkEpisodes(selectedMalAnimeId, onlyLocal=false) {
    const storageKey = `available_episodes_${selectedMalAnimeId}`;
    const cachedData = localStorage.getItem(storageKey);
    const cacheExpiryKey = `${storageKey}_expiry`;
    const cacheExpiry = localStorage.getItem(cacheExpiryKey);
    const now = new Date().getTime();
    const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours in milliseconds

    // Check if data exists and is not expired
    if (cachedData && cacheExpiry && now < parseInt(cacheExpiry, 10)) {
        try {
            const availableEpisodes = JSON.parse(cachedData);
            console.log('Using cached available episodes:', availableEpisodes);
            return availableEpisodes;
        } catch (error) {
            console.error('Error parsing cached data:', error);
            // If parsing fails, proceed to fetch fresh data
        }
    }

    if (onlyLocal === true) {
        return null;
    }

    // If no valid cached data, fetch from backend
    try {
        const response = await fetch(`/check_available_episodes/${selectedMalAnimeId}`);
        if (response.status === 200) {
            const availableEpisodes = await response.json(); // Direct array of URLs

            if (!Array.isArray(availableEpisodes)) {
                throw new Error('Invalid data structure: expected an array of available episodes');
            }

            // Store in Local Storage
            localStorage.setItem(storageKey, JSON.stringify(availableEpisodes));
            localStorage.setItem(cacheExpiryKey, now + CACHE_DURATION); // Set expiry time

            console.log('Fetched and cached available episodes:', availableEpisodes);
            return availableEpisodes;
        } else {
            // Attempt to parse error message
            const errorData = await response.json();
            const errorMessage = errorData.error || `Failed to fetch episodes: ${response.status}`;
            throw new Error(errorMessage);
        }
    } catch (error) {
        console.error('Error in checkEpisodes:', error);
        throw error; // Re-throw the error to be handled in the calling function
    }
}