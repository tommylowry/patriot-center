export function toPlayerSlug(name) {
  if (!name) return '';
  const cleaned = name
    .trim()
    .replace(/'/g, "'")  // normalize curly apostrophes to straight
    .toLowerCase();
  return encodeURIComponent(cleaned);
}

export function displayFromSlug(slug) {
  if (!slug) return '';
  const decoded = decodeURIComponent(slug);
  return decoded.replace(/_/g, ' ');
}