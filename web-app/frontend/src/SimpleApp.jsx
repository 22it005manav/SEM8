import { useState, useEffect, useRef } from 'react';
import './SimpleApp.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

function SimpleApp() {
  // Core state
  const [selectedFile, setSelectedFile] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState('idle'); // idle, uploading, reviewing, processing, completed, error
  const [statusText, setStatusText] = useState('');
  const [error, setError] = useState(null);
  const [outputVideoUrl, setOutputVideoUrl] = useState(null);
  const [isReviewing, setIsReviewing] = useState(false);
  
  // Processing options
  const [modelLayers, setModelLayers] = useState('8');
  const [useGpu, setUseGpu] = useState(false);
  const [cudaAvailable, setCudaAvailable] = useState(false);
  const [useFp16, setUseFp16] = useState(false);
  const [resolution, setResolution] = useState(512);
  const [uploadProgress, setUploadProgress] = useState(0);
  
  // Real-time stats
  const [stats, setStats] = useState({
    fps: 0,
    currentFrame: 0,
    totalFrames: 0,
    elapsed: 0,
    remaining: 0
  });
  
  const fileInputRef = useRef(null);
  const wsRef = useRef(null);
  const pollIntervalRef = useRef(null);
  const videoPreviewRef = useRef(null);
  const objectUrlRef = useRef(null);

  // Check CUDA availability on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        setCudaAvailable(data.cuda_available);
        setUseGpu(data.cuda_available);
      } catch (err) {
        console.log('Health check failed:', err);
        setCudaAvailable(false);
      }
    };
    checkHealth();
  }, []);

  // Cleanup
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
      }
    };
  }, []);

  // Handle file selection
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const validTypes = ['video/mp4', 'video/avi', 'video/x-msvideo', 'video/quicktime', 'video/x-matroska'];
    if (!validTypes.includes(file.type)) {
      setError('Invalid file type. Please use MP4, AVI, MOV, or MKV');
      return;
    }
    if (file.size > 500 * 1024 * 1024) {
      setError('File too large. Maximum size is 500MB');
      return;
    }

    setSelectedFile(file);
    setError(null);
    setIsReviewing(false);
    setJobId(null);
    setProgress(0);
    setStage('idle');
  };

  // Review/Preview video
  const handleReview = () => {
    if (!selectedFile) return;

    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
    }
    objectUrlRef.current = URL.createObjectURL(selectedFile);
    
    if (videoPreviewRef.current) {
      videoPreviewRef.current.src = objectUrlRef.current;
    }
    setIsReviewing(true);
  };

  // Upload video
  const handleUpload = async () => {
    if (!selectedFile) return;

    setStage('uploading');
    setUploadProgress(0);
    setStatusText('Uploading video...');
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percent = Math.round((e.loaded / e.total) * 100);
          setUploadProgress(percent);
          setStatusText(`Uploading... ${percent}%`);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          const response = JSON.parse(xhr.responseText);
          setJobId(response.job_id);
          setStage('ready');
          setProgress(0);
          setUploadProgress(0);
          setStatusText('Upload complete! Ready to process.');
        } else {
          const errorData = JSON.parse(xhr.responseText);
          throw new Error(errorData.detail || 'Upload failed');
        }
      });

      xhr.addEventListener('error', () => {
        throw new Error('Upload failed - network error');
      });

      xhr.open('POST', `${API_BASE}/upload`);
      xhr.send(formData);

    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message || 'Upload failed');
      setStage('error');
      setUploadProgress(0);
    }
  };

  // Start processing
  const handleProcess = async () => {
    if (!jobId) return;

    const device = (useGpu && cudaAvailable) ? 'cuda' : 'cpu';

    setStage('processing');
    setProgress(0);
    setStatusText('Starting video dehazing...');
    setError(null);
    setStats({ fps: 0, currentFrame: 0, totalFrames: 0, elapsed: 0, remaining: 0 });

    try {
      const response = await fetch(`${API_BASE}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: jobId,
          model_layers: parseInt(modelLayers),
          resolution: resolution,
          use_fp16: useFp16 && device === 'cuda',
          device: device
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to start processing');
      }

      connectWebSocket(jobId);
      startPolling(jobId);

    } catch (err) {
      console.error('Process error:', err);
      setError(err.message || 'Processing failed');
      setStage('error');
    }
  };

  // WebSocket connection
  const connectWebSocket = (jobId) => {
    try {
      const wsUrl = `ws://localhost:8000/api/ws/${jobId}`;
      const ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.progress !== undefined) {
          setProgress(Math.round(data.progress));
          setStatusText(data.stage || `Processing... ${Math.round(data.progress)}%`);
          if (data.fps) setStats(s => ({ ...s, fps: data.fps }));
          if (data.current_frame) setStats(s => ({ ...s, currentFrame: data.current_frame }));
          if (data.total_frames) setStats(s => ({ ...s, totalFrames: data.total_frames }));
          if (data.elapsed_time) setStats(s => ({ ...s, elapsed: data.elapsed_time }));
          if (data.estimated_remaining) setStats(s => ({ ...s, remaining: data.estimated_remaining }));
        }
      };

      ws.onerror = (error) => {
        console.log('WebSocket error (falling back to polling):', error);
      };

      wsRef.current = ws;
    } catch (err) {
      console.log('WebSocket connection failed, using polling only');
    }
  };

  // Poll for status
  const startPolling = (jobId) => {
    pollIntervalRef.current = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE}/status/${jobId}`);
        const data = await response.json();

        if (data.progress !== undefined) {
          setProgress(Math.round(data.progress));
          setStats(s => ({
            ...s,
            fps: data.fps || s.fps,
            currentFrame: data.current_frame || s.currentFrame,
            totalFrames: data.total_frames || s.totalFrames,
            elapsed: data.elapsed_time || s.elapsed,
            remaining: data.estimated_remaining || s.remaining
          }));
        }

        if (data.status === 'completed') {
          setStage('completed');
          setProgress(100);
          setStatusText('Processing complete! Ready to download.');
          setOutputVideoUrl(`${API_BASE}/download/${jobId}`);
          stopPolling();
        } else if (data.status === 'failed') {
          setStage('error');
          setError(data.error_message || 'Processing failed');
          stopPolling();
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 1000);
  };

  // Stop polling
  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  // Download result
  const handleDownload = () => {
    if (outputVideoUrl) {
      window.open(outputVideoUrl, '_blank');
    }
  };

  // Reset
  const handleReset = () => {
    stopPolling();
    setSelectedFile(null);
    setJobId(null);
    setProgress(0);
    setStage('idle');
    setStatusText('');
    setError(null);
    setOutputVideoUrl(null);
    setIsReviewing(false);
    setUploadProgress(0);
    setStats({ fps: 0, currentFrame: 0, totalFrames: 0, elapsed: 0, remaining: 0 });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
  };

  return (
    <div className="simple-app">
      {/* Header */}
      <header className="header">
        <h1>🌥️ Video Dehazing AI</h1>
        <p>Professional Video Enhancement with Deep Learning</p>
      </header>

      {/* Main Container */}
      <div className="container">
        <div className="card">
          
          {/* Error Message */}
          {error && (
            <div className="alert alert-error">
              <span>⚠️</span>
              <div>
                <strong>Error:</strong> {error}
              </div>
            </div>
          )}

          {/* === STEP 1: FILE SELECTION === */}
          <div className="section">
            <h2>📁 Step 1: Select Video</h2>
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              onChange={handleFileSelect}
              disabled={stage === 'uploading' || stage === 'processing'}
              className="file-input"
            />
            {selectedFile && (
              <div className="file-info">
                ✓ <strong>{selectedFile.name}</strong> ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
              </div>
            )}
          </div>

          {/* === ACTION BUTTONS: Upload/Review === */}
          {!jobId && selectedFile && stage !== 'uploading' && stage !== 'processing' && (
            <div className="section buttons-grid">
              <button 
                className="btn btn-primary"
                onClick={handleReview}
              >
                👁️ Review
              </button>
              <button 
                className="btn btn-success btn-large"
                onClick={handleUpload}
              >
                📤 Upload
              </button>
            </div>
          )}

          {/* === STEP 2: VIDEO PREVIEW === */}
          {isReviewing && selectedFile && (
            <div className="section">
              <h2>🎬 Preview</h2>
              <div className="video-preview">
                <video
                  ref={videoPreviewRef}
                  controls
                  className="preview-video"
                >
                  Your browser does not support video playback.
                </video>
              </div>
            </div>
          )}

          {/* === UPLOAD PROGRESS === */}
          {stage === 'uploading' && (
            <div className="section">
              <div className="progress-info">
                <span>📤 Uploading...</span>
                <span className="progress-percent">{uploadProgress}%</span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* === STEP 3: PROCESSING OPTIONS === */}
          {jobId && stage !== 'processing' && stage !== 'completed' && stage !== 'error' && (
            <div className="section">
              <h2>⚙️ Step 2: Processing Settings</h2>
              
              <div className="settings-grid">
                
                {/* Model Selection */}
                <div className="setting-group">
                  <label>Model Depth</label>
                  <div className="button-group">
                    {['4', '8', '16'].map(layers => (
                      <button
                        key={layers}
                        className={`btn-option ${modelLayers === layers ? 'active' : ''}`}
                        onClick={() => setModelLayers(layers)}
                        disabled={stage === 'processing'}
                      >
                        {layers} Layers
                      </button>
                    ))}
                  </div>
                </div>

                {/* Device Selection */}
                <div className="setting-group">
                  <label>Device</label>
                  <div className="button-group">
                    <button
                      className={`btn-option ${!useGpu ? 'active' : ''}`}
                      onClick={() => setUseGpu(false)}
                      disabled={stage === 'processing'}
                    >
                      💻 CPU
                    </button>
                    <button
                      className={`btn-option ${useGpu ? 'active' : ''} ${!cudaAvailable ? 'disabled' : ''}`}
                      onClick={() => cudaAvailable && setUseGpu(true)}
                      disabled={!cudaAvailable || stage === 'processing'}
                      title={!cudaAvailable ? 'CUDA not available' : ''}
                    >
                      🎮 GPU{!cudaAvailable ? ' (N/A)' : ''}
                    </button>
                  </div>
                </div>

                {/* FP16 Option */}
                {useGpu && cudaAvailable && (
                  <div className="setting-group">
                    <label>FP16 Precision</label>
                    <button
                      className={`btn-option btn-toggle ${useFp16 ? 'active' : ''}`}
                      onClick={() => setUseFp16(!useFp16)}
                      disabled={stage === 'processing'}
                    >
                      {useFp16 ? '✓ Enabled' : '○ Disabled'}
                    </button>
                  </div>
                )}

                {/* Resolution */}
                <div className="setting-group">
                  <label>Resolution: {resolution}px</label>
                  <input
                    type="range"
                    min="256"
                    max="1024"
                    step="256"
                    value={resolution}
                    onChange={(e) => setResolution(Number(e.target.value))}
                    disabled={stage === 'processing'}
                    className="slider"
                  />
                  <div className="resolution-labels">
                    <span>256</span><span>512</span><span>768</span><span>1024</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* === PROCESSING PROGRESS === */}
          {stage === 'processing' && (
            <div className="section">
              <h2>🔄 Step 3: Processing</h2>
              
              <div className="progress-info">
                <span>{statusText}</span>
                <span className="progress-percent">{progress}%</span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${progress}%` }}
                >
                  <span className="progress-text">{progress}%</span>
                </div>
              </div>

              {/* Real-time Statistics */}
              {(stats.totalFrames > 0 || stats.fps > 0) && (
                <div className="stats-grid">
                  <div className="stat-box">
                    <div className="stat-label">FPS</div>
                    <div className="stat-value">{stats.fps.toFixed(1)}</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-label">Frames</div>
                    <div className="stat-value">{stats.currentFrame}/{stats.totalFrames}</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-label">Elapsed</div>
                    <div className="stat-value">{Math.floor(stats.elapsed)}s</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-label">Remaining</div>
                    <div className="stat-value">~{Math.floor(stats.remaining)}s</div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* === ACTION BUTTONS: Process/Download === */}
          <div className="section buttons-main">
            {jobId && stage === 'ready' && (
              <button 
                className="btn btn-success btn-large"
                onClick={handleProcess}
              >
                🎬 Start Dehazing
              </button>
            )}

            {stage === 'completed' && (
              <>
                <div className="alert alert-success">
                  ✅ <strong>Processing Complete!</strong> Your dehazed video is ready.
                </div>
                <button 
                  className="btn btn-primary btn-large"
                  onClick={handleDownload}
                >
                  ⬇️ Download Result
                </button>
              </>
            )}

            {(stage !== 'idle' && stage !== 'uploading') && (
              <button 
                className="btn btn-secondary"
                onClick={handleReset}
                disabled={stage === 'processing'}
              >
                🔄 Start New
              </button>
            )}
          </div>

        </div>

        {/* Instructions */}
        <div className="instructions">
          <h3>📋 How to Use:</h3>
          <ol>
            <li>Select your video file (MP4, AVI, MOV, or MKV)</li>
            <li>Click <strong>Review</strong> to preview, then <strong>Upload</strong></li>
            <li>Select processing settings (model, device, resolution)</li>
            <li>Click <strong>Start Dehazing</strong> and watch real-time progress</li>
            <li>Click <strong>Download Result</strong> when complete</li>
          </ol>
          <p><em>⏱️ Processing time depends on video length and device. GPU is significantly faster than CPU.</em></p>
        </div>
      </div>
    </div>
  );
}

export default SimpleApp;
