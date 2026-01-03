import { useState, useEffect, useRef } from 'react';
import { Upload, Play, Download, Trash2, Settings, AlertCircle, CheckCircle, Loader, ArrowRight, Sparkles, Zap, Video, FileVideo, Clock, Gauge, Film } from 'lucide-react';
import { videoService, WebSocketService } from './services/api';
import { SplitScreenComparison } from './components/SplitScreenComparison';
import './App.css';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [livePreview, setLivePreview] = useState({ original: null, dehazed: null });
  const [liveFps, setLiveFps] = useState(0);

  // Settings
  // Default to 8-layer model (only pretrained weights shipped by default)
  const [modelLayers, setModelLayers] = useState('8');
  const [resolution, setResolution] = useState(512);
  const [useFp16, setUseFp16] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Video refs
  const containerRef = useRef(null);
  const originalCanvasRef = useRef(null);
  const dehazedCanvasRef = useRef(null);
  const originalVideoRef = useRef(null);
  const dehazedVideoRef = useRef(null);
  const wsRef = useRef(null);
  const pollIntervalRef = useRef(null);
  const [syncedPlay, setSyncedPlay] = useState(false);

  // File selection
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      const validTypes = ['video/mp4', 'video/avi', 'video/x-msvideo', 'video/quicktime', 'video/x-matroska'];
      if (!validTypes.includes(file.type)) {
        setError('Invalid file type. Please upload MP4, AVI, MOV, or MKV');
        return;
      }

      if (file.size > 500 * 1024 * 1024) {
        setError('File too large. Maximum size is 500MB');
        return;
      }

      setSelectedFile(file);
      setError(null);

      // Preview original video
      const url = URL.createObjectURL(file);
      if (originalVideoRef.current) {
        originalVideoRef.current.src = url;
      }
    }
  };

  // Upload video
  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setError(null);
    setUploadProgress(0);

    try {
      const response = await videoService.uploadVideo(
        selectedFile,
        (progress) => setUploadProgress(progress)
      );

      setJobId(response.job_id);
      console.log('Upload successful:', response);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  // Start processing
  const handleProcess = async () => {
    if (!jobId) return;

    setProcessing(true);
    setError(null);

    try {
      await videoService.startProcessing(jobId, {
        modelLayers,
        resolution,
        useFp16,
      });

      // Connect WebSocket for real-time updates
      wsRef.current = new WebSocketService(jobId, (update) => {
        console.log('WebSocket update:', update);
        if (update.progress !== undefined) {
          setStatus(prev => ({ ...prev, ...update }));
          setLiveFps(update.fps || 0);

          // Update live preview frames
          if (update.preview) {
            setLivePreview({
              original: update.preview.original,
              dehazed: update.preview.dehazed
            });
          }
        }
      });

      // Start polling as backup
      startPolling();

    } catch (err) {
      setError(err.response?.data?.detail || 'Processing failed');
      setProcessing(false);
    }
  };

  // Poll status
  const startPolling = () => {
    pollIntervalRef.current = setInterval(async () => {
      try {
        const statusData = await videoService.getStatus(jobId);
        setStatus(statusData);

        if (statusData.status === 'completed') {
          setProcessing(false);
          stopPolling();
          loadOutputVideo();
        } else if (statusData.status === 'failed') {
          setError(statusData.error_message || 'Processing failed');
          setProcessing(false);
          stopPolling();
        }
      } catch (err) {
        console.error('Status poll error:', err);
      }
    }, 2000);
  };

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

  // Load output video
  const loadOutputVideo = () => {
    if (jobId && dehazedVideoRef.current) {
      const url = videoService.getDownloadUrl(jobId);
      dehazedVideoRef.current.src = url;
    }
  };

  // Sync video playback
  const handlePlayPause = (e, isOriginal) => {
    const sourceVideo = isOriginal ? originalVideoRef.current : dehazedVideoRef.current;
    const targetVideo = isOriginal ? dehazedVideoRef.current : originalVideoRef.current;

    if (syncedPlay) {
      if (sourceVideo.paused) {
        targetVideo?.pause();
      } else {
        targetVideo?.play();
      }
    }
  };

  const handleTimeUpdate = (e, isOriginal) => {
    const sourceVideo = isOriginal ? originalVideoRef.current : dehazedVideoRef.current;
    const targetVideo = isOriginal ? dehazedVideoRef.current : originalVideoRef.current;

    if (syncedPlay && targetVideo && Math.abs(targetVideo.currentTime - sourceVideo.currentTime) > 0.1) {
      targetVideo.currentTime = sourceVideo.currentTime;
    }
  };

  // Download output
  const handleDownload = () => {
    if (jobId) {
      window.open(videoService.getDownloadUrl(jobId), '_blank');
    }
  };

  // Reset
  const handleReset = () => {
    stopPolling();
    setSelectedFile(null);
    setJobId(null);
    setStatus(null);
    setError(null);
    setUploadProgress(0);
    setProcessing(false);
    if (originalVideoRef.current) originalVideoRef.current.src = '';
    if (dehazedVideoRef.current) dehazedVideoRef.current.src = '';
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0d1a] via-[#141625] to-[#0f1117] relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-purple-600/15 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-pink-600/15 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-3xl animate-pulse delay-2000"></div>
        {/* Grid overlay for depth */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(139,92,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(139,92,246,0.03)_1px,transparent_1px)] bg-[size:100px_100px] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_50%,#000_70%,transparent_100%)]"></div>
      </div>

      {/* Header */}
      <header className="relative bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 backdrop-blur-xl border-b-2 border-purple-500/30 sticky top-0 z-50 shadow-2xl">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-5">
              <div className="relative group">
                <div className="absolute inset-0 bg-gradient-to-br from-purple-500 via-pink-500 to-indigo-500 rounded-2xl blur-xl opacity-60 group-hover:opacity-90 transition-opacity duration-300"></div>
                <div className="relative p-4 bg-gradient-to-br from-purple-600 via-pink-600 to-indigo-600 rounded-2xl shadow-2xl transform hover:scale-110 transition-all duration-300">
                  <Video className="w-8 h-8 text-white" />
                </div>
              </div>
              <div>
                <h1 className="text-5xl font-black bg-gradient-to-r from-purple-400 via-pink-400 to-indigo-400 bg-clip-text text-transparent tracking-tight leading-none">
                  Video Dehazing
                </h1>
                <p className="text-base text-purple-300/90 font-semibold flex items-center gap-2 mt-1.5">
                  <Sparkles className="w-4 h-4" />
                  Deep Learning Powered
                </p>
              </div>
            </div>
            <div className="hidden md:flex items-center gap-3 px-5 py-2.5 bg-gradient-to-r from-green-500/20 to-emerald-500/20 rounded-full border-2 border-green-500/40 backdrop-blur-sm shadow-lg">
              <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse shadow-lg shadow-green-400/70"></div>
              <span className="text-sm font-bold text-green-300 uppercase tracking-wide">System Ready</span>
            </div>
          </div>
        </div>
      </header>

      <main className="relative container mx-auto px-4 md:px-6 py-10">
        {/* Error Alert */}
        {error && (
          <div className="mb-8 p-5 bg-gradient-to-r from-red-900/50 to-rose-900/50 border-2 border-red-500/50 rounded-2xl flex items-start gap-4 animate-slideIn shadow-2xl backdrop-blur-sm">
            <div className="p-2 bg-red-500/20 rounded-xl">
              <AlertCircle className="w-6 h-6 text-red-400" />
            </div>
            <div className="flex-1">
              <p className="font-bold text-red-200 text-lg mb-1">Oops! Something went wrong</p>
              <p className="text-red-300/90 text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Upload Section */}
        {!jobId && (
          <div className="mb-10 animate-slideIn">
            <div className="relative bg-gradient-to-br from-slate-900/80 via-slate-900/70 to-slate-800/80 backdrop-blur-2xl border-2 border-purple-500/40 rounded-3xl p-12 shadow-2xl overflow-hidden hover:border-purple-500/60 transition-all duration-500">
              {/* Decorative gradient overlay */}
              <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-full blur-3xl -mr-40 -mt-40"></div>
              <div className="absolute bottom-0 left-0 w-80 h-80 bg-gradient-to-tr from-indigo-500/15 to-purple-500/15 rounded-full blur-3xl -ml-40 -mb-40"></div>

              <div className="relative">
                <h2 className="text-3xl font-black mb-8 text-white flex items-center gap-4">
                  <div className="p-3 bg-gradient-to-br from-purple-600 to-pink-600 rounded-2xl shadow-xl">
                    <FileVideo className="w-7 h-7 text-white" />
                  </div>
                  <span className="bg-gradient-to-r from-purple-200 via-pink-200 to-indigo-200 bg-clip-text text-transparent">
                    Video Upload Area
                  </span>
                </h2>

                <div className="border-3 border-dashed border-purple-400/50 rounded-2xl p-20 text-center hover:border-purple-400/80 hover:bg-gradient-to-br hover:from-purple-500/10 hover:to-pink-500/10 transition-all duration-500 group cursor-pointer backdrop-blur-sm bg-slate-900/30">
                  <input
                    type="file"
                    accept="video/mp4,video/avi,video/quicktime,video/x-matroska"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="file-upload"
                    disabled={uploading}
                  />
                  <label
                    htmlFor="file-upload"
                    className="cursor-pointer flex flex-col items-center gap-6"
                  >
                    <div className="relative">
                      <div className="absolute inset-0 bg-gradient-to-br from-purple-500 via-pink-500 to-indigo-500 rounded-full blur-2xl opacity-40 group-hover:opacity-70 transition-opacity duration-500"></div>
                      <div className="relative p-8 bg-gradient-to-br from-purple-600 via-pink-600 to-indigo-600 rounded-full shadow-2xl transform group-hover:scale-110 transition-all duration-500">
                        <Upload className="w-16 h-16 text-white" />
                      </div>
                    </div>
                    <div>
                      <p className="text-2xl font-black text-white mb-3">
                        {selectedFile ? (
                          <span className="flex items-center gap-3 justify-center">
                            <Video className="w-6 h-6 text-purple-400" />
                            {selectedFile.name}
                          </span>
                        ) : (
                          'Drag & Drop or Click to Upload'
                        )}
                      </p>
                      <p className="text-base text-purple-300/80 font-semibold">
                        Supported: MP4, AVI, MOV, MKV • Max Size: 500MB
                      </p>
                    </div>
                  </label>
                </div>

                {selectedFile && (
                  <div className="mt-10 animate-slideIn">
                    <button
                      onClick={handleUpload}
                      disabled={uploading}
                      className="w-full bg-gradient-to-r from-purple-600 via-pink-600 to-indigo-600 hover:from-purple-700 hover:via-pink-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-black py-6 px-10 rounded-2xl flex items-center justify-center gap-4 transition-all duration-300 shadow-2xl hover:shadow-purple-500/60 transform hover:scale-[1.02] active:scale-[0.98] text-xl"
                    >
                      {uploading ? (
                        <>
                          <Loader className="w-7 h-7 animate-spin" />
                          <span>Uploading... {uploadProgress}%</span>
                        </>
                      ) : (
                        <>
                          <Upload className="w-7 h-7" />
                          <span>Upload & Continue</span>
                          <ArrowRight className="w-6 h-6" />
                        </>
                      )}
                    </button>

                    {uploadProgress > 0 && uploadProgress < 100 && (
                      <div className="mt-8">
                        <div className="h-4 bg-slate-950/80 rounded-full overflow-hidden shadow-inner border-2 border-slate-800">
                          <div
                            className="h-full bg-gradient-to-r from-purple-500 via-pink-500 to-indigo-500 transition-all duration-300 rounded-full shadow-lg relative overflow-hidden"
                            style={{ width: `${uploadProgress}%` }}
                          >
                            <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
                          </div>
                        </div>
                        <p className="text-center text-purple-300 text-base font-bold mt-3 flex items-center justify-center gap-2">
                          <Loader className="w-4 h-4 animate-spin" />
                          {uploadProgress}% Complete
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Processing Section */}
        {jobId && !status?.output_video_path && (
          <div className="mb-10 animate-slideIn">
            <div className="relative bg-gradient-to-br from-slate-900/80 via-slate-900/70 to-slate-800/80 backdrop-blur-2xl border-2 border-indigo-500/40 rounded-3xl p-12 shadow-2xl overflow-hidden hover:border-indigo-500/60 transition-all duration-500">
              <div className="absolute top-0 left-0 w-80 h-80 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-full blur-3xl -ml-40 -mt-40"></div>

              <div className="relative">
                <div className="flex items-center justify-between mb-10">
                  <h2 className="text-3xl font-black text-white flex items-center gap-4">
                    <div className="p-3 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-2xl shadow-xl">
                      <Settings className="w-7 h-7 text-white" />
                    </div>
                    <span className="bg-gradient-to-r from-indigo-200 via-purple-200 to-pink-200 bg-clip-text text-transparent">
                      Processing Settings Panel
                    </span>
                  </h2>
                  <button
                    onClick={() => setShowSettings(!showSettings)}
                    disabled={processing}
                    className="p-3.5 hover:bg-indigo-500/20 rounded-2xl transition-all border-2 border-indigo-500/40 hover:border-indigo-500/60 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Settings className={`w-7 h-7 text-indigo-400 transition-transform duration-500 ${showSettings ? 'rotate-180' : ''}`} />
                  </button>
                </div>

                {/* Settings Panel */}
                {showSettings && (
                  <div className="mb-10 p-10 bg-gradient-to-br from-slate-950/80 to-slate-900/80 rounded-3xl border-2 border-indigo-500/30 space-y-8 backdrop-blur-sm shadow-2xl animate-slideIn">
                    <div>
                      <label className="block text-base font-black text-indigo-200 mb-4 uppercase tracking-wide flex items-center gap-2">
                        <Zap className="w-5 h-5" />
                        Model Selection
                      </label>
                      <select
                        value={modelLayers}
                        onChange={(e) => setModelLayers(e.target.value)}
                        disabled={processing}
                        className="w-full bg-slate-900/90 border-2 border-indigo-500/40 rounded-2xl px-6 py-4 text-white font-bold text-lg hover:border-indigo-500/60 focus:border-indigo-500 focus:outline-none transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <option value="8">⚖️ 8 Layers - Balanced Quality (Recommended)</option>
                        <option value="16">✨ 16 Layers - Premium Quality</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-base font-black text-indigo-200 mb-4 uppercase tracking-wide flex items-center justify-between">
                        <span className="flex items-center gap-2">
                          <Gauge className="w-5 h-5" />
                          Resolution Selector
                        </span>
                        <span className="text-2xl font-black text-indigo-400">{resolution}×{resolution}</span>
                      </label>
                      <input
                        type="range"
                        min="256"
                        max="1024"
                        step="256"
                        value={resolution}
                        onChange={(e) => setResolution(Number(e.target.value))}
                        disabled={processing}
                        className="w-full h-4 accent-indigo-500 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                      />
                      <div className="flex justify-between text-sm text-indigo-300/80 font-bold mt-3">
                        <span>256px</span>
                        <span>512px</span>
                        <span>768px</span>
                        <span>1024px</span>
                      </div>
                    </div>

                    <div className="pt-6 border-t-2 border-indigo-500/30">
                      <label className="flex items-center gap-5 cursor-pointer p-6 bg-slate-900/60 rounded-2xl hover:bg-slate-900/80 transition-all border-2 border-indigo-500/30 hover:border-indigo-500/50">
                        <input
                          type="checkbox"
                          checked={useFp16}
                          onChange={(e) => setUseFp16(e.target.checked)}
                          disabled={processing}
                          className="w-6 h-6 accent-indigo-500 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                        />
                        <div className="flex-1">
                          <span className="text-lg font-black text-indigo-200 block">
                            FP16 GPU Acceleration Toggle
                          </span>
                          <span className="text-sm text-indigo-300/70 font-semibold mt-1 block">
                            Enables half-precision for 2x faster processing (GPU required) 🚀
                          </span>
                        </div>
                      </label>
                    </div>
                  </div>
                )}

                <button
                  onClick={handleProcess}
                  disabled={processing}
                  className="w-full bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-700 hover:via-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-black py-6 px-10 rounded-2xl flex items-center justify-center gap-4 transition-all duration-300 shadow-2xl hover:shadow-indigo-500/60 transform hover:scale-[1.02] active:scale-[0.98] text-xl"
                >
                  {processing ? (
                    <>
                      <Loader className="w-7 h-7 animate-spin" />
                      <span>Processing Video...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-7 h-7" />
                      <span>Start Dehazing Process</span>
                      <Sparkles className="w-6 h-6" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Progress */}
        {processing && status && (
          <div className="mb-10 animate-slideIn">
            <div className="relative bg-gradient-to-br from-slate-900/80 via-slate-900/70 to-slate-800/80 backdrop-blur-2xl border-2 border-pink-500/40 rounded-3xl p-12 shadow-2xl overflow-hidden">
              <div className="absolute bottom-0 right-0 w-80 h-80 bg-gradient-to-tl from-pink-500/20 to-purple-500/20 rounded-full blur-3xl -mr-40 -mb-40"></div>

              <div className="relative">
                <h2 className="text-3xl font-black mb-10 text-white flex items-center gap-4">
                  <div className="p-3 bg-gradient-to-br from-pink-600 to-purple-600 rounded-2xl shadow-xl">
                    <Loader className="w-7 h-7 text-white animate-spin" />
                  </div>
                  <span className="bg-gradient-to-r from-pink-200 via-purple-200 to-indigo-200 bg-clip-text text-transparent">
                    Real-time Progress Tracking
                  </span>
                </h2>

                {/* Live Frame Preview */}
                {livePreview.original && livePreview.dehazed && (
                  <div className="mb-10 p-8 bg-gradient-to-br from-slate-950/80 to-slate-900/80 rounded-3xl border-2 border-pink-500/30 backdrop-blur-sm shadow-2xl">
                    <h3 className="text-base font-black text-pink-300 mb-6 uppercase tracking-wider flex items-center gap-3">
                      <Film className="w-5 h-5" />
                      Preview Area - Before & After Comparison
                    </h3>
                    <div className="grid md:grid-cols-2 gap-8">
                      <div className="relative overflow-hidden rounded-2xl bg-black shadow-2xl border-2 border-purple-500/40 group">
                        <img
                          src={`data:image/jpeg;base64,${livePreview.original}`}
                          alt="Original frame"
                          className="w-full h-auto transform group-hover:scale-105 transition-transform duration-500"
                        />
                        <div className="absolute top-4 left-4 px-5 py-2.5 bg-gradient-to-r from-purple-600/95 to-pink-600/95 backdrop-blur-md rounded-2xl text-sm font-black text-white border-2 border-purple-400/60 shadow-xl">
                          Input (Hazy)
                        </div>
                        <div className="absolute bottom-4 right-4 px-5 py-2.5 bg-blue-600/95 backdrop-blur-md rounded-2xl text-sm font-black text-white shadow-xl">
                          {liveFps.toFixed(1)} FPS
                        </div>
                      </div>
                      <div className="relative overflow-hidden rounded-2xl bg-black shadow-2xl border-2 border-green-500/40 group">
                        <img
                          src={`data:image/jpeg;base64,${livePreview.dehazed}`}
                          alt="Dehazed frame"
                          className="w-full h-auto transform group-hover:scale-105 transition-transform duration-500"
                        />
                        <div className="absolute top-4 left-4 px-5 py-2.5 bg-gradient-to-r from-green-600/95 to-emerald-600/95 backdrop-blur-md rounded-2xl text-sm font-black text-white border-2 border-green-400/60 shadow-xl">
                          Output (Clear)
                        </div>
                        <div className="absolute bottom-4 right-4 px-5 py-2.5 bg-green-600/95 backdrop-blur-md rounded-2xl text-sm font-black text-white shadow-xl flex items-center gap-2">
                          <CheckCircle className="w-4 h-4" />
                          Enhanced
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <div className="space-y-10">
                  {/* Animated Horizontal Progress Bar */}
                  <div className="p-8 bg-gradient-to-br from-slate-950/80 to-slate-900/80 rounded-3xl border-2 border-pink-500/30 shadow-xl">
                    <div className="flex justify-between items-center mb-6">
                      <span className="text-pink-300 font-black text-xl flex items-center gap-3">
                        <Zap className="w-6 h-6" />
                        Overall Progress
                      </span>
                      <span className="text-pink-400 font-black text-3xl">
                        {(status.progress || 0).toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-5 bg-slate-950/90 rounded-full overflow-hidden shadow-inner border-2 border-slate-800">
                      <div
                        className="h-full bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 transition-all duration-300 rounded-full shadow-xl relative overflow-hidden"
                        style={{ width: `${status.progress || 0}%` }}
                      >
                        {/* Animated shimmer effect */}
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse"></div>
                      </div>
                    </div>
                    {/* Current Processing Stage */}
                    <div className="mt-6 flex items-center justify-center gap-3 text-pink-200">
                      <div className="w-2.5 h-2.5 bg-pink-400 rounded-full animate-pulse shadow-lg shadow-pink-400/70"></div>
                      <span className="text-base font-bold">
                        {status.current_frame > 0 && status.current_frame < (status.total_frames || 0)
                          ? `Processing frames... (${status.current_frame}/${status.total_frames})`
                          : status.progress === 0
                          ? 'Loading model...'
                          : status.progress === 100
                          ? 'Reconstructing video...'
                          : 'Processing frames...'}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                    <div className="p-6 bg-gradient-to-br from-slate-900/90 to-slate-800/90 rounded-2xl border-2 border-purple-500/30 hover:border-purple-500/50 transition-all shadow-xl hover:shadow-purple-500/30">
                      <div className="flex items-center gap-2 mb-3">
                        <Film className="w-5 h-5 text-purple-400" />
                        <p className="text-purple-300 text-xs font-black uppercase tracking-wide">Frames</p>
                      </div>
                      <p className="text-white font-black text-3xl mt-2">
                        {status.current_frame || 0} <span className="text-purple-400/60 text-xl">/ {status.total_frames || 0}</span>
                      </p>
                    </div>
                    <div className="p-6 bg-gradient-to-br from-slate-900/90 to-slate-800/90 rounded-2xl border-2 border-pink-500/30 hover:border-pink-500/50 transition-all shadow-xl hover:shadow-pink-500/30">
                      <div className="flex items-center gap-2 mb-3">
                        <Gauge className="w-5 h-5 text-pink-400" />
                        <p className="text-pink-300 text-xs font-black uppercase tracking-wide">Speed</p>
                      </div>
                      <p className="text-white font-black text-3xl mt-2">
                        {(status.fps || 0).toFixed(1)} <span className="text-pink-400/60 text-base">FPS</span>
                      </p>
                    </div>
                    <div className="p-6 bg-gradient-to-br from-slate-900/90 to-slate-800/90 rounded-2xl border-2 border-indigo-500/30 hover:border-indigo-500/50 transition-all shadow-xl hover:shadow-indigo-500/30">
                      <div className="flex items-center gap-2 mb-3">
                        <Clock className="w-5 h-5 text-indigo-400" />
                        <p className="text-indigo-300 text-xs font-black uppercase tracking-wide">Elapsed</p>
                      </div>
                      <p className="text-white font-black text-3xl mt-2">
                        {Math.floor(status.elapsed_time || 0)}<span className="text-indigo-400/60 text-base">s</span>
                      </p>
                    </div>
                    <div className="p-6 bg-gradient-to-br from-slate-900/90 to-slate-800/90 rounded-2xl border-2 border-cyan-500/30 hover:border-cyan-500/50 transition-all shadow-xl hover:shadow-cyan-500/30">
                      <div className="flex items-center gap-2 mb-3">
                        <Clock className="w-5 h-5 text-cyan-400" />
                        <p className="text-cyan-300 text-xs font-black uppercase tracking-wide">Remaining</p>
                      </div>
                      <p className="text-white font-black text-3xl mt-2">
                        ~{Math.floor(status.estimated_remaining || 0)}<span className="text-cyan-400/60 text-base">s</span>
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Results - Side by Side Comparison */}
        {status?.output_video_path && (
          <div className="mb-10 animate-slideIn">
            <div className="relative bg-gradient-to-br from-slate-900/80 via-slate-900/70 to-slate-800/80 backdrop-blur-2xl border-2 border-green-500/40 rounded-3xl p-12 shadow-2xl overflow-hidden">
              <div className="absolute top-0 left-0 w-80 h-80 bg-gradient-to-br from-green-500/20 to-emerald-500/20 rounded-full blur-3xl -ml-40 -mt-40"></div>

              <div className="relative">
                <div className="flex items-center justify-between mb-12 flex-wrap gap-6">
                  <h2 className="text-4xl font-black text-white flex items-center gap-4">
                    <div className="p-3 bg-gradient-to-br from-green-600 to-emerald-600 rounded-2xl shadow-xl">
                      <CheckCircle className="w-8 h-8 text-white" />
                    </div>
                    <span className="bg-gradient-to-r from-green-200 via-emerald-200 to-teal-200 bg-clip-text text-transparent">
                      Completion State - Success!
                    </span>
                  </h2>
                  <div className="flex gap-4">
                    <button
                      onClick={handleDownload}
                      className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-black py-4 px-8 rounded-2xl flex items-center gap-3 transition-all shadow-2xl hover:shadow-green-500/60 transform hover:scale-105 active:scale-95 text-lg"
                    >
                      <Download className="w-6 h-6" />
                      Download Dehazed Video
                    </button>
                    <button
                      onClick={handleReset}
                      className="bg-slate-800 hover:bg-slate-700 text-white font-black py-4 px-8 rounded-2xl flex items-center gap-3 transition-all border-2 border-slate-600 hover:border-slate-500 shadow-xl"
                    >
                      <Trash2 className="w-6 h-6" />
                      New Video
                    </button>
                  </div>
                </div>

                {/* Side by Side Video Comparison */}
                <div className="mb-10 p-3 bg-slate-950/60 rounded-3xl border-2 border-green-500/30 shadow-2xl">
                  <SplitScreenComparison
                    originalVideoRef={originalVideoRef}
                    dehazedVideoRef={dehazedVideoRef}
                    onPlayPause={handlePlayPause}
                    onTimeUpdate={handleTimeUpdate}
                    syncedPlay={syncedPlay}
                    onSyncToggle={setSyncedPlay}
                  />
                </div>

                {/* Statistics */}
                {status.statistics && (
                  <div className="p-10 bg-gradient-to-br from-slate-950/80 to-slate-900/80 rounded-3xl border-2 border-green-500/30 backdrop-blur-sm shadow-xl">
                    <h3 className="text-base font-black text-green-300 mb-8 uppercase tracking-wider flex items-center gap-3">
                      <Gauge className="w-5 h-5" />
                      Processing Statistics Report
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                      <div className="p-6 bg-gradient-to-br from-slate-900/90 to-slate-800/90 rounded-2xl border-2 border-green-500/30 hover:border-green-500/50 transition-all shadow-xl hover:shadow-green-500/30">
                        <p className="text-green-300 text-xs font-black uppercase tracking-wide mb-3">Total Frames</p>
                        <p className="text-white font-black text-3xl">{status.statistics.total_frames}</p>
                      </div>
                      <div className="p-6 bg-gradient-to-br from-slate-900/90 to-slate-800/90 rounded-2xl border-2 border-emerald-500/30 hover:border-emerald-500/50 transition-all shadow-xl hover:shadow-emerald-500/30">
                        <p className="text-emerald-300 text-xs font-black uppercase tracking-wide mb-3">Processing Time</p>
                        <p className="text-white font-black text-3xl">{status.statistics.total_time_seconds}<span className="text-emerald-400/60 text-base">s</span></p>
                      </div>
                      <div className="p-6 bg-gradient-to-br from-slate-900/90 to-slate-800/90 rounded-2xl border-2 border-cyan-500/30 hover:border-cyan-500/50 transition-all shadow-xl hover:shadow-cyan-500/30">
                        <p className="text-cyan-300 text-xs font-black uppercase tracking-wide mb-3">Average FPS</p>
                        <p className="text-white font-black text-3xl">{(status.statistics.average_fps).toFixed(2)}</p>
                      </div>
                      <div className="p-6 bg-gradient-to-br from-slate-900/90 to-slate-800/90 rounded-2xl border-2 border-purple-500/30 hover:border-purple-500/50 transition-all shadow-xl hover:shadow-purple-500/30">
                        <p className="text-purple-300 text-xs font-black uppercase tracking-wide mb-3">Avg Inference</p>
                        <p className="text-white font-black text-3xl">{(status.statistics.average_inference_ms).toFixed(1)}<span className="text-purple-400/60 text-base">ms</span></p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="relative bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 backdrop-blur-xl border-t-2 border-purple-500/30 mt-20">
        <div className="container mx-auto px-6 py-10 text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Sparkles className="w-6 h-6 text-purple-400" />
            <p className="text-purple-300 font-black text-lg">
              Video Dehazing using Deep Learning
            </p>
          </div>
          <p className="text-purple-400/80 text-base font-semibold">
            Powered by PyTorch, FastAPI & React
          </p>
          <p className="text-purple-500/60 text-sm mt-5 font-medium">
            © 2025 Final Year Engineering Project • All Rights Reserved
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
