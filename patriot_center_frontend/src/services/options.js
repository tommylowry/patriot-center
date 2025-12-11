import { apiGet } from '../config/api';

export async function fetchOptions() {
  return apiGet('/valid_options');
}

export async function fetchValidOptions(year = null, week = null, manager = null, player = null, position = null) {
  const parts = [];
  if (year) parts.push(String(year));
  if (week) parts.push(String(week));
  if (manager) parts.push(encodeURIComponent(String(manager)));
  if (player) parts.push(encodeURIComponent(String(player)));
  if (position && position !== 'ALL') parts.push(String(position));

  const path = parts.length > 0
    ? `/valid_options/${parts.join('/')}`
    : '/valid_options';

  return apiGet(path);
}