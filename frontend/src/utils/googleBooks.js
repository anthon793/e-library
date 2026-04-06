function looksLikeVolumeId(value) {
  return /^[A-Za-z0-9._-]{6,}$/.test(value);
}

function extractVolumeIdFromString(input) {
  const raw = String(input || '').trim();
  if (!raw) return '';

  if (raw.includes('/volumes/')) {
    const match = raw.match(/\/volumes\/([A-Za-z0-9._-]+)/i);
    if (match?.[1]) return match[1];
  }

  if (raw.startsWith('/volumes/')) {
    const id = raw.replace('/volumes/', '').split(/[/?#]/)[0];
    if (id) return id;
  }

  if (raw.includes(':') && !raw.includes('://')) {
    const tail = raw.split(':').pop()?.trim() || '';
    if (looksLikeVolumeId(tail) && !tail.toUpperCase().startsWith('ISBN')) {
      return tail;
    }
  }

  try {
    const parsed = new URL(raw);
    const idParam = parsed.searchParams.get('id') || parsed.searchParams.get('vid');
    if (idParam) return idParam;

    const pathMatch = parsed.pathname.match(/\/volumes\/([A-Za-z0-9._-]+)/i);
    if (pathMatch?.[1]) return pathMatch[1];
  } catch {
    const paramMatch = raw.match(/[?&](?:id|vid)=([^&#]+)/i);
    if (paramMatch?.[1]) return decodeURIComponent(paramMatch[1]);

    const pathMatch = raw.match(/\/volumes\/([A-Za-z0-9._-]+)/i);
    if (pathMatch?.[1]) return pathMatch[1];
  }

  if (looksLikeVolumeId(raw) && !raw.toUpperCase().startsWith('ISBN')) {
    return raw;
  }

  return '';
}

export function extractGoogleBooksVolumeId(book) {
  if (!book) return '';

  const direct = [
    book.volumeId,
    book.volume_id,
    book.google_volume_id,
  ];

  for (const candidate of direct) {
    const id = extractVolumeIdFromString(candidate);
    if (id) return id;
  }

  const links = [
    book.api_id,
    book.viewer_link,
    book.preview_link,
    book.download_link,
    book.view_link,
    book.info_link,
    book.canonical_link,
  ];

  for (const candidate of links) {
    const id = extractVolumeIdFromString(candidate);
    if (id) return id;
  }

  return '';
}
