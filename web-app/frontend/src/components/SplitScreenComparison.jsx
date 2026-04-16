import { useState, useRef, useEffect } from 'react';

export function SplitScreenComparison({ originalVideoRef, dehazedVideoRef, onPlayPause, onTimeUpdate, syncedPlay, onSyncToggle }) {
  const [sliderPosition, setSliderPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef(null);
  const safeSlider = Math.min(100, Math.max(1, sliderPosition));

  // Handle slider drag
  const handleMouseDown = () => setIsDragging(true);

  useEffect(() => {
    const handleMouseUp = () => setIsDragging(false);
    const handleMouseMove = (e) => {
      if (!isDragging || !containerRef.current) return;

      const container = containerRef.current;
      const rect = container.getBoundingClientRect();
      const newPosition = ((e.clientX - rect.left) / rect.width) * 100;
      
      if (newPosition >= 0 && newPosition <= 100) {
        setSliderPosition(newPosition);
      }
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  return (
    <div className="space-y-8">
      {/* Split Screen Comparison */}
      <div 
        ref={containerRef}
        className="relative w-full overflow-hidden rounded-2xl bg-black shadow-2xl border-2 border-purple-500/30 group cursor-col-resize"
        style={{ paddingBottom: '56.25%' }}
      >
        {/* Original Video - Full Width */}
        <div className="absolute inset-0 w-full h-full">
          <video
            ref={originalVideoRef}
            controls
            onPlay={(e) => onPlayPause?.(e, true)}
            onPause={(e) => onPlayPause?.(e, true)}
            onTimeUpdate={(e) => onTimeUpdate?.(e, true)}
            className="w-full h-full object-cover bg-black"
          />
          <div className="absolute top-4 left-4 px-4 py-2 bg-gradient-to-r from-purple-600/90 to-pink-600/90 backdrop-blur-md rounded-xl text-xs font-bold text-white border-2 border-purple-400/50 shadow-lg">
            Original (Hazy)
          </div>
        </div>

        {/* Dehazed Video - Clipped */}
        <div 
          className="absolute inset-0 w-full h-full overflow-hidden"
          style={{ width: `${safeSlider}%` }}
        >
          <video
            ref={dehazedVideoRef}
            controls
            onPlay={(e) => onPlayPause?.(e, false)}
            onPause={(e) => onPlayPause?.(e, false)}
            onTimeUpdate={(e) => onTimeUpdate?.(e, false)}
            className="absolute inset-0 w-full h-full object-cover bg-black"
            style={{ width: `${(100 / safeSlider) * 100}%` }}
          />
          <div className="absolute top-4 left-4 px-4 py-2 bg-gradient-to-r from-green-600/90 to-emerald-600/90 backdrop-blur-md rounded-xl text-xs font-bold text-white border-2 border-green-400/50 shadow-lg">
            Dehazed (Clear)
          </div>
        </div>

        {/* Slider Handle */}
        <div
          className="absolute top-0 bottom-0 w-1.5 bg-gradient-to-b from-purple-400 via-pink-400 to-indigo-400 cursor-col-resize hover:w-3 transition-all shadow-2xl"
          style={{ left: `${safeSlider}%`, transform: 'translateX(-50%)' }}
          onMouseDown={handleMouseDown}
        >
          {/* Handle Thumb */}
          <div className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 -ml-5 -mt-5 w-10 h-10">
            <div className="absolute inset-0 bg-gradient-to-r from-purple-500 via-pink-500 to-indigo-500 rounded-full shadow-2xl opacity-0 group-hover:opacity-100 transition-opacity blur-sm" />
            <div className="absolute inset-1 bg-slate-900 rounded-full border-2 border-pink-400 shadow-lg" />
            <div className="absolute inset-2 flex items-center justify-center">
              <div className="flex gap-1">
                <div className="w-1 h-4 bg-pink-400 rounded-full" />
                <div className="w-1 h-4 bg-pink-400 rounded-full" />
              </div>
            </div>
          </div>
        </div>

        {/* Position Label */}
        <div className="absolute top-5 left-1/2 transform -translate-x-1/2 px-5 py-2.5 bg-gradient-to-r from-purple-600/90 to-pink-600/90 backdrop-blur-md rounded-xl text-sm font-black text-white border-2 border-pink-400/50 pointer-events-none shadow-2xl">
          {safeSlider.toFixed(0)}%
        </div>
      </div>

      {/* Sync Control */}
      <div className="flex items-center justify-center gap-6 flex-wrap">
        <label className="flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-slate-800/80 to-slate-900/80 rounded-xl border-2 border-purple-500/30 hover:border-purple-500/50 transition-all cursor-pointer shadow-lg hover:shadow-purple-500/20">
          <input
            type="checkbox"
            checked={syncedPlay}
            onChange={(e) => {
              onSyncToggle?.(e.target.checked);
            }}
            className="w-5 h-5 accent-purple-500"
          />
          <span className="text-sm font-bold text-purple-300">Synchronized Playback</span>
        </label>
        
        <div className="hidden md:flex items-center gap-2 text-xs text-purple-300/70 px-4 py-2 bg-slate-800/60 rounded-xl border-2 border-purple-500/20 font-semibold">
          <span className="text-lg">💡</span>
          <span>Drag the slider to compare</span>
        </div>
      </div>

      {/* Comparison Tips */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="p-5 bg-gradient-to-br from-purple-900/40 to-pink-900/40 border-2 border-purple-500/30 rounded-2xl backdrop-blur-sm">
          <p className="text-purple-300 font-bold mb-2 text-sm">Left Side (Hazy)</p>
          <p className="text-purple-200/70 text-xs">Original video with haze/fog</p>
        </div>
        <div className="p-5 bg-gradient-to-br from-green-900/40 to-emerald-900/40 border-2 border-green-500/30 rounded-2xl backdrop-blur-sm">
          <p className="text-green-300 font-bold mb-2 text-sm">Right Side (Clear)</p>
          <p className="text-green-200/70 text-xs">Dehazed output after processing</p>
        </div>
      </div>
    </div>
  );
}
