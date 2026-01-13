import { apiGet } from '../config/api';

export async function fetchOptions() {
  return apiGet('/dynamic_filtering');
}

export async function fetchValidOptions(year = null, week = null, manager = null, player = null, position = null) {
  const params = new URLSearchParams();

  if (year) params.append('yr', String(year));
  if (week) params.append('wk', String(week));
  if (manager) params.append('mgr', String(manager));
  if (player) params.append('plyr', String(player));
  if (position && position !== 'ALL') params.append('pos', String(position));

  const queryString = params.toString();
  const path = queryString ? `/dynamic_filtering?${queryString}` : '/dynamic_filtering';

  return apiGet(path);
}