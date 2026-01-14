import { apiGet } from '../config/api';

/**
 * Fetches valid filtering options from the API.
 *
 * @returns {Promise<Object>} A promise that resolves to an object containing valid filtering options.
 */
export async function fetchOptions() {
  return apiGet('/dynamic_filtering');
}

/**
 * Fetches valid filtering options from the API based on the provided parameters.
 *
 * @param {string|number|null} year - The year of the data to filter.
 * @param {string|number|null} week - The week of the data to filter.
 * @param {string|null} manager - The manager of the data to filter.
 * @param {string|null} player - The player of the data to filter.
 * @param {string|null} position - The position of the data to filter.
 * @returns {Promise<Object>} A promise that resolves to an object containing valid filtering options.
 */
export async function fetchDynamicFiltering(year = null, week = null, manager = null, player = null, position = null) {
  // Construct the query string
  const params = new URLSearchParams();

  // Append the year if provided
  if (year) params.append('yr', String(year));

  // Append the week if provided
  if (week) params.append('wk', String(week));

  // Append the manager if provided
  if (manager) params.append('mgr', String(manager));

  // Append the player if provided
  if (player) params.append('plyr', String(player));

  // Append the position if provided and not equal to 'ALL'
  if (position && position !== 'ALL') params.append('pos', String(position));

  // Construct the path
  const queryString = params.toString();
  const path = queryString ? `/dynamic_filtering?${queryString}` : '/dynamic_filtering';

  // Fetch the data
  return apiGet(path);
}