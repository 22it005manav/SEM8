import { useState, useEffect, useRef, useMemo } from 'react';
import {
  Upload, Play, Download, Trash2, Settings, AlertCircle, CheckCircle,
  Loader, ArrowRight, Sparkles, Zap, Video, FileVideo, Clock, Gauge,
  Film, HelpCircle, Shield, Activity, Layers, UploadCloud, X
} from 'lucide-react';
import { videoService, WebSocketService } from './services/api';
import { SplitScreenComparison } from './components/SplitScreenComparison';
import './App.css';

function App() {
  // State Management
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [livePreview, setLivePreview] = useState({ original: null, dehazed: null });
  const [liveFps, setLiveFps] = useState(0);
  const [showReview, setShowReview] = useState(false);

  const canUpload = !processing && !uploading && Boolean(selectedFile) && !jobId;
  const canStart = Boolean(jobId) && !processing;
  const canReview = Boolean(selectedFile);
  const canDownload = Boolean(status?.output_video_path);

  // Processing Stage Logic
  const stageText = useMemo(() => {
    if (status?.stage) return status.stage;
    const progressVal = status?.progress || 0;
    if (progressVal === 0) return 'Initializing model...';
    if (progressVal >= 100) return 'Finalizing video...';
    return 'Processing frames';
  }, [status]);

  // Live Stats Logic
  const liveStats = useMemo(() => {
    const framesProcessed = status?.current_frame || 0;
    const totalFrames = status?.total_frames || 0;
    const fps = status?.fps ?? liveFps ?? 0;
    const elapsed = status?.elapsed_time || 0;
    let remaining = status?.estimated_remaining;

    if ((remaining === undefined || remaining === null) && fps > 0 && totalFrames > framesProcessed) {
      const remainingFrames = totalFrames - framesProcessed;
      remaining = remainingFrames / fps;
    }

    if (remaining === undefined || remaining === null) remaining = 0;

    return { framesProcessed, totalFrames, fps, elapsed, remaining };
  }, [status, liveFps]);

  // Settings
  const [modelLayers, setModelLayers] = useState('8');
  const [resolution, setResolution] = useState(512);
  const [useGpu, setUseGpu] = useState(false);
  const [cudaAvailable, setCudaAvailable] = useState(null);
  const [useFp16, setUseFp16] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  // Refs
  const containerRef = useRef(null);
  const originalCanvasRef = useRef(null);
  const dehazedCanvasRef = useRef(null);
  const originalVideoRef = useRef(null);
  const dehazedVideoRef = useRef(null);
  const wsRef = useRef(null);
  const pollIntervalRef = useRef(null);
  const [syncedPlay, setSyncedPlay] = useState(false);
  const objectUrlRef = useRef(null);

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validate file name
    if (!file.name || file.name.trim() === '') {
      setError('Invalid file: filename is missing');
      return;
    }
    
    // Validate file extension
    if (!file.name.includes('.')) {
      setError('Invalid file: file must have an extension');
      return;
    }
    
    const validTypes = ['video/mp4', 'video/avi', 'video/x-msvideo', 'video/quicktime', 'video/x-matroska'];
    if (!validTypes.includes(file.type)) {
      setError('Invalid file type. Please upload MP4, AVI, MOV, or MKV');
      return;
    }
    if (file.size > 500 * 1024 * 1024) {
      setError('File too large. Maximum size is 500MB');
      return;
    }
    if (file.size === 0) {
      setError('Invalid file: file is empty');
      return;
    }
    
    stopPolling();
    if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
    objectUrlRef.current = URL.createObjectURL(file);
    setSelectedFile(file);
    setJobId(null);
    setStatus(null);
    setUploadProgress(0);
    setProcessing(false);
    setLivePreview({ original: null, dehazed: null });
    setLiveFps(0);
    setShowReview(false);
    setError(null);
    if (originalVideoRef.current) originalVideoRef.current.src = objectUrlRef.current;
  };

  const handleUpload = async () => {
    if (!selectedFile || uploading) return;
    setUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      const response = await videoService.uploadVideo(selectedFile, (progress) => setUploadProgress(progress));
      setJobId(response.job_id);
      setError(null);
    } catch (err) {
      console.error('Upload error:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Upload failed';
      setError(`Upload failed: ${errorMsg}`);
      setJobId(null);
    } finally {
      setUploading(false);
    }
  };

  const handleReview = () => {
    if (!selectedFile) return;
    setShowReview(true);
    if (originalVideoRef.current && objectUrlRef.current) {
      originalVideoRef.current.src = objectUrlRef.current;
    }
  };

  const handleProcess = async () => {
    if (!canStart) return;
    if (useGpu && cudaAvailable === false) {
      setError('CUDA is not available. Switch to CPU mode.');
      return;
    }
    const chosenDevice = useGpu && cudaAvailable ? 'cuda' : 'cpu';
    setProcessing(true);
    setError(null);
    setStatus({ progress: 0, current_frame: 0, total_frames: status?.total_frames || 0, stage: 'Starting...' });

    try {
      await videoService.startProcessing(jobId, { modelLayers, resolution, useFp16, device: chosenDevice });
      wsRef.current = new WebSocketService(jobId, (update) => {
        if (update.progress !== undefined) {
          setStatus(prev => ({ ...prev, ...update }));
          setLiveFps(update.fps || 0);
          if (update.preview) setLivePreview({ original: update.preview.original, dehazed: update.preview.dehazed });
        }
      });
      startPolling();
    } catch (err) {
      setError(err.response?.data?.detail || 'Processing failed');
      setProcessing(false);
    }
  };

  const startPolling = () => {
    pollIntervalRef.current = setInterval(async () => {
      try {
        const statusData = await videoService.getStatus(jobId);
        setStatus(statusData);
        if (statusData.status === 'completed') {
          setStatus({ ...statusData, progress: 100, stage: 'Completed' });
          setProcessing(false);
          stopPolling();
          loadOutputVideo();
        } else if (statusData.status === 'failed') {
          setError(statusData.error_message || 'Processing failed');
          setProcessing(false);
          stopPolling();
        }
      } catch (err) { console.error(err); }
    }, 2000);
  };

  const stopPolling = () => {
    if (pollIntervalRef.current) { clearInterval(pollIntervalRef.current); pollIntervalRef.current = null; }
    if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
  };

  const loadOutputVideo = () => {
    if (jobId && dehazedVideoRef.current) {
      const url = videoService.getDownloadUrl(jobId);
      dehazedVideoRef.current.src = url;
    }
  };

  const handlePlayPause = (e, isOriginal) => {
    const sourceVideo = isOriginal ? originalVideoRef.current : dehazedVideoRef.current;
    const targetVideo = isOriginal ? dehazedVideoRef.current : originalVideoRef.current;
    if (!sourceVideo) return;
    if (syncedPlay) {
      if (sourceVideo.paused) targetVideo?.pause();
      else targetVideo?.play();
    }
  };

  const handleTimeUpdate = (e, isOriginal) => {
    const sourceVideo = isOriginal ? originalVideoRef.current : dehazedVideoRef.current;
    const targetVideo = isOriginal ? dehazedVideoRef.current : originalVideoRef.current;
    if (!sourceVideo || !targetVideo) return;
    if (syncedPlay && targetVideo && Math.abs(targetVideo.currentTime - sourceVideo.currentTime) > 0.1) {
      targetVideo.currentTime = sourceVideo.currentTime;
    }
  };

  const handleDownload = () => { if (jobId) window.open(videoService.getDownloadUrl(jobId), '_blank'); };

  const handleReset = () => {
    stopPolling();
    setSelectedFile(null);
    setJobId(null);
    setStatus(null);
    setError(null);
    setUploadProgress(0);
    setProcessing(false);
    setShowReview(false);
    setLivePreview({ original: null, dehazed: null });
    setLiveFps(0);
    if (originalVideoRef.current) originalVideoRef.current.src = '';
    if (dehazedVideoRef.current) dehazedVideoRef.current.src = '';
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
  };

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const health = await videoService.healthCheck();
        setCudaAvailable(Boolean(health.cuda_available));
        setUseGpu(Boolean(health.cuda_available));
      } catch (err) { setCudaAvailable(false); }
    };
    fetchHealth();
  }, []);

  useEffect(() => {
    if (!useGpu || !cudaAvailable) setUseFp16(false);
  }, [useGpu, cudaAvailable]);

  useEffect(() => () => stopPolling(), []);
  useEffect(() => () => {
    if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
  }, []);

  // UI Components
  const ProgressBar = ({ progress, color = 'bg-cyan-400' }) => (
    <div className="h-2 bg-slate-900 rounded-full overflow-hidden w-full relative border border-slate-700">
      <div
        className={`h-full ${color} transition-all duration-300 relative`}
        style={{ width: `${progress}%` }}
      >
        <div className="absolute inset-0 bg-white/30 animate-pulse"></div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-cyan-500/30 overflow-x-hidden">

      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-slate-900/80 backdrop-blur-md border-b border-slate-800">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <Sparkles className="w-5 h-5 text-white fill-current" />
            </div>
            <span className="text-xl font-bold tracking-tight text-white">
              VideoDehaze<span className="text-cyan-400">AI</span>
            </span>
          </div>

          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-400">
            <button className="hover:text-white transition-colors">Dashboard</button>
            <button className="hover:text-white transition-colors">History</button>
            <button className="hover:text-white transition-colors" onClick={() => setShowHelp(true)}>Help</button>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className={`p-2 rounded-full hover:bg-slate-800 transition-colors ${showSettings ? 'text-cyan-400 bg-slate-800' : 'text-slate-400'}`}
            >
              <Settings className="w-5 h-5" />
            </button>
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700"></div>
          </div>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="container mx-auto px-4 py-8 max-w-6xl min-h-[calc(100vh-64px)] flex flex-col items-center justify-center relative">

        {/* Background Gradients */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-[100px] pointer-events-none"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-[100px] pointer-events-none"></div>

        {/* Error Toast */}
        {error && (
          <div className="fixed top-20 right-6 z-50 animate-[slideIn_0.3s_ease-out]">
            <div className="bg-red-500/10 border border-red-500/50 text-red-200 px-4 py-3 rounded-lg backdrop-blur-md shadow-lg flex items-start gap-3 max-w-md">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-sm">Error Occurred</h4>
                <p className="text-sm opacity-90">{error}</p>
              </div>
              <button onClick={() => setError(null)} className="ml-auto hover:text-white"><X className="w-4 h-4" /></button>
            </div>
          </div>
        )}

        {/* Settings Modal (Overlay) */}
        {showSettings && (
          <div className="absolute top-4 right-4 z-40 w-80 bg-slate-900/95 backdrop-blur-xl border border-slate-700 rounded-2xl shadow-2xl p-6 animate-[scaleIn_0.2s_ease-out]">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Settings className="w-5 h-5 text-cyan-400" /> Configuration
              </h3>
              <button onClick={() => setShowSettings(false)} className="text-slate-400 hover:text-white"><X className="w-4 h-4" /></button>
            </div>

            <div className="space-y-6">
              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Model Depth</label>
                <div className="grid grid-cols-2 gap-2">
                  {['8', '16'].map((l) => (
                    <button
                      key={l}
                      onClick={() => !processing && setModelLayers(l)}
                      className={`py-2 px-3 rounded-lg text-sm font-medium border transition-all ${modelLayers === l
                        ? 'bg-cyan-500/10 border-cyan-500/50 text-cyan-300 shadow-[0_0_15px_rgba(6,182,212,0.15)]'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-600'}`}
                    >
                      {l} Layers
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Resolution: {resolution}px</label>
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <input
                    type="range" min="256" max="1024" step="256"
                    value={resolution} onChange={(e) => setResolution(Number(e.target.value))}
                    disabled={processing}
                    className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500 mt-2 font-mono">
                    <span>256</span><span>512</span><span>768</span><span>1024</span>
                  </div>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Hardware</label>
                <div className="space-y-2">
                  <button
                    onClick={() => cudaAvailable && !processing && setUseGpu(!useGpu)}
                    className={`w-full flex items-center justify-between p-3 rounded-lg border transition-all ${useGpu
                      ? 'bg-green-500/10 border-green-500/40 text-green-300'
                      : 'bg-slate-950 border-slate-800 text-slate-400'}`}
                  >
                    <span className="flex items-center gap-2 text-sm"><Zap className="w-4 h-4" /> GPU Acceleration</span>
                    <div className={`w-2 h-2 rounded-full ${cudaAvailable ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  </button>
                  <button
                    onClick={() => useGpu && !processing && setUseFp16(!useFp16)}
                    disabled={!useGpu}
                    className={`w-full flex items-center justify-between p-3 rounded-lg border transition-all ${useFp16
                      ? 'bg-blue-500/10 border-blue-500/40 text-blue-300'
                      : 'bg-slate-950 border-slate-800 text-slate-500'}`}
                  >
                    <span className="flex items-center gap-2 text-sm"><Activity className="w-4 h-4" /> FP16 Precision</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* --- STATE 1: IDLE / HERO --- */}
        {!selectedFile && !jobId && !status?.output_video_path && (
          <div className="w-full max-w-4xl animate-[fadeIn_0.5s_ease-out] flex flex-col items-center text-center">

            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-900/50 border border-slate-800 text-xs font-medium text-cyan-400 mb-8 backdrop-blur-sm shadow-sm">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
              </span>
              v2.0 Now Available with 16-Layer Models
            </div>

            <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight tracking-tight">
              Enhance Your Videos <br /> with <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">AI Dehazing</span>
            </h1>

            <p className="text-lg text-slate-400 mb-12 max-w-2xl leading-relaxed">
              Professional-grade video restoration powered by deep learning. Remove haze, fog, and smoke in real-time with our advanced neural networks.
            </p>

            {/* Upload Area */}
            <div className="w-full max-w-2xl relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-500"></div>
              <div className="relative bg-slate-950 border border-slate-800 rounded-xl p-8 md:p-12 hover:border-cyan-500/50 transition-colors duration-300">
                
                {!uploading && !jobId ? (
                  // Show upload button when no file is being uploaded
                  <label className="flex flex-col items-center gap-6 cursor-pointer">
                    <input
                      type="file"
                      accept="video/*"
                      onChange={handleFileSelect}
                      className="hidden"
                      disabled={uploading}
                    />
                    <div className="w-20 h-20 bg-slate-900 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform duration-300 shadow-inner border border-slate-800">
                      <UploadCloud className="w-10 h-10 text-cyan-400" />
                    </div>
                    <div className="text-center">
                      <h3 className="text-xl font-semibold text-white mb-2">Click to Select Video</h3>
                      <p className="text-slate-400 text-sm">MP4, AVI, MKV up to 500MB</p>
                      <p className="text-cyan-400 text-xs mt-2 font-medium">Upload starts when you click Upload</p>
                    </div>
                  </label>
                ) : uploading ? (
                  // Show progress during upload
                  <div className="flex flex-col items-center gap-6 animate-[fadeIn_0.3s]">
                    <div className="w-20 h-20 bg-slate-900 rounded-full flex items-center justify-center border border-cyan-500/30">
                      <Loader className="w-10 h-10 text-cyan-400 animate-spin" />
                    </div>
                    <div className="text-center w-full">
                      <h3 className="text-lg font-semibold text-white mb-2">Uploading...</h3>
                      {selectedFile && <p className="text-slate-400 text-sm mb-4">{selectedFile.name}</p>}
                      <div className="w-full max-w-sm mx-auto">
                        <div className="flex justify-between text-sm text-slate-400 mb-2">
                          <span>Progress</span>
                          <span className="text-cyan-400 font-semibold">{uploadProgress}%</span>
                        </div>
                        <ProgressBar progress={uploadProgress} color="bg-cyan-400" />
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>

            {/* Features Grid */}
            <div className="grid md:grid-cols-4 gap-6 mt-20 text-left w-full max-w-5xl">
              {[
                { icon: Zap, title: "Real-Time", desc: "Instant processing with GPU support" },
                { icon: Layers, title: "Deep Learning", desc: "Advanced 16-layer U-Net architecture" },
                { icon: Shield, title: "Secure", desc: "Enterprise-grade data protection" },
                { icon: Activity, title: "High Quality", desc: "Support for 1080p+ restoration" },
              ].map((f, i) => (
                <div key={i} className="p-6 rounded-xl bg-slate-900/40 border border-slate-800 hover:bg-slate-900/60 transition-colors">
                  <f.icon className="w-8 h-8 text-cyan-400 mb-4" />
                  <h3 className="text-white font-semibold mb-2">{f.title}</h3>
                  <p className="text-sm text-slate-400">{f.desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* --- STATE 2: CONFIGURATION & PROCESSING --- */}
        {(selectedFile || jobId) && !status?.output_video_path && (
          <div className="w-full max-w-5xl animate-[scaleIn_0.3s_ease-out]">
            <div className="header mb-8 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                {processing ? <Loader className="w-6 h-6 animate-spin text-cyan-400" /> : <Settings className="w-6 h-6 text-cyan-400" />}
                {processing ? 'Processing Video...' : 'Project Workspace'}
              </h2>
              <button
                onClick={handleReset}
                className="text-slate-400 hover:text-red-400 text-sm flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-red-500/10 transition-colors"
                disabled={processing}
              >
                <Trash2 className="w-4 h-4" /> Cancel Project
              </button>
            </div>

            <div className="grid lg:grid-cols-3 gap-8 h-full">
              {/* Left Panel: Preview & Status */}
              <div className="lg:col-span-2 space-y-6">

                {/* Visualizer / Preview Box */}
                <div className="aspect-video bg-black rounded-2xl border border-slate-800 overflow-hidden relative shadow-2xl">
                  {processing && livePreview.original && livePreview.dehazed ? (
                    <div className="grid grid-cols-2 h-full">
                      <div className="relative border-r border-cyan-500/20">
                        <img src={`data:image/jpeg;base64,${livePreview.original}`} className="w-full h-full object-cover" />
                        <span className="absolute top-4 left-4 text-xs font-bold text-white bg-black/50 px-2 py-1 rounded backdrop-blur border border-white/10">INPUT</span>
                      </div>
                      <div className="relative">
                        <img src={`data:image/jpeg;base64,${livePreview.dehazed}`} className="w-full h-full object-cover" />
                        <span className="absolute top-4 right-4 text-xs font-bold text-white bg-cyan-600/80 px-2 py-1 rounded backdrop-blur border border-cyan-400/30">AI OUTPUT</span>
                      </div>
                    </div>
                  ) : showReview && selectedFile ? (
                    <div className="relative w-full h-full">
                      <video
                        ref={originalVideoRef}
                        controls
                        className="w-full h-full object-cover bg-black"
                      />
                      <span className="absolute top-4 left-4 text-xs font-bold text-white bg-black/50 px-2 py-1 rounded backdrop-blur border border-white/10">REVIEW</span>
                    </div>
                  ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center bg-slate-950/50">
                      {processing ? (
                        <div className="text-center">
                          <Loader className="w-12 h-12 text-cyan-400 animate-spin mx-auto mb-4" />
                          <p className="text-cyan-400 font-medium animate-pulse">Initializing neural network...</p>
                        </div>
                      ) : (
                        <div className="text-center text-slate-500">
                          <Video className="w-16 h-16 mx-auto mb-4 opacity-50" />
                          <p>Select a file and click Review to preview</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Progress Bar & Stats */}
                {processing && (
                  <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur">
                    <div className="flex justify-between text-sm font-medium mb-2">
                      <span className="text-cyan-400">{stageText}</span>
                      <span className="text-white">{status?.progress?.toFixed(1)}%</span>
                    </div>
                    <ProgressBar progress={status?.progress || 0} />

                    <div className="grid grid-cols-4 gap-4 mt-6 text-center">
                      {[
                        { label: 'FPS', val: liveStats.fps.toFixed(1) },
                        { label: 'Frames', val: `${liveStats.framesProcessed}/${liveStats.totalFrames}` },
                        { label: 'Time', val: `${Math.floor(liveStats.elapsed)}s` },
                        { label: 'Left', val: `~${Math.floor(liveStats.remaining)}s` }
                      ].map((s, i) => (
                        <div key={i} className="bg-slate-950/50 rounded-lg p-3 border border-slate-800">
                          <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">{s.label}</p>
                          <p className="text-lg font-bold text-white font-mono">{s.val}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Right Panel: Controls */}
              <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6 h-fit backdrop-blur">
                <h3 className="text-white font-semibold mb-6 flex items-center gap-2">
                  <Settings className="w-4 h-4 text-cyan-400" /> Controls
                </h3>

                <div className="space-y-6">
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      onClick={handleUpload}
                      disabled={!canUpload}
                      className={`py-3 rounded-lg font-semibold flex items-center justify-center gap-2 transition-all ${canUpload
                        ? 'bg-cyan-600 hover:bg-cyan-500 text-white'
                        : 'bg-slate-800 text-slate-500 cursor-not-allowed'}`}
                    >
                      <Upload className="w-4 h-4" /> Upload
                    </button>
                    <button
                      onClick={handleReview}
                      disabled={!canReview}
                      className={`py-3 rounded-lg font-semibold flex items-center justify-center gap-2 transition-all ${canReview
                        ? 'bg-slate-800 hover:bg-slate-700 text-slate-200'
                        : 'bg-slate-800 text-slate-500 cursor-not-allowed'}`}
                    >
                      <Video className="w-4 h-4" /> Review
                    </button>
                    <button
                      onClick={handleProcess}
                      disabled={!canStart || processing}
                      className={`py-3 rounded-lg font-semibold flex items-center justify-center gap-2 transition-all col-span-2 ${(!canStart || processing)
                        ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                        : 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white'}`}
                    >
                      {processing ? <Loader className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4 fill-white" />}
                      {processing ? 'Dehazing...' : 'Start Dehazing'}
                    </button>
                    <button
                      onClick={handleDownload}
                      disabled={!canDownload}
                      className={`py-3 rounded-lg font-semibold flex items-center justify-center gap-2 transition-all col-span-2 ${canDownload
                        ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                        : 'bg-slate-800 text-slate-500 cursor-not-allowed'}`}
                    >
                      <Download className="w-4 h-4" /> Download
                    </button>
                  </div>

                  {uploading && (
                    <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4">
                      <div className="flex justify-between text-xs text-slate-400 mb-2">
                        <span>Upload Progress</span>
                        <span className="text-cyan-400 font-semibold">{uploadProgress}%</span>
                      </div>
                      <ProgressBar progress={uploadProgress} color="bg-cyan-400" />
                    </div>
                  )}

                  <div>
                    <label className="text-xs text-slate-400 uppercase font-bold mb-3 block">Enhancement Model</label>
                    <div className="grid grid-cols-3 gap-2">
                      {['4', '8', '16'].map((l) => (
                        <button
                          key={l}
                          onClick={() => !processing && setModelLayers(l)}
                          className={`py-2 rounded-lg text-sm font-semibold border transition-all ${modelLayers === l
                            ? 'bg-cyan-500/10 border-cyan-500/50 text-cyan-300'
                            : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-600'}`}
                        >
                          {l} Layers
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="text-xs text-slate-400 uppercase font-bold mb-3 block">Resolution</label>
                    <div className="bg-slate-950 rounded-lg p-4 border border-slate-800">
                      <input
                        type="range" min="256" max="1024" step="256"
                        value={resolution} onChange={(e) => setResolution(Number(e.target.value))} disabled={processing}
                        className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
                      />
                      <div className="flex justify-between mt-2 text-xs text-slate-400 font-mono">
                        <span>256p</span><span>{resolution}p</span><span>1024p</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="text-xs text-slate-400 uppercase font-bold mb-3 block">Device</label>
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={() => !processing && setUseGpu(false)}
                        className={`py-2 rounded-lg text-sm font-semibold border transition-all ${!useGpu
                          ? 'bg-blue-500/10 border-blue-500/50 text-blue-300'
                          : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-600'}`}
                      >
                        CPU
                      </button>
                      <button
                        onClick={() => cudaAvailable && !processing && setUseGpu(true)}
                        disabled={!cudaAvailable}
                        className={`py-2 rounded-lg text-sm font-semibold border transition-all ${useGpu
                          ? 'bg-green-500/10 border-green-500/50 text-green-300'
                          : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-600'} ${!cudaAvailable ? 'cursor-not-allowed opacity-50' : ''}`}
                      >
                        GPU
                      </button>
                    </div>
                    {cudaAvailable === false && (
                      <p className="text-xs text-red-400 mt-2">CUDA not available. GPU disabled.</p>
                    )}
                  </div>

                  <div>
                    <label className="text-xs text-slate-400 uppercase font-bold mb-3 block">FP16 Precision</label>
                    <button
                      onClick={() => useGpu && !processing && setUseFp16(!useFp16)}
                      disabled={!useGpu}
                      className={`w-full py-2 rounded-lg text-sm font-semibold border transition-all ${useFp16
                        ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-300'
                        : 'bg-slate-950 border-slate-800 text-slate-500'} ${!useGpu ? 'cursor-not-allowed opacity-50' : ''}`}
                    >
                      {useFp16 ? 'Enabled' : 'Disabled'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* --- STATE 3: COMPLETED --- */}
        {status?.output_video_path && (
          <div className="w-full max-w-6xl animate-[scaleIn_0.3s_ease-out]">
            <div className="text-center mb-10">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-500/10 border border-green-500/30 text-green-400 mb-4 shadow-[0_0_20px_rgba(34,197,94,0.3)]">
                <CheckCircle className="w-8 h-8" />
              </div>
              <h2 className="text-4xl font-bold text-white mb-2">Enhancement Complete</h2>
              <p className="text-slate-400">Your video has been successfully processed and optimized.</p>
            </div>

            <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-2 pb-0 overflow-hidden shadow-2xl backdrop-blur-md">
              {/* Split Comparison */}
              <div className="aspect-video bg-black rounded-xl overflow-hidden relative group" ref={containerRef}>
                <SplitScreenComparison
                  originalVideoRef={originalVideoRef}
                  dehazedVideoRef={dehazedVideoRef}
                  onPlayPause={handlePlayPause}
                  onTimeUpdate={handleTimeUpdate}
                  syncedPlay={syncedPlay}
                  onSyncToggle={setSyncedPlay}
                />

                {/* Floating Video Controls */}
                <div className="absolute opacity-0 group-hover:opacity-100 transition-opacity bottom-6 left-1/2 -translate-x-1/2 bg-slate-900/90 border border-slate-700 px-6 py-2 rounded-full flex items-center gap-4 text-white text-sm backdrop-blur">
                  <span>Move cursor to compare</span>
                  <div className="h-4 w-px bg-slate-600"></div>
                  <span className="font-mono text-cyan-400">
                    ORIGINAL vs ENHANCED
                  </span>
                </div>
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-6 mt-8">
              <button
                onClick={handleDownload}
                className="flex flex-col items-center justify-center p-6 bg-gradient-to-br from-green-600 to-emerald-600 rounded-xl text-white hover:scale-[1.02] transition-transform shadow-lg group"
              >
                <Download className="w-8 h-8 mb-2 group-hover:animate-bounce" />
                <span className="font-bold text-lg">Download Result</span>
                <span className="text-xs opacity-70 mt-1">MP4 Format • High Quality</span>
              </button>

              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 flex flex-col justify-center">
                <div className="text-center">
                  <p className="text-slate-400 text-sm uppercase font-bold mb-1">Processing Time</p>
                  <p className="text-2xl font-mono text-white">{status.statistics?.total_time_seconds}s</p>
                  <p className="text-xs text-slate-500 mt-2">Avg Speed: {status.statistics?.average_fps.toFixed(1)} FPS</p>
                </div>
              </div>

              <button
                onClick={handleReset}
                className="flex flex-col items-center justify-center p-6 bg-slate-800 border border-slate-700 rounded-xl text-slate-300 hover:bg-slate-700 hover:text-white transition-colors group"
              >
                <Trash2 className="w-8 h-8 mb-2 group-hover:text-red-400 transition-colors" />
                <span className="font-bold text-lg">Start New Project</span>
              </button>
            </div>
          </div>
        )}

      </main>

      {/* Floating Help Button */}
      <button
        className="fixed bottom-6 right-6 w-12 h-12 bg-slate-900 hover:bg-cyan-600 text-cyan-400 hover:text-white rounded-full shadow-lg border border-cyan-500/30 flex items-center justify-center transition-all z-40"
        title="Help & Support"
        onClick={() => setShowHelp(true)}
      >
        <HelpCircle className="w-6 h-6" />
      </button>

      {/* Help Modal */}
      {showHelp && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-[fadeIn_0.2s_ease-out]" onClick={() => setShowHelp(false)}>
          <div className="bg-slate-900 border border-slate-700 p-8 rounded-2xl max-w-lg shadow-2xl relative" onClick={e => e.stopPropagation()}>
            <h2 className="text-2xl font-bold text-white mb-6">How to use VideoDehaze AI</h2>
            <div className="space-y-6">
              {[
                { step: 1, title: 'Upload', desc: 'Drag & drop any hazy video file (MP4, AVI, MKV).' },
                { step: 2, title: 'Configure', desc: 'Select AI model depth (8 or 16 layers) and target resolution.' },
                { step: 3, title: 'Process', desc: 'Watch real-time GPU enhancement as our AI cleans your footage.' },
                { step: 4, title: 'Download', desc: 'Compare results side-by-side and download the HD output.' },
              ].map((s) => (
                <div key={s.step} className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold shrink-0 border border-cyan-500/30">
                    {s.step}
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">{s.title}</h3>
                    <p className="text-slate-400 text-sm">{s.desc}</p>
                  </div>
                </div>
              ))}
            </div>
            <button
              onClick={() => setShowHelp(false)}
              className="mt-8 w-full py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors"
            >
              Start Dehazing
            </button>
          </div>
        </div>
      )}

    </div>
  );
}

export default App;
