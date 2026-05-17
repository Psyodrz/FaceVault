const DEFAULT_WS_BASE = 'https://facevault-production-04a2.up.railway.app';

/** Production API host (Railway). Override with VITE_WS_BASE_URL in Vercel if the domain changes. */
export function getWsBaseUrl() {
  const fromEnv = import.meta.env.VITE_WS_BASE_URL?.trim();
  if (fromEnv) return fromEnv.replace(/\/$/, '');

  const { hostname, protocol } = window.location;
  const isLocal =
    hostname === 'localhost' ||
    hostname === '127.0.0.1' ||
    hostname.endsWith('.local');

  if (isLocal) {
    return `${protocol}//${window.location.host}`;
  }

  return DEFAULT_WS_BASE;
}

export function getRecognizeWsUrl() {
  const base = getWsBaseUrl();
  const wsProtocol = base.startsWith('https') ? 'wss' : base.startsWith('http') ? 'ws' : 'wss';
  const host = base.replace(/^https?:\/\//, '');
  return `${wsProtocol}://${host}/ws/recognize`;
}
