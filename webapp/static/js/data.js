// data.js

export let cachedAnimeData = null;
export let cachedLineageData = null;

/**
 * Refreshes the user data by fetching the latest anime list status.
 */
export async function refreshUserData() {
    await fetch('/refresh_user_list_status');
}

/**
 * Fetches lineage data from the backend.
 * @returns {Promise<object>} - The lineage data.
 */
export async function fetchLineageData() {
    if (cachedLineageData) return cachedLineageData;
    const response = await fetch('/lineage_data');
    if (!response.ok) {
        console.error('Failed to fetch lineage data:', response.statusText);
        return {};
    }
    cachedLineageData = await response.json();
    return cachedLineageData;
}

/**
 * Fetches all animes from the backend.
 * @returns {Promise<object>} - The anime data.
 */
export async function fetchAnimes() {
    if (cachedAnimeData) return cachedAnimeData;
    const response = await fetch('/animes');
    if (!response.ok) {
        console.error('Failed to fetch anime data:', response.statusText);
        return {};
    }
    cachedAnimeData = await response.json();
    return cachedAnimeData;
}

/**
 * Fetches available episodes and the next airing date for a given MAL Anime ID.
 * Utilizes Local Storage to cache the results and avoid redundant network requests.
 * @param {number} selectedMalAnimeId - The MAL Anime ID.
 * @param {number} [episodeNumber=1] - The episode number associated with the airing date.
 * @param {boolean} [onlyLocal=false] - If true, fetches data only from Local Storage.
 * @returns {Promise<object|null>} - An object containing available episodes and next airing date, or null if onlyLocal is true and no data exists.
 */
export async function checkEpisodes(selectedMalAnimeId, episodeNumber = 1, onlyLocal = false) {
    const availableEpisodesKey = `available_episodes_${selectedMalAnimeId}`;
    const availableEpisodesCached = localStorage.getItem(availableEpisodesKey);
    const availableEpisodesExpiryKey = `${availableEpisodesKey}_expiry`;
    const availableEpisodesExpiry = localStorage.getItem(availableEpisodesExpiryKey);
    
    const nextAiringKey = `next_airing_${selectedMalAnimeId}_${episodeNumber}`;
    const nextAiringCached = localStorage.getItem(nextAiringKey);
    const nextAiringExpiryKey = `${nextAiringKey}_expiry`;
    const nextAiringExpiry = localStorage.getItem(nextAiringExpiryKey);
    
    const now = Date.now();
    const AVAILABLE_CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours
    const AIRING_CACHE_DURATION = 1 * 60 * 60 * 1000; // 1 hour for airing date
    
    let availableEpisodes = null;
    let nextAiringDate = null;
    
    // Check and retrieve available episodes from cache
    if (availableEpisodesCached && availableEpisodesExpiry && now < parseInt(availableEpisodesExpiry, 10)) {
        try {
            availableEpisodes = JSON.parse(availableEpisodesCached);
            console.log(`Using cached available episodes for Anime ID ${selectedMalAnimeId}:`, availableEpisodes);
        } catch (error) {
            console.error('Error parsing cached available episodes:', error);
            // If parsing fails, proceed to fetch fresh data
            availableEpisodes = null;
        }
    }
    
    // Check and retrieve next airing date from cache
    if (nextAiringCached && nextAiringExpiry && now < parseInt(nextAiringExpiry, 10)) {
        try {
            nextAiringDate = JSON.parse(nextAiringCached);
            console.log(`Using cached next airing date for Anime ID ${selectedMalAnimeId}, Episode ${episodeNumber}:`, nextAiringDate);
        } catch (error) {
            console.error('Error parsing cached next airing date:', error);
            // If parsing fails, proceed to fetch fresh data
            nextAiringDate = null;
        }
    }
    
    // If onlyLocal is true and both data pieces are available, return them
    if (onlyLocal) {
        if (availableEpisodes && nextAiringDate) {
            return {
                availableEpisodes,
                nextAiringDate
            };
        }
        return null;
    }
    
    // If any of the data is missing or expired, fetch fresh data from the backend
    try {
        const response = await fetch(`/api/get_episode_data/${selectedMalAnimeId}/${episodeNumber}`);
        if (response.ok) {
            const data = await response.json();
            
            availableEpisodes = data.availableEpisodes || [];
            nextAiringDate = data.nextAiringDate || null;
    
            // Validate data structure
            if (!Array.isArray(availableEpisodes)) {
                throw new Error('Invalid data structure: availableEpisodes should be an array.');
            }
    
            // Store available episodes in Local Storage
            localStorage.setItem(availableEpisodesKey, JSON.stringify(availableEpisodes));
            localStorage.setItem(availableEpisodesExpiryKey, now + AVAILABLE_CACHE_DURATION);
            console.log(`Fetched and cached available episodes for Anime ID ${selectedMalAnimeId}:`, availableEpisodes);
    
            // Store next airing date in Local Storage
            if (nextAiringDate) {
                localStorage.setItem(nextAiringKey, JSON.stringify(nextAiringDate));
                localStorage.setItem(nextAiringExpiryKey, now + AIRING_CACHE_DURATION);
                console.log(`Fetched and cached next airing date for Anime ID ${selectedMalAnimeId}, Episode ${episodeNumber}:`, nextAiringDate);
            } else {
                // If no airing date is found, ensure no stale data remains
                localStorage.removeItem(nextAiringKey);
                localStorage.removeItem(nextAiringExpiryKey);
                console.log(`No next airing date found for Anime ID ${selectedMalAnimeId}, Episode ${episodeNumber}.`);
            }
    
            return {
                availableEpisodes,
                nextAiringDate
            };
        } else {
            // Attempt to parse error message from backend
            const errorData = await response.json();
            const errorMessage = errorData.error || `Failed to fetch episodes: ${response.status}`;
            throw new Error(errorMessage);
        }
    } catch (error) {
        console.error(`Error fetching episodes for Anime ID ${selectedMalAnimeId}:`, error);
        throw error; // Re-throw the error to be handled in the calling function
    }
}

