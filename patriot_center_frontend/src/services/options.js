const BASE = process.env.REACT_APP_API_BASE || '';
export async function fetchOptions() {
  const res = await fetch(`${BASE}/meta/options`);
  if (!res.ok) throw new Error('HTTP ' + res.status);
  return res.json();
}