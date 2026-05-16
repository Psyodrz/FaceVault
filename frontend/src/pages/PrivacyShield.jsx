import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { EyeOff, Upload, Download, ShieldCheck, Camera, AlertTriangle } from 'lucide-react';

const PrivacyShield = () => {
  const { token } = useAuth();
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [facesFound, setFacesFound] = useState(null);
  const [mode, setMode] = useState('blur');
  const [strength, setStrength] = useState(51);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      setPreview(URL.createObjectURL(file));
      setResult(null);
      setFacesFound(null);
      setError(null);
    }
  };

  const handleAnonymize = async () => {
    if (!image) return;
    setProcessing(true);
    setError(null);
    
    const formData = new FormData();
    formData.append('image', image);
    formData.append('mode', mode);
    formData.append('blur_strength', strength);

    try {
      const res = await fetch('/api/anonymize', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        setResult(`data:image/jpeg;base64,${data.image_base64}`);
        setFacesFound(data.faces_anonymized);
      } else {
        setError('Failed to process image. Please try a different file.');
      }
    } catch (err) {
      console.error("Failed to anonymize image", err);
      setError('Network error. Please check your connection.');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="privacy-shield">
      <div className="page-header">
        <div>
          <h1>Privacy Shield</h1>
          <p className="page-subtitle">GDPR-compliant face redaction protocol</p>
        </div>
        <div className="badge badge-blue">
          <ShieldCheck size={14} /> Encryption Active
        </div>
      </div>

      <div className="grid-dashboard">
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="section-header">
            <div className="section-title">Configuration</div>
          </div>
          
          <div className="input-group">
            <label className="input-label">Redaction Method</label>
            <div style={{ display: 'flex', gap: '12px' }}>
              {['blur', 'pixelate', 'solid'].map(m => (
                <button 
                  key={m}
                  className={`btn ${mode === m ? 'btn-primary' : 'btn-ghost'}`}
                  style={{ flex: 1, textTransform: 'capitalize' }}
                  onClick={() => setMode(m)}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          <div className="input-group">
            <label className="input-label">Obfuscation Strength: {strength}</label>
            <input 
              type="range" 
              min="1" max="99" step="2" 
              value={strength} 
              onChange={e => setStrength(Number(e.target.value))} 
              style={{ width: '100%', accentColor: 'var(--accent-blue)' }}
            />
          </div>

          <div style={{ marginTop: 'auto' }}>
            <label className="btn btn-ghost" style={{ width: '100%', marginBottom: '12px', cursor: 'pointer' }}>
              <Upload size={16} /> {image ? image.name : 'Select Evidence File'}
              <input type="file" accept="image/*" hidden onChange={handleImageUpload} />
            </label>

            <button 
              className="btn btn-primary" 
              style={{ width: '100%' }} 
              disabled={!image || processing}
              onClick={handleAnonymize}
            >
              {processing ? 'Processing...' : <><EyeOff size={16} /> Execute Redaction</>}
            </button>
          </div>

          {error && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '12px', background: 'rgba(218, 54, 51, 0.1)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--danger)', color: 'var(--danger)', fontSize: '0.85rem' }}>
              <AlertTriangle size={16} /> {error}
            </div>
          )}

          {facesFound !== null && (
            <div style={{ padding: '12px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              <strong style={{ color: 'var(--text-primary)' }}>{facesFound}</strong> face{facesFound !== 1 ? 's' : ''} detected and redacted using <strong style={{ color: 'var(--text-primary)' }}>{mode}</strong> method.
            </div>
          )}
        </div>

        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="section-header">
            <div className="section-title">Visual Output</div>
            {result && (
              <a href={result} download={`redacted_${Date.now()}.jpg`} className="btn btn-ghost btn-sm">
                <Download size={14} /> Save Secure Copy
              </a>
            )}
          </div>
          
          <div style={{ flex: 1, background: '#000', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)', overflow: 'hidden', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
            {!preview && !result && (
              <div style={{ color: 'var(--text-muted)', textAlign: 'center' }}>
                <Camera size={48} style={{ opacity: 0.2, margin: '0 auto 16px' }} />
                <p>Upload an image to begin redaction.</p>
              </div>
            )}
            
            {preview && !result && (
              <img src={preview} alt="Original" style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }} />
            )}

            {result && (
              <img src={result} alt="Redacted" style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PrivacyShield;