/**
 * Retrieves available episodes from Local Storage.
 * @param {number} selectedMalAnimeId - The MAL Anime ID.
 * @returns {string[]|null} - Array of available episode URLs or null if not found.
 */
export function getAvailableEpisodesFromLocal(selectedMalAnimeId) {
    const availableEpisodesKey = `available_episodes_${selectedMalAnimeId}`;
    const availableEpisodesCached = localStorage.getItem(availableEpisodesKey);
    if (availableEpisodesCached) {
        try {
            const availableEpisodes = JSON.parse(availableEpisodesCached);
            return availableEpisodes;
        } catch (error) {
            console.error('Error parsing cached available episodes:', error);
            return null;
        }
    }
    return null;
}

/**
 * Retrieves the next airing date from Local Storage.
 * @param {number} selectedMalAnimeId - The MAL Anime ID.
 * @param {number} episodeNumber - The episode number associated with the airing date.
 * @returns {string|null} - ISO-formatted datetime string or null if not found.
 */
export function getNextAiringDateFromLocal(selectedMalAnimeId, episodeNumber) {
    const nextAiringKey = `next_airing_${selectedMalAnimeId}_${episodeNumber}`;
    const nextAiringCached = localStorage.getItem(nextAiringKey);
    if (nextAiringCached) {
        try {
            const nextAiringDate = JSON.parse(nextAiringCached);
            return nextAiringDate;
        } catch (error) {
            console.error('Error parsing cached next airing date:', error);
            return null;
        }
    }
    return null;
}

/**
 * Clears cached available episodes and next airing date for a given MAL Anime ID.
 * @param {number} selectedMalAnimeId - The MAL Anime ID.
 * @param {number} [episodeNumber=1] - The episode number associated with the airing date.
 */
export function clearCachedEpisodeData(selectedMalAnimeId, episodeNumber = 1) {
    const availableEpisodesKey = `available_episodes_${selectedMalAnimeId}`;
    const availableEpisodesExpiryKey = `${availableEpisodesKey}_expiry`;
    localStorage.removeItem(availableEpisodesKey);
    localStorage.removeItem(availableEpisodesExpiryKey);
    console.log(`Cleared cached available episodes for Anime ID ${selectedMalAnimeId}.`);
    
    const nextAiringKey = `next_airing_${selectedMalAnimeId}_${episodeNumber}`;
    const nextAiringExpiryKey = `${nextAiringKey}_expiry`;
    localStorage.removeItem(nextAiringKey);
    localStorage.removeItem(nextAiringExpiryKey);
    console.log(`Cleared cached next airing date for Anime ID ${selectedMalAnimeId}, Episode ${episodeNumber}.`);
}
