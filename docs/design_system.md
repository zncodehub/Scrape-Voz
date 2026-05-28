# Design System - Voz Thread Scraper & Explorer

This document outlines the visual language, color palettes, UI tokens, and component guidelines for the Voz Thread Scraper & Explorer application. It ensures visual consistency across the control panel, central explorer, and thread viewers.

---

## 1. Design Philosophy
The visual direction combines **Classic XenForo brand aesthetics** with a **Modern Retro-Glassmorphic Developer layout**. 
*   **Web Control Panel (`scraper_ui.html`)**: Sleek, immersive dark developer environment with glassmorphic cards, glowing status nodes, and neon-themed terminal outputs.
*   **Explorer & Viewer (`index.html` & `thread_viewer.html`)**: Polished XenForo clone, offering a familiar, readable layout in both soft-blue Light theme and deep-slate Dark theme.

---

## 2. Color Palette & Theme Tokens

### A. Scraper Control Panel Dark Slate Theme
*   **Base Background**: HSL Tailored Gradient `#0f172a` (Dark Slate Blue) to `#1e1b4b` (Deep Indigo).
*   **Card Background**: `#1e293b` (Slate 800) with a semi-transparent glass border `rgba(51, 65, 85, 0.5)`.
*   **Accent Color**: `#38bdf8` (Cyan 400) - represents active processes and primary links.
*   **Success Color**: `#10b981` (Emerald 500) - indicates successful completions.
*   **Warning Color**: `#f59e0b` (Amber 500) - indicates active scraping/staggering states.
*   **Error Color**: `#ef4444` (Red 500) - indicates failed page loads or terminations.
*   **Console Output Background**: `#090d16` (Deep Midnight Black).

### B. Explorer & Viewer Themes (XenForo Match)

```css
/* LIGHT THEME (XenForo Light Blue) */
:root {
    --bg-gradient: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    --panel-bg: #ffffff;
    --header-bg: #185886;              /* Classic XenForo Deep Blue */
    --header-text: #ffffff;
    --text-color: #141414;
    --text-muted: #64748b;
    --border-color: #e2e8f0;
    --accent-color: #2187c1;            /* Standard Forum Blue Links */
    --accent-hover: #176594;
    --table-header-bg: #f8fafc;
    --row-hover-bg: #f1f5f9;
    --badge-bg: #e0f2fe;
    --badge-text: #0369a1;
}

/* DARK THEME (XenForo Dark Slate) */
[data-theme="dark"] {
    --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    --panel-bg: #1e293b;
    --header-bg: #0f172a;
    --header-text: #f1f5f9;
    --text-color: #f1f5f9;
    --text-muted: #94a3b8;
    --border-color: #334155;
    --accent-color: #38bdf8;            /* Retro Cyan Links */
    --accent-hover: #0ea5e9;
    --table-header-bg: #1e293b;
    --row-hover-bg: #334155;
    --badge-bg: #0c4a6e;
    --badge-text: #38bdf8;
}
```

---

## 3. Typography
The system imports premium typography from Google Fonts:
*   **Primary Copy**: `'Inter', sans-serif` - clean, geometric sans-serif optimized for long-form reading, user metadata, and data tables.
*   **Terminal Outputs**: `'Fira Code', monospace` - monospaced font equipped with clean spacing, used exclusively for the real-time terminal widget.

---

## 4. Key UI Elements & Controls

### A. The Monospaced Terminal Viewport
*   Uses a midnight black box (`#090d16`) with inset shadows to give a retro console depth.
*   Log lines are parsed dynamically for formatting classes:
    *   `[Info]`, `Detecting...` -> Cyan (`#38bdf8`)
    *   `[Warning]` -> Amber (`#f59e0b`)
    *   `[Error]` -> Red (`#ef4444`)
    *   `scraped successfully`, `complete!` -> Emerald (`#10b981`)
    *   System overheads -> Dim gray (`#475569`)

### B. Interactive Switches & Sliders
*   Custom switches with smooth 300ms transitions (`transition: .3s`).
*   Active state toggles the slider from steel-gray (`#334155`) to vibrant Cyan (`var(--accent-color)`), shifting the toggle knob `20px` to the right.

### C. Glassmorphic Table Rows
*   The thread explorer registry lists rows inside a bordered card.
*   Rows feature dynamic `:hover` states changing the background to HSL tinted slate (`var(--row-hover-bg)`), with table elements adapting automatically to light/dark themes.
*   A custom red-accented `btn-delete` provides a prominent but non-intrusive action path, shifting to vibrant red (`#ef4444`) and spawning glowing shadows upon hover.

### D. Image Gallery Card Grid
*   Features a responsive flex-grid with card elements representing comments.
*   Card headers crop the first embedded post image to a standard `3:2` aspect ratio cover, adding a semi-transparent absolute badge (e.g. `+3 ảnh`) in the top right.
*   Card footers place reactions inline, using smaller avatars and reaction emojis for high density.
