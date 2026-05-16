import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Users, Search, Plus, Trash2, Camera, UserCheck, X, Upload, CameraOff, ImagePlus, UserPlus } from 'lucide-react';

const Personnel = () => {
  const { token, user } = useAuth();
  const [people, setPeople] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [selectedPerson, setSelectedPerson] = useState(null);

  const isSuperAdmin = user?.role === 'super_admin';

  useEffect(() => {
    fetchPeople();
  }, [token]);

  const fetchPeople = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/people', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPeople(data);
      }
    } catch (err) {
      console.error("Failed to fetch personnel", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to remove this personnel record? This will delete all face vectors for this person.")) return;
    
    try {
      const res = await fetch(`/api/people/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        fetchPeople();
      }
    } catch (err) {
      console.error("Failed to delete person", err);
    }
  };

  const filteredPeople = people.filter(p => p.name.toLowerCase().includes(searchTerm.toLowerCase()));

  return (
    <div className="personnel">
      <div className="page-header">
        <div>
          <h1>Personnel Registry</h1>
          <p className="page-subtitle">Manage enrolled identities and facial dataset volume</p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <div className="search-bar">
            <Search size={16} />
            <input 
              type="text" 
              placeholder="Search by name..." 
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
            />
          </div>
          <button className="btn btn-primary" onClick={() => setShowEnrollModal(true)}>
            <UserPlus size={16} /> Enroll New
          </button>
        </div>
      </div>

      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Profile</th>
              <th>Name</th>
              <th>System ID</th>
              <th>Dataset Volume</th>
              <th>Last Recognized</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="7" style={{ textAlign: 'center', padding: '32px' }}>Loading registry data...</td></tr>
            ) : filteredPeople.length === 0 ? (
              <tr><td colSpan="7" style={{ textAlign: 'center', padding: '32px' }}>No personnel records found. Start by enrolling yourself.</td></tr>
            ) : (
              filteredPeople.map(person => (
                <tr key={person.id}>
                  <td>
                    <div style={{ width: '40px', height: '40px', borderRadius: '6px', background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {person.thumbnail ? (
                         <img src={`data:image/jpeg;base64,${person.thumbnail}`} alt={person.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                      ) : (
                        <UserCheck size={20} color="var(--text-muted)" style={{ margin: 'auto' }} />
                      )}
                    </div>
                  </td>
                  <td style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{person.name}</td>
                  <td className="mono" style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>SID-{person.label_id.toString().padStart(4, '0')}</td>
                  <td>
                    <button 
                      className="btn btn-ghost btn-sm" 
                      style={{ padding: '4px 8px', fontSize: '0.75rem', height: 'auto' }}
                      onClick={() => setSelectedPerson(person)}
                      title="Add more photos to enrich recognition"
                    >
                      <ImagePlus size={14} style={{ marginRight: '6px' }} />
                      {person.image_count} vectors
                    </button>
                  </td>
                  <td className="mono" style={{ fontSize: '0.8rem' }}>
                    {person.last_seen ? new Date(person.last_seen).toLocaleString() : 'Never'}
                  </td>
                  <td>
                    <span className="badge badge-green">Active</span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button className="icon-btn" onClick={() => setSelectedPerson(person)} title="Enrich Data">
                        <ImagePlus size={16} />
                      </button>
                      {isSuperAdmin && (
                        <button className="icon-btn" onClick={() => handleDelete(person.id)} style={{ color: 'var(--danger)' }} title="Revoke Access">
                          <Trash2 size={16} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showEnrollModal && (
        <EnrollModal 
          token={token}
          onClose={() => setShowEnrollModal(false)} 
          onSuccess={() => { setShowEnrollModal(false); fetchPeople(); }} 
        />
      )}

      {selectedPerson && (
        <ManagePhotosModal
          token={token}
          person={selectedPerson}
          onClose={() => setSelectedPerson(null)}
          onSuccess={() => { setSelectedPerson(null); fetchPeople(); }}
        />
      )}
    </div>
  );
};


/* ─── Manage Photos Modal (Enrichment) ────────────────────────── */

const ManagePhotosModal = ({ token, person, onClose, onSuccess }) => {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');

  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    setUploadedFiles(prev => [...prev, ...files]);
  };

  const removeFile = (index) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpdate = async () => {
    if (uploadedFiles.length === 0) return;
    setProcessing(true);
    setError('');

    try {
      const formData = new FormData();
      for (const file of uploadedFiles) {
        formData.append('images', file);
      }

      const res = await fetch(`/api/people/${person.id}/photos`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });

      if (res.ok) {
        onSuccess();
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || 'Failed to update photos');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '20px'
    }} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="glass-card" style={{ width: '100%', maxWidth: '500px', padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h2 style={{ color: 'var(--text-primary)', margin: 0, fontSize: '1.2rem' }}>Enrich Dataset: {person.name}</h2>
            <p style={{ color: 'var(--text-secondary)', margin: '4px 0 0', fontSize: '0.8rem' }}>
              Current volume: {person.image_count} vectors
            </p>
          </div>
          <button className="icon-btn" onClick={onClose}><X size={20} /></button>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            Add more photos to improve recognition accuracy across different lighting, ages, or accessories (glasses, hats).
          </p>
          
          <label style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
            padding: '24px', border: '2px dashed var(--border-default)',
            borderRadius: 'var(--radius-sm)', cursor: 'pointer',
            color: 'var(--text-muted)', fontSize: '0.85rem',
            transition: 'all 0.2s'
          }}>
            <Upload size={20} />
            <span>Click to upload new face samples</span>
            <input type="file" multiple accept="image/*" onChange={handleFileUpload} style={{ display: 'none' }} />
          </label>

          {uploadedFiles.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '16px' }}>
              {uploadedFiles.map((f, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: '6px',
                  background: 'var(--bg-elevated)', border: '1px solid var(--border-default)',
                  borderRadius: '4px', padding: '4px 8px', fontSize: '0.75rem',
                  color: 'var(--text-secondary)'
                }}>
                  <span style={{ maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</span>
                  <button onClick={() => removeFile(i)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 0 }}>
                    <X size={12} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {error && (
          <div style={{ padding: '10px', background: 'rgba(255,60,60,0.1)', border: '1px solid var(--danger)', borderRadius: '6px', color: 'var(--danger)', fontSize: '0.85rem', marginBottom: '16px' }}>
            {error}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button className="btn btn-ghost" onClick={onClose} disabled={processing}>Cancel</button>
          <button 
            className="btn btn-primary" 
            onClick={handleUpdate} 
            disabled={processing || uploadedFiles.length === 0}
          >
            {processing ? 'Updating...' : `Add ${uploadedFiles.length} Photos`}
          </button>
        </div>
      </div>
    </div>
  );
};


/* ─── Enrollment Modal ────────────────────────────────────── */

const EnrollModal = ({ token, onClose, onSuccess }) => {
  const [name, setName] = useState('');
  const [snapshots, setSnapshots] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [cameraActive, setCameraActive] = useState(false);
  const [enrolling, setEnrolling] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

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
    } catch (err) {
      setError("Camera access denied or unavailable.");
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
  }, []);

  const captureSnapshot = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const video = videoRef.current;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
    setSnapshots(prev => [...prev, dataUrl]);
  }, []);

  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    setUploadedFiles(prev => [...prev, ...files]);
  };

  const removeSnapshot = (index) => {
    setSnapshots(prev => prev.filter((_, i) => i !== index));
  };

  const removeFile = (index) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const dataUrlToBlob = (dataUrl) => {
    const parts = dataUrl.split(',');
    const mime = parts[0].match(/:(.*?);/)?.[1] || 'image/jpeg';
    const byteStr = atob(parts[1]);
    const ab = new ArrayBuffer(byteStr.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteStr.length; i++) {
      ia[i] = byteStr.charCodeAt(i);
    }
    return new Blob([ab], { type: mime });
  };

  const handleEnroll = async () => {
    setError('');
    setSuccess('');
    
    if (!name.trim()) {
      setError('Name is required');
      return;
    }
    if (snapshots.length === 0 && uploadedFiles.length === 0) {
      setError('Please capture at least one photo or upload images');
      return;
    }

    setEnrolling(true);
    try {
      const formData = new FormData();
      formData.append('name', name.trim());
      
      snapshots.forEach((snap, i) => {
        const blob = dataUrlToBlob(snap);
        formData.append('images', blob, `webcam_${i + 1}.jpg`);
      });
      
      for (const file of uploadedFiles) {
        formData.append('images', file);
      }

      const res = await fetch('/api/people', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setSuccess(`Successfully enrolled "${data.person.name}" with ${data.person.image_count} face vectors.`);
        stopCamera();
        setTimeout(() => onSuccess(), 1500);
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || 'Enrollment failed');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setEnrolling(false);
    }
  };

  useEffect(() => {
    return () => stopCamera();
  }, [stopCamera]);

  const totalImages = snapshots.length + uploadedFiles.length;

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '20px'
    }} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="glass-card" style={{ width: '100%', maxWidth: '700px', maxHeight: '90vh', overflow: 'auto', padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h2 style={{ color: 'var(--text-primary)', margin: 0, fontSize: '1.25rem' }}>Enroll New Personnel</h2>
            <p style={{ color: 'var(--text-secondary)', margin: '4px 0 0', fontSize: '0.85rem' }}>
              Capture face data for recognition enrollment
            </p>
          </div>
          <button className="icon-btn" onClick={onClose}><X size={20} /></button>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label className="input-label">Full Name</label>
          <input
            type="text"
            className="input"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="Enter personnel name..."
          />
        </div>

        <div style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <label className="input-label">Webcam Capture ({snapshots.length} captured)</label>
            <div style={{ display: 'flex', gap: '8px' }}>
              {!cameraActive ? (
                <button className="btn btn-ghost btn-sm" onClick={startCamera}>
                  <Camera size={14} /> Start Camera
                </button>
              ) : (
                <>
                  <button className="btn btn-primary btn-sm" onClick={captureSnapshot}>
                    <Camera size={14} /> Capture
                  </button>
                  <button className="btn btn-ghost btn-sm" onClick={stopCamera}>
                    <CameraOff size={14} /> Stop
                  </button>
                </>
              )}
            </div>
          </div>
          
          {cameraActive && (
            <div style={{ position: 'relative', background: '#000', borderRadius: 'var(--radius-sm)', overflow: 'hidden', marginBottom: '8px' }}>
              <video ref={videoRef} autoPlay playsInline muted style={{ width: '100%', maxHeight: '300px', objectFit: 'cover' }} />
              <canvas ref={canvasRef} style={{ display: 'none' }} />
            </div>
          )}

          {snapshots.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '8px' }}>
              {snapshots.map((snap, i) => (
                <div key={i} style={{ position: 'relative', width: '64px', height: '64px', borderRadius: '6px', overflow: 'hidden', border: '1px solid var(--border-default)' }}>
                  <img src={snap} alt={`snap ${i + 1}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  <button onClick={() => removeSnapshot(i)} style={{
                    position: 'absolute', top: '2px', right: '2px',
                    background: 'rgba(0,0,0,0.6)', border: 'none', borderRadius: '50%',
                    width: '18px', height: '18px', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    cursor: 'pointer', color: '#fff', padding: 0
                  }}><X size={10} /></button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label className="input-label">Or Upload Images ({uploadedFiles.length} selected)</label>
          <label style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
            padding: '16px', border: '2px dashed var(--border-default)',
            borderRadius: 'var(--radius-sm)', cursor: 'pointer',
            color: 'var(--text-muted)', fontSize: '0.85rem'
          }}>
            <Upload size={16} />
            <span>Click to upload face images</span>
            <input type="file" multiple accept="image/*" onChange={handleFileUpload} style={{ display: 'none' }} />
          </label>
        </div>

        {error && <div style={{ padding: '10px', background: 'rgba(255,60,60,0.1)', border: '1px solid var(--danger)', borderRadius: '6px', color: 'var(--danger)', fontSize: '0.85rem', marginBottom: '16px' }}>{error}</div>}
        {success && <div style={{ padding: '10px', background: 'rgba(0,200,120,0.1)', border: '1px solid var(--success)', borderRadius: '6px', color: 'var(--success)', fontSize: '0.85rem', marginBottom: '16px' }}>{success}</div>}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button className="btn btn-ghost" onClick={onClose} disabled={enrolling}>Cancel</button>
          <button className="btn btn-primary" onClick={handleEnroll} disabled={enrolling || !name.trim() || totalImages === 0}>
            {enrolling ? 'Enrolling...' : `Enroll (${totalImages} images)`}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Personnel;
