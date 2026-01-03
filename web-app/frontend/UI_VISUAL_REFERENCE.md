# Video Dehazing UI - Quick Visual Reference

## 🎨 Color System

### Primary Colors

```
Deep Navy:    #0a0d1a  ███████  Background Base
Charcoal:     #141625  ███████  Background Mid
Deep Slate:   #0f1117  ███████  Background Dark
```

### Accent Colors

```
Purple:       #a855f7  ███████  Primary Actions / Tech
Pink:         #ec4899  ███████  Processing / Energy
Indigo:       #6366f1  ███████  Settings / Config
Green:        #22c563  ███████  Success / Complete
Emerald:      #10b981  ███████  Success Secondary
Cyan:         #06b6d4  ███████  Info / Stats
```

## 📐 Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│  🎬 Video Dehazing        [●] System Ready              │ HEADER
│     Deep Learning Powered                               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  📁 Video Upload Area                             │  │ UPLOAD
│  │  ┌─────────────────────────────────────────────┐  │  │ SECTION
│  │  │                                             │  │  │
│  │  │        ⬆️  Drag & Drop or Click            │  │  │
│  │  │           to Upload                         │  │  │
│  │  │                                             │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  │  [████████████████████] Upload & Continue         │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  ⚙️ Processing Settings Panel         [⚙️]       │  │ SETTINGS
│  │  ┌─────────────────────────────────────────────┐  │  │ SECTION
│  │  │  Model: [8 Layers ▼]                        │  │  │
│  │  │  Resolution: [━━━●━━━] 512×512              │  │  │
│  │  │  ☑️ FP16 GPU Acceleration                   │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  │  [▶️ Start Dehazing Process]                     │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  📊 Real-time Progress Tracking                   │  │ PROGRESS
│  │  ┌─────────────────┬─────────────────┐            │  │ SECTION
│  │  │  Hazy Frame     │  Clear Frame    │            │  │
│  │  │  [IMAGE]        │  [IMAGE]        │            │  │
│  │  └─────────────────┴─────────────────┘            │  │
│  │  Overall Progress: 67.5%                          │  │
│  │  [██████████████░░░░░░░░░░░]                      │  │
│  │  Processing frames... (135/200)                   │  │
│  │  ┌──────┬──────┬──────┬──────┐                    │  │
│  │  │135/  │12.3  │45s   │~22s  │  Statistics       │  │
│  │  │200   │FPS   │      │      │                    │  │
│  │  └──────┴──────┴──────┴──────┘                    │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  ✅ Completion State - Success!                   │  │ RESULTS
│  │         [⬇️ Download] [🗑️ New Video]              │  │ SECTION
│  │  ┌─────────────────┬─────────────────┐            │  │
│  │  │  Original       │  Dehazed        │            │  │
│  │  │  [VIDEO]        │  [VIDEO]        │            │  │
│  │  └─────────────────┴─────────────────┘            │  │
│  │  Processing Statistics Report:                    │  │
│  │  [200 frames | 16.2s | 12.3 FPS | 81.2ms]        │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  ✨ Video Dehazing using Deep Learning                  │ FOOTER
│     Powered by PyTorch, FastAPI & React                 │
└─────────────────────────────────────────────────────────┘
```

## 🎭 Component States

### Upload Section

```
State 1: Empty
┌────────────────────────────┐
│      ⬆️ [64px icon]        │
│  Drag & Drop or Click      │
│  MP4, AVI, MOV • 500MB     │
└────────────────────────────┘

State 2: File Selected
┌────────────────────────────┐
│    🎥 my_video.mp4         │
│  [Upload & Continue] →     │
└────────────────────────────┘

State 3: Uploading
┌────────────────────────────┐
│    ⏳ Uploading... 45%     │
│  [████████░░░░░░░░░░░]     │
└────────────────────────────┘
```

### Progress Bar States

```
Loading Model (0%)
[░░░░░░░░░░░░░░░░░░░░] 0.0%
● Loading model...

Processing (45%)
[█████████░░░░░░░░░░░] 45.0%
● Processing frames... (90/200)

Reconstructing (100%)
[████████████████████] 100%
● Reconstructing video...
```

### Settings Panel

```
Collapsed:
⚙️ Processing Settings Panel    [⚙️]

