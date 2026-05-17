import { getRecognizeWsUrl } from './websocket';

const WS_FAILOVER_MS = 4000;

/**
 * Live Monitor transport: WebSocket to Railway when possible,
 * otherwise HTTP via same-origin /api proxy (Vercel → Railway).
 */
export function createTelemetryTransport({ onFaces, onStatus }) {
  let stopped = false;
  let mode = 'ws';
  let ws = null;
  let reconnectTimer = null;
  let failTimer = null;
  let wsAttempts = 0;

  const setMode = (next) => {
    mode = next;
    onStatus({ connected: true, mode: next });
  };

  const sendFrameHttp = async (blob) => {
    const res = await fetch('/api/recognize/frame', {
      method: 'POST',
      body: blob,
      headers: { 'Content-Type': 'image/jpeg' },
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const data = await res.json();
    onFaces(data.faces || []);
    return true;
  };

  const sendFrame = async (blob) => {
    if (stopped) return false;
    if (mode === 'http') {
      await sendFrameHttp(blob);
      return true;
    }
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(blob);
      return true;
    }
    return false;
  };

  const startHttp = () => {
    if (stopped || mode === 'http') return;
    if (ws) {
      ws.onclose = null;
      ws.close();
      ws = null;
    }
    clearTimeout(failTimer);
    clearTimeout(reconnectTimer);
    setMode('http');
    console.log('[Telemetry] Using HTTP stream via /api/recognize/frame');
  };

  const connectWs = () => {
    if (stopped || mode === 'http') return;

    const wsUrl = getRecognizeWsUrl();
    ws = new WebSocket(wsUrl);
    let opened = false;

    failTimer = setTimeout(() => {
      if (!opened && !stopped) {
        console.warn('[Telemetry] WebSocket timeout, switching to HTTP');
        startHttp();
      }
    }, WS_FAILOVER_MS);

    ws.onopen = () => {
      opened = true;
      clearTimeout(failTimer);
      wsAttempts = 0;
      setMode('ws');
      console.log('[Telemetry] WebSocket connected:', wsUrl);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onFaces(data.faces || []);
      } catch (e) {
        console.error('Telemetry parse error', e);
      }
    };

    ws.onerror = () => {
      if (!opened && mode !== 'http') {
        onStatus({ connected: false, mode: 'ws', error: 'Connecting to neural engine…' });
      }
    };

    ws.onclose = () => {
      clearTimeout(failTimer);
      if (stopped || mode === 'http') return;

      wsAttempts += 1;
      if (wsAttempts >= 2) {
        startHttp();
        return;
      }

      onStatus({ connected: false, mode: 'ws', error: 'Reconnecting stream…' });
      reconnectTimer = setTimeout(connectWs, 3000);
    };
  };

  // Vercel cannot proxy WebSockets; Railway direct WSS often fails on some DNS networks.
  // On Vercel production, use HTTP frames via /api proxy immediately.
  const preferHttp =
    import.meta.env.VITE_TELEMETRY_HTTP === 'true' ||
    (!import.meta.env.DEV && window.location.hostname.includes('vercel.app'));

  if (preferHttp) {
    startHttp();
  } else {
    connectWs();
    onStatus({ connected: false, mode: 'ws', error: 'Establishing telemetry…' });
  }

  return {
    sendFrame,
    getMode: () => mode,
    isReady: () => mode === 'http' || ws?.readyState === WebSocket.OPEN,
    close: () => {
      stopped = true;
      clearTimeout(failTimer);
      clearTimeout(reconnectTimer);
      if (ws) {
        ws.onclose = null;
        ws.close();
      }
      onStatus({ connected: false, mode: null });
    },
  };
}
