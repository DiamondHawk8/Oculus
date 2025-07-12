# Oculus

A **modern, high-performance** desktop media manager and viewer built with **PySide6**.

---

## Project Status

| Phase                               | State       | Key Deliverables                                                                                                                                                          |
|-------------------------------------|-------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **1 — UI Skeleton**                 | Completed   | Border-less dark shell, custom window grips, page scaffolding                                                                                                             |
| **2 — Core Metadata & Thumbnailing**| Completed   | Threaded folder scanner, SQLite schema (`media`, `tags`, `roots`), thumbnail cache                                                                                        |
| **3 — Image Workflows**             | Completed   | Tabs per folder, Browser-style history, Fullscreen viewer (zoom + pan), Sorting, Variants, Unified Metadata dialog, Rename & Move queue, Comment system with drag-reorder |
| **4 — Rich Media Support**          | In Progress | GIF playback (`QMovie`), Video playback (`QMediaPlayer` / PyAV), Audio (stretch goal)                                                                                     |
| **5 — Polish & Packaging**          | Planned     | Session save/load, Commit/rollback move queue, Installers/portable build, Performance sweeps                                                                              |
| **6 — Experimental/Cloud**          | Planned     | PostgreSQL backend, Cloud sync hooks, AI tagging suggestions                                                                                                              |

---

## Feature Checklist

### **Completed**

- Asynchronous folder ingest (JPEG/PNG) with deep-tree scan
- SQLite backend for paths, roots, tags & favourites
- Background thumbnail generation via `QThreadPool`
- Gallery view  
  - List/grid toggle, dynamic icon sizing  
  - Browser-like Back/Forward navigation  
  - Tabs per sub-folder (Ctrl+W, Ctrl+Tab, middle-click open)  
  - **Drag-move to "Move to..."
- Fullscreen image viewer  
  - Fit/zoom (wheel, ±) & double-click toggle  
  - Left/Right navigation through current list  
  - Basic click-drag panning  
  - Comments panel (add / edit / delete, live sync, drag-reorder with DB persistence)
- Variants  
  - Auto-stack detection, collapse/expand, visual stack badge  
  - In-viewer Up/Down variant cycling
- Unified Metadata dialog (Tags, Attributes, Zoom/Pan presets)  
  - Batch scope (this / selected / folder), variant inclusion  
  - Zoom/Pan presets with default & hotkey support
- Rename dialog + safe overwrite + undo

### **In Progress (Phase 4)**

- GIF playback (`QMovie`)
- Video playback (`QMediaPlayer` / PyAV)
- Optional audio preview

### **Planned (Phase 5)**

- Session save/load (open tabs + per-tab view state)
- Performance sweeps, memory guardrails
- Windows / MSIX + macOS dmg packaging

### **Planned (Phase 6)**

- PostgreSQL backend option
- Cloud sync / multi-user hooks
- AI-powered tagging & duplicate detection

---

## Screenshots  *(Phase 3 — UI subject to further polish)*

| Gallery                                      | Search                                  | Media View                             |
|----------------------------------------------|-----------------------------------------|----------------------------------------|
| ![Gallery view](docs/screens/gallery.png)    | ![Search view](docs/screens/search.png) | ![Media view](docs/screens/viewer.png) |

---

## Immediate Milestones

1. **Complete Phase 4**  
   - Integrate GIF playback pipeline  
   - Prototype video playback with `QMediaPlayer` / PyAV
2. **Phase 5**  
   - Session save/load prototype (tabs, view state, panel positions)
   - First end-to-end performance sweep

---
