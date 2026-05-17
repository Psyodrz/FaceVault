import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Monitor, Camera, ShieldAlert, Wifi, WifiOff } from 'lucide-react';
import { getRecognizeWsUrl } from '../lib/websocket';

const LiveMonitor = () => {
  const { token } = useAuth();
  const [faces, setFaces] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [error, setError] = useState(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  const streamRef = useRef(null);
  const cameraActiveRef = useRef(false);
  const captureTimerRef = useRef(null);
  const waitingForResponse = useRef(false);

  // Keep ref in sync with state
  useEffect(() => {
    cameraActiveRef.current = cameraActive;
  }, [cameraActive]);

  useEffect(() => {
    const wsUrl = getRecognizeWsUrl();
    let reconnectTimer;
    let stopped = false;

    const connectWs = () => {
      if (stopped) return;

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('[WS] Connected:', wsUrl);
        setWsConnected(true);
        setError(null);
      };

      ws.onclose = () => {
        console.log('[WS] Disconnected');
        setWsConnected(false);
        wsRef.current = null;
        if (!stopped) {
          reconnectTimer = setTimeout(connectWs, 3000);
        }
      };

      ws.onerror = () => {
        setError('Neural stream offline — reconnecting to backend…');
      };

      ws.onmessage = (event) => {
        waitingForResponse.current = false;
        try {
          const data = JSON.parse(event.data);
          setFaces(data.faces || []);
        } catch (e) {
          console.error('WS parse error', e);
        }
      };

      wsRef.current = ws;
    };

    connectWs();

    return () => {
      stopped = true;
      clearTimeout(reconnectTimer);
      if (wsRef.current && wsRef.current.readyState <= 1) {
        wsRef.current.close();
      }
    };
  }, []);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 640, height: 480, facingMode: 'user' } 
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      streamRef.current = stream;
      setCameraActive(true);
      cameraActiveRef.current = true;

      // Start capture loop — fast, with frame-skipping
      const captureFrame = () => {
        if (!cameraActiveRef.current) return;
        
        if (!videoRef.current || !canvasRef.current || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          captureTimerRef.current = setTimeout(captureFrame, 100);
          return;
        }

        // Skip this frame if still waiting for the previous response
        if (waitingForResponse.current) {
          captureTimerRef.current = setTimeout(captureFrame, 30);
          return;
        }

        const video = videoRef.current;
        const canvas = canvasRef.current;
        
        const vw = video.videoWidth || 640;
        const vh = video.videoHeight || 480;
        canvas.width = vw;
        canvas.height = vh;
        
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0, vw, vh);
        
        canvas.toBlob((blob) => {
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && blob) {
            waitingForResponse.current = true;
            wsRef.current.send(blob);
          }
        }, 'image/jpeg', 0.5);

        // ~15 FPS target
        captureTimerRef.current = setTimeout(captureFrame, 67);
      };

      captureFrame();

    } catch (err) {
      setError("Camera access denied or unavailable.");
    }
  }, []);

  const stopCamera = useCallback(() => {
    cameraActiveRef.current = false;
    if (captureTimerRef.current) {
      clearTimeout(captureTimerRef.current);
      captureTimerRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
    setFaces([]);
    setError(null);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  // Calculate overlay positions relative to the video display size
  const getOverlayStyle = (face) => {
    if (!videoRef.current) return {};
    const video = videoRef.current;
    const displayW = video.clientWidth;
    const displayH = video.clientHeight;
    const videoW = video.videoWidth || 640;
    const videoH = video.videoHeight || 480;
    
    const scaleX = displayW / videoW;
    const scaleY = displayH / videoH;
    
    return {
      position: 'absolute',
      border: `2px solid ${face.name === 'Unknown' ? 'var(--danger)' : 'var(--success)'}`,
      left: `${face.x * scaleX}px`,
      top: `${face.y * scaleY}px`,
      width: `${face.w * scaleX}px`,
      height: `${face.h * scaleY}px`,
      pointerEvents: 'none',
      boxShadow: face.name === 'Unknown' 
        ? '0 0 8px rgba(255, 60, 60, 0.4)' 
        : '0 0 8px rgba(0, 200, 120, 0.4)',
      transition: 'all 0.05s linear'
    };
  };

  return (
    <div className="live-monitor">
      <div className="page-header">
        <div>
          <h1>Surveillance Monitor</h1>
          <p className="page-subtitle">Real-time facial intelligence and threat detection</p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div className={`badge ${wsConnected ? 'badge-green' : 'badge-red'}`}>
            {wsConnected ? <Wifi size={14} /> : <WifiOff size={14} />}
            {wsConnected ? 'Telemetry Active' : 'Offline'}
          </div>
          {cameraActive ? (
            <button className="btn btn-danger" onClick={stopCamera}>
              <Monitor size={16} /> Disable Feed
            </button>
          ) : (
            <button className="btn btn-primary" onClick={startCamera}>
              <Camera size={16} /> Enable Feed
            </button>
          )}
        </div>
      </div>

      <div className="grid-dashboard">
        {/* Main Feed */}
        <div className="glass-card" style={{ padding: 0, overflow: 'hidden', position: 'relative', minHeight: '480px', background: '#000' }}>
          <video 
            ref={videoRef} 
            autoPlay 
            playsInline 
            muted 
            style={{ width: '100%', height: '100%', objectFit: 'cover', display: cameraActive ? 'block' : 'none' }} 
          />
          <canvas ref={canvasRef} width="640" height="480" style={{ display: 'none' }} />
          
          {!cameraActive && (
            <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
              {error ? (
                <div style={{ textAlign: 'center', padding: '32px' }}>
                  <ShieldAlert size={48} color="var(--danger)" style={{ marginBottom: '16px', filter: 'drop-shadow(0 0 10px rgba(239, 68, 68, 0.4))' }} />
                  <p style={{ color: 'var(--danger)', fontWeight: '600', marginBottom: '8px' }}>HARDWARE FAULT</p>
                  <p style={{ fontSize: '0.85rem' }}>{error}</p>
                  <button className="btn btn-ghost btn-sm" style={{ marginTop: '16px' }} onClick={startCamera}>Retry Connection</button>
                </div>
              ) : (
                <>
                  <Monitor size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
                  <p>Surveillance feed offline. Awaiting activation.</p>
                </>
              )}
            </div>
          )}

          {/* Face bounding box overlays */}
          {cameraActive && faces.map((face, i) => (
            <div key={i} style={getOverlayStyle(face)}>
              <div style={{
                position: 'absolute',
                bottom: '-24px',
                left: '-2px',
                background: face.name === 'Unknown' ? 'var(--danger)' : 'var(--success)',
                color: '#fff',
                fontSize: '0.75rem',
                fontWeight: '600',
                padding: '2px 6px',
                whiteSpace: 'nowrap',
                fontFamily: 'JetBrains Mono, monospace'
              }}>
                {face.name} • {Math.round(face.confidence)}%
              </div>
            </div>
          ))}
        </div>

        {/* Telemetry Sidebar */}
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="section-header" style={{ marginBottom: 0 }}>
            <div className="section-title">
              <div className="dot"></div> Live Telemetry Log
            </div>
          </div>
          
          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {faces.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: '20px' }}>
                No signatures detected.
              </div>
            ) : (
              faces.map((face, i) => (
                <div key={i} style={{ 
                  padding: '12px', 
                  borderLeft: `3px solid ${face.name === 'Unknown' ? 'var(--danger)' : 'var(--success)'}`,
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-default)',
                  borderLeftWidth: '3px',
                  borderRadius: 'var(--radius-sm)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{face.name}</span>
                    <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      Match: {Math.round(face.confidence)}%
                    </span>
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Region: ({face.x}, {face.y}) {face.w}×{face.h}
                  </div>
                  {face.name === 'Unknown' && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--danger)', fontSize: '0.75rem', marginTop: '6px' }}>
                      <ShieldAlert size={12} /> Unauthorized Signature
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveMonitor;
