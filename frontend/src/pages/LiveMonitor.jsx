import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Monitor, Camera, ShieldAlert, Wifi, WifiOff } from 'lucide-react';
import { createTelemetryTransport } from '../lib/telemetry';

const LiveMonitor = () => {
  const [faces, setFaces] = useState([]);
  const [telemetry, setTelemetry] = useState({ connected: false, mode: null, error: null });
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const transportRef = useRef(null);
  const streamRef = useRef(null);
  const cameraActiveRef = useRef(false);
  const captureTimerRef = useRef(null);
  const waitingForResponse = useRef(false);

  useEffect(() => {
    cameraActiveRef.current = cameraActive;
  }, [cameraActive]);

  useEffect(() => {
    const transport = createTelemetryTransport({
      onFaces: (nextFaces) => {
        waitingForResponse.current = false;
        setFaces(nextFaces);
      },
      onStatus: (status) => setTelemetry(status),
    });
    transportRef.current = transport;
    return () => transport.close();
  }, []);

  const startCamera = useCallback(async () => {
    try {
      setCameraError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' },
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      streamRef.current = stream;
      setCameraActive(true);
      cameraActiveRef.current = true;

      const captureFrame = async () => {
        if (!cameraActiveRef.current) return;

        const transport = transportRef.current;
        if (!videoRef.current || !canvasRef.current || !transport?.isReady()) {
          captureTimerRef.current = setTimeout(captureFrame, 100);
          return;
        }

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

        canvas.toBlob(async (blob) => {
          if (!blob || !cameraActiveRef.current || !transportRef.current?.isReady()) {
            captureTimerRef.current = setTimeout(captureFrame, 100);
            return;
          }

          waitingForResponse.current = true;
          try {
            const sent = await transportRef.current.sendFrame(blob);
            if (!sent) waitingForResponse.current = false;
          } catch (err) {
            waitingForResponse.current = false;
            console.error('[Telemetry] Frame send failed', err);
            setTelemetry((prev) => ({
              ...prev,
              connected: false,
              error: 'Neural stream interrupted — retrying…',
            }));
          }

          captureTimerRef.current = setTimeout(
            captureFrame,
            transportRef.current?.getMode() === 'http' ? 200 : 67
          );
        }, 'image/jpeg', 0.5);
      };

      captureFrame();
    } catch {
      setCameraError('Camera access denied or unavailable.');
    }
  }, []);

  const stopCamera = useCallback(() => {
    cameraActiveRef.current = false;
    if (captureTimerRef.current) {
      clearTimeout(captureTimerRef.current);
      captureTimerRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
    setFaces([]);
    setCameraError(null);
  }, []);

  useEffect(() => () => stopCamera(), [stopCamera]);

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
      boxShadow:
        face.name === 'Unknown'
          ? '0 0 8px rgba(255, 60, 60, 0.4)'
          : '0 0 8px rgba(0, 200, 120, 0.4)',
      transition: 'all 0.05s linear',
    };
  };

  const telemetryLabel = telemetry.connected
    ? telemetry.mode === 'http'
      ? 'Telemetry Active (HTTP)'
      : 'Telemetry Active'
    : 'Offline';

  return (
    <div className="live-monitor">
      <div className="page-header">
        <div>
          <h1>Surveillance Monitor</h1>
          <p className="page-subtitle">Real-time facial intelligence and threat detection</p>
          {telemetry.error && cameraActive && (
            <p style={{ fontSize: '0.8rem', color: 'var(--warning)', marginTop: '8px' }}>{telemetry.error}</p>
          )}
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div className={`badge ${telemetry.connected ? 'badge-green' : 'badge-red'}`}>
            {telemetry.connected ? <Wifi size={14} /> : <WifiOff size={14} />}
            {telemetryLabel}
          </div>
          {cameraActive ? (
            <button type="button" className="btn btn-danger" onClick={stopCamera}>
              <Monitor size={16} /> Disable Feed
            </button>
          ) : (
            <button type="button" className="btn btn-primary" onClick={startCamera}>
              <Camera size={16} /> Enable Feed
            </button>
          )}
        </div>
      </div>

      <div className="grid-dashboard">
        <div
          className="glass-card"
          style={{ padding: 0, overflow: 'hidden', position: 'relative', minHeight: '480px', background: '#000' }}
        >
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{ width: '100%', height: '100%', objectFit: 'cover', display: cameraActive ? 'block' : 'none' }}
          />
          <canvas ref={canvasRef} width="640" height="480" style={{ display: 'none' }} />

          {!cameraActive && (
            <div
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--text-muted)',
              }}
            >
              {cameraError ? (
                <div style={{ textAlign: 'center', padding: '32px' }}>
                  <ShieldAlert
                    size={48}
                    color="var(--danger)"
                    style={{ marginBottom: '16px', filter: 'drop-shadow(0 0 10px rgba(239, 68, 68, 0.4))' }}
                  />
                  <p style={{ color: 'var(--danger)', fontWeight: '600', marginBottom: '8px' }}>CAMERA UNAVAILABLE</p>
                  <p style={{ fontSize: '0.85rem' }}>{cameraError}</p>
                  <button type="button" className="btn btn-ghost btn-sm" style={{ marginTop: '16px' }} onClick={startCamera}>
                    Retry Camera
                  </button>
                </div>
              ) : (
                <>
                  <Monitor size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
                  <p>Surveillance feed offline. Awaiting activation.</p>
                  {!telemetry.connected && (
                    <p style={{ fontSize: '0.8rem', marginTop: '8px' }}>Connecting telemetry to backend…</p>
                  )}
                </>
              )}
            </div>
          )}

          {cameraActive &&
            faces.map((face, i) => (
              <div key={i} style={getOverlayStyle(face)}>
                <div
                  style={{
                    position: 'absolute',
                    bottom: '-24px',
                    left: '-2px',
                    background: face.name === 'Unknown' ? 'var(--danger)' : 'var(--success)',
                    color: '#fff',
                    fontSize: '0.75rem',
                    fontWeight: '600',
                    padding: '2px 6px',
                    whiteSpace: 'nowrap',
                    fontFamily: 'JetBrains Mono, monospace',
                  }}
                >
                  {face.name} • {Math.round(face.confidence)}%
                </div>
              </div>
            ))}
        </div>

        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="section-header" style={{ marginBottom: 0 }}>
            <div className="section-title">
              <div className="dot" /> Live Telemetry Log
            </div>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {faces.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: '20px' }}>
                {cameraActive && telemetry.connected
                  ? 'Scanning for facial signatures…'
                  : 'No signatures detected.'}
              </div>
            ) : (
              faces.map((face, i) => (
                <div
                  key={i}
                  style={{
                    padding: '12px',
                    borderLeft: `3px solid ${face.name === 'Unknown' ? 'var(--danger)' : 'var(--success)'}`,
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-default)',
                    borderLeftWidth: '3px',
                    borderRadius: 'var(--radius-sm)',
                  }}
                >
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
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        color: 'var(--danger)',
                        fontSize: '0.75rem',
                        marginTop: '6px',
                      }}
                    >
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