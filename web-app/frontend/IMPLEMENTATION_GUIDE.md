# Video Dehazing UI - Implementation Guide

## 🚀 Quick Start

### Prerequisites

```bash
Node.js 16+ and npm installed
```

### Installation

```bash
cd web-app/frontend
npm install
```

### Development

```bash
npm run dev
```

### Production Build

```bash
npm run build
npm run preview
```

## 📁 File Structure

```
frontend/
├── src/
│   ├── App.jsx                    # Main component (updated)
│   ├── App.css                    # Custom styles (updated)
│   ├── components/
│   │   └── SplitScreenComparison.jsx
│   ├── services/
│   │   └── api.js
│   └── main.jsx
├── tailwind.config.js             # Tailwind config (updated)
├── vite.config.js
├── package.json
├── index.html
├── UI_DESIGN_DOCUMENTATION.md     # Complete design specs
└── UI_VISUAL_REFERENCE.md         # Visual quick reference
```

## 🎨 Key Design Features Implemented

### 1. Modern Dark Theme

- **Background**: Deep navy (#0a0d1a) with gradient overlays
- **Cards**: Glassmorphism with backdrop-blur
- **Borders**: Subtle gradients with glow effects
- **Grid Overlay**: CSS pattern for depth

### 2. Professional Header

```jsx
<header
  className="bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 
                   backdrop-blur-xl border-b-2 border-purple-500/30 sticky top-0"
>
  {/* Title: "Video Dehazing" */}
  {/* Subtitle: "Deep Learning Powered" */}
  {/* Status: "System Ready" */}
</header>
```

### 3. Card-Based Sections

All major sections follow this pattern:

- Rounded corners (24px)
- Gradient backgrounds
- 2px colored borders
- Backdrop blur
- Hover transitions

### 4. Upload Area

- **Drag-and-drop support**: HTML5 file API
- **Visual feedback**: Border color changes on hover
- **Progress bar**: Animated gradient with shimmer
- **Disabled state**: During processing

### 5. Settings Panel

- **Collapsible**: Toggle with rotation animation
- **Model Selection**: Dropdown with 3 options
  - 4 Layers (Fastest)
  - 8 Layers (Recommended)
  - 16 Layers (Best Quality)
- **Resolution Slider**: 256px → 1024px in 256px steps
- **FP16 Toggle**: Checkbox for GPU acceleration

### 6. Progress Tracking

- **Horizontal Progress Bar**:
  - Gradient fill (pink → purple → indigo)
  - Shimmer animation overlay
  - Large percentage display (32px)
- **Processing Stage**:
  - "Loading model..." (0%)
  - "Processing frames... (X/Y)" (1-99%)
  - "Reconstructing video..." (100%)
- **Live Preview**:
  - Side-by-side frames
  - Before (hazy) vs After (clear)
  - Real-time FPS counter
- **Statistics Grid**:
  - 4 cards: Frames, Speed, Elapsed, Remaining
  - Color-coded borders
  - Large numbers with small units

### 7. Completion State

- **Success Message**: Large green checkmark
- **Download Button**: Green gradient, prominent
- **New Video Button**: Secondary gray style
- **Video Comparison**: Side-by-side player
- **Statistics Report**: Final processing metrics

## 🎭 Animation Details

### Entry Animations

Every section fades in with `animate-slideIn`:

```css
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

### Continuous Animations

- **Pulse**: Status indicators, gradients (2s)
- **Spin**: Loading icons (1s)
- **Shimmer**: Progress bar overlay (2s)

### Interaction Animations

- **Hover**: Scale 102-105%, translate up -2 to -4px
- **Active**: Scale 98%
- **Focus**: 3px purple outline

## 🎨 Color Usage Guide

### Section Color Coding

```
Upload:      Purple (#a855f7)
Settings:    Indigo (#6366f1)
Progress:    Pink (#ec4899)
Completion:  Green (#22c563)
```

### Gradient Patterns

```jsx
// Button Gradient
className="bg-gradient-to-r from-purple-600 via-pink-600 to-indigo-600"

// Text Gradient
className="bg-gradient-to-r from-purple-200 via-pink-200 to-indigo-200
           bg-clip-text text-transparent"

// Card Background
className="bg-gradient-to-br from-slate-900/80 via-slate-900/70 to-slate-800/80"
```

## 📊 Typography Implementation

### Font Weights

```jsx
font - black(900); // Headers, important numbers
font - bold(700); // Buttons, labels
font - semibold(600); // Descriptions
font - medium(500); // Body text
```

### Sizes

```jsx
text-5xl      (48px)  // Main header
text-4xl      (36px)  // Success message
text-3xl      (30px)  // Section headers
text-2xl      (24px)  // Large numbers
text-xl       (20px)  // Subheaders
text-lg       (18px)  // Buttons
text-base     (16px)  // Body
text-sm       (14px)  // Secondary
text-xs       (12px)  // Labels
```

## 🔧 Key Components

### Progress Bar Component

```jsx
<div className="h-5 bg-slate-950/90 rounded-full overflow-hidden">
  <div
    className="h-full bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 
               transition-all duration-300 relative overflow-hidden"
    style={{ width: `${progress}%` }}
  >
    <div
      className="absolute inset-0 bg-gradient-to-r from-transparent 
                    via-white/30 to-transparent animate-pulse"
    />
  </div>
</div>
```

### Stat Card Component

```jsx
<div
  className="p-6 bg-gradient-to-br from-slate-900/90 to-slate-800/90 
                rounded-2xl border-2 border-purple-500/30 
                hover:border-purple-500/50 transition-all shadow-xl"
>
  <div className="flex items-center gap-2 mb-3">
    <Icon className="w-5 h-5 text-purple-400" />
    <p className="text-purple-300 text-xs font-black uppercase">Label</p>
  </div>
  <p className="text-white font-black text-3xl">
    {value} <span className="text-purple-400/60 text-base">{unit}</span>
  </p>
</div>
```

### Button Component

```jsx
<button
  onClick={handler}
  disabled={disabled}
  className="w-full bg-gradient-to-r from-purple-600 via-pink-600 to-indigo-600 
             hover:from-purple-700 hover:via-pink-700 hover:to-indigo-700 
             disabled:opacity-50 disabled:cursor-not-allowed 
             text-white font-black py-6 px-10 rounded-2xl 
             flex items-center justify-center gap-4 
             transition-all duration-300 shadow-2xl 
             hover:shadow-purple-500/60 
             transform hover:scale-[1.02] active:scale-[0.98] 
             text-xl"
>
  <Icon className="w-7 h-7" />
  <span>Button Text</span>
</button>
```

## 🎯 State Management

### Upload States

```javascript
const [selectedFile, setSelectedFile] = useState(null);
const [uploading, setUploading] = useState(false);
const [uploadProgress, setUploadProgress] = useState(0);
```

### Processing States

```javascript
const [jobId, setJobId] = useState(null);
const [processing, setProcessing] = useState(false);
const [status, setStatus] = useState(null);
```

### Settings States

```javascript
const [modelLayers, setModelLayers] = useState("8");
const [resolution, setResolution] = useState(512);
const [useFp16, setUseFp16] = useState(false);
const [showSettings, setShowSettings] = useState(false);
```

### Preview States

```javascript
const [livePreview, setLivePreview] = useState({
  original: null,
  dehazed: null,
});
const [liveFps, setLiveFps] = useState(0);
```

## 🔄 User Flow

```
1. UPLOAD
   ├─ User selects/drops video file
   ├─ File validation (type, size)
   ├─ Display filename
   └─ Click "Upload & Continue"
       ├─ Show progress bar (0-100%)
       └─ On complete → Show Settings

2. SETTINGS
   ├─ User configures (or uses defaults)
   │   ├─ Model: 4/8/16 layers
   │   ├─ Resolution: 256-1024px
   │   └─ FP16: on/off
   └─ Click "Start Dehazing Process"
       └─ Controls disabled → Show Progress

3. PROCESSING
   ├─ Connect WebSocket for updates
   ├─ Display live preview frames
   ├─ Update progress bar (0-100%)
   ├─ Show current stage text
   └─ Update statistics cards
       └─ On complete → Show Results

4. COMPLETION
   ├─ Display success message
   ├─ Show video comparison
   ├─ Display final statistics
   └─ Provide actions
       ├─ Download dehazed video
       └─ Start new video (reset)
```

## 🐛 Error Handling

### Error Display

```jsx
{
  error && (
    <div
      className="p-5 bg-gradient-to-r from-red-900/50 to-rose-900/50 
                  border-2 border-red-500/50 rounded-2xl 
                  flex items-start gap-4 animate-slideIn"
    >
      <AlertCircle className="w-6 h-6 text-red-400" />
      <div>
        <p className="font-bold text-red-200 text-lg">Error Title</p>
        <p className="text-red-300/90 text-sm">{error}</p>
      </div>
    </div>
  );
}
```

### Common Errors

- Invalid file type
- File too large (>500MB)
- Upload failed
- Processing failed
- Network timeout

## 🎨 Customization

### Changing Primary Color

Edit `tailwind.config.js`:

```javascript
extend: {
  colors: {
    primary: '#a855f7',  // Change this
  }
}
```

### Adjusting Animation Speed

Edit `App.css`:

```css
.animate-slideIn {
  animation: slideIn 0.5s...; /* Change duration */
}
```

### Modifying Card Styles

Edit card className:

```jsx
className="bg-gradient-to-br from-YOUR-COLOR/80
           border-2 border-YOUR-COLOR/40
           hover:border-YOUR-COLOR/60"
```

## 📱 Responsive Behavior

### Mobile (<768px)

- Single column layout
- Full-width components
- Stacked video previews
- 2×2 statistics grid
- Larger touch targets

### Tablet (768-1024px)

- Adapted grid layouts
- Side-by-side when possible
- Adjusted spacing
- Touch-friendly controls

### Desktop (>1024px)

- Full layout as designed
- Hover effects enabled
- Keyboard shortcuts
- Optimal spacing

## ⚡ Performance Tips

1. **Lazy Load Images**: Use loading="lazy" for preview frames
2. **Optimize Animations**: Use CSS transforms (GPU accelerated)
3. **Debounce Inputs**: For slider, use debounce (300ms)
4. **Memoize Components**: Use React.memo for expensive renders
5. **Code Splitting**: Dynamic imports for heavy components

## 🔐 Accessibility

### Keyboard Navigation

- Tab order follows visual flow
- All interactive elements focusable
- Escape key closes modals
- Enter/Space activates buttons

### Screen Readers

- Semantic HTML (header, main, footer, section)
- ARIA labels on icons
- Alt text on images
- Status announcements

### Contrast

- All text meets WCAG AA (4.5:1)
- Interactive elements clearly visible
- Focus indicators prominent

## 🧪 Testing

### Visual Regression

1. Upload section (empty, file selected, uploading)
2. Settings panel (collapsed, expanded)
3. Progress tracking (various percentages)
4. Completion state

### Interaction Testing

1. File upload flow
2. Settings modification
3. Progress updates
4. Download/reset actions

### Responsive Testing

1. Mobile viewport (375px)
2. Tablet viewport (768px)
3. Desktop viewport (1920px)

## 📚 Resources

### Icons

- Library: Lucide React
- Size: 16-64px range
- Style: Outline, 2px stroke

### Fonts

- System fonts (sans-serif stack)
- Weights: 400, 500, 600, 700, 900

### Colors

- Tailwind CSS default palette
- Custom values in config

## 🎉 Final Checklist

- ✅ Dark navy background with gradients
- ✅ Clear visual hierarchy
- ✅ Card-based layout
- ✅ Header with title and subtitle
- ✅ Video upload with drag-and-drop
- ✅ Processing settings panel (model, resolution, FP16)
- ✅ Real-time progress bar
- ✅ Percentage indicator
- ✅ Current processing stage
- ✅ Before-and-after preview
- ✅ Success message and download button
- ✅ Disabled controls during processing
- ✅ Smooth transitions and animations
- ✅ Modern typography
- ✅ Rounded corners
- ✅ Soft shadows

## 🚀 Deployment

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

### Deploy to Vercel/Netlify

```bash
# Vercel
vercel --prod

# Netlify
netlify deploy --prod
```

---

**Design Status**: ✅ Complete and Production-Ready
**Last Updated**: January 2025
**Version**: 2.0.0