Expanded:
⚙️ Processing Settings Panel    [⚙️↻]
┌─────────────────────────────────┐
│ ⚡ MODEL SELECTION              │
│ [▼ 8 Layers - Balanced]         │
│                                 │
│ 📊 RESOLUTION SELECTOR          │
│ [━━━━━●━━━] 512×512             │
│                                 │
│ ☑️ FP16 GPU Acceleration Toggle │
│ Half-precision for 2x speed     │
└─────────────────────────────────┘
```

## 🎬 Animations Showcase

### Entry Animations

```
slideIn:     ↓ fade + move from top (0.5s)
fadeIn:      ○ → ● opacity only (0.3s)
scaleIn:     ⊙ → ● scale + fade (0.4s)
```

### Continuous Animations

```
pulse:       ● → ◉ → ● gentle throb (2s infinite)
spin:        ↻ rotation (1s infinite)
float:       ↕️ vertical oscillation (3s infinite)
shimmer:     → sweep across (2s infinite)
```

### Hover Effects

```
Button:      ▭ → ▬ (scale 102%, -2px up)
Card:        ▢ → ▣ (scale 105%, -4px up, glow)
Image:       ▭ → ▬ (scale 105%)
```

## 📊 Typography Scale

```
Display (Header):
  5xl: █████ 48px  "Video Dehazing"
  4xl: ████ 36px   Section Headers

Title (Subheader):
  3xl: ███ 30px    Card Titles
  2xl: ██ 24px     Subsection Titles
  xl:  █ 20px      Large Labels

Body:
  lg:  ═ 18px      Important Text
  base:─ 16px      Standard Text
  sm:  ─ 14px      Secondary Text
  xs:  ─ 12px      Labels, Captions
```

## 🎯 Icon Sizes

```
Mega:    █████  64px  Upload Icon (main)
Large:   ████   48px  Section Icons
Medium:  ███    32px  (unused)
Regular: ██     24px  Action Buttons
Small:   █      16px  Inline Icons
Tiny:    ▪      12px  Status Indicators
```

## 🔲 Spacing System

```
Padding Scale:
  p-3:   12px   Compact
  p-4:   16px   Tight
  p-6:   24px   Cozy
  p-8:   32px   Standard
  p-10:  40px   Comfortable
  p-12:  48px   Spacious

Gap Scale:
  gap-2:  8px   Tight
  gap-3:  12px  Close
  gap-4:  16px  Standard
  gap-6:  24px  Comfortable
  gap-8:  32px  Loose
```

## 🎪 Border Radii

```
Card Borders:
  rounded-2xl:  16px  Large Cards
  rounded-3xl:  24px  Main Sections

Button Borders:
  rounded-xl:   12px  Small Buttons
  rounded-2xl:  16px  Large Buttons

Badges/Pills:
  rounded-full: 999px Indicators
```

## 🌟 Shadow Depths

```
Level 1: shadow-lg    ▭ Hover State
Level 2: shadow-xl    ▬ Active Elements
Level 3: shadow-2xl   ▣ Main Cards
Glow:    shadow-glow  ◉ Accent Elements
```

## 📱 Responsive Breakpoints

```
Mobile:  < 768px   │ 1 Column Layout
                   │ Stacked Components
                   │ Full-width Buttons
                   ▼
Tablet:  768-1024  │ 2 Column Grid
                   │ Adapted Spacing
                   │ Touch-friendly
                   ▼
Desktop: > 1024px  │ Full Layout
                   │ Side-by-side
                   │ Hover Effects
```

## 🎨 Gradient Combinations

### Background Gradients

```
Main:    from-[#0a0d1a] via-[#141625] to-[#0f1117]
Header:  from-slate-950 via-slate-900 to-slate-950
Card:    from-slate-900/80 via-slate-900/70 to-slate-800/80
```

### Accent Gradients

```
Purple:  from-purple-600 via-pink-600 to-indigo-600
Green:   from-green-600 to-emerald-600
Text:    from-purple-200 via-pink-200 to-indigo-200
```

## 🎯 Call-to-Action Hierarchy

```
Primary:     [▶️ Start Dehazing Process]     Purple Gradient
Secondary:   [⬇️ Download Dehazed Video]     Green Gradient
Tertiary:    [🗑️ New Video]                  Gray/Slate
Disabled:    [⏳ Processing...]              50% Opacity
```

## ✨ Success

This UI design successfully combines:

- ✅ Modern dark aesthetics
- ✅ Clear visual hierarchy
- ✅ Smooth animations
- ✅ Professional appearance
- ✅ Research-grade presentation
- ✅ Engineering project quality
- ✅ Production-ready polish

**Perfect for final-year project demonstrations!**
