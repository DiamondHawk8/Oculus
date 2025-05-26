# Oculus
A modern, high-performance media viewer built with **PySide6**

---

## Project Status

| Phase                           | Date        | Highlight                                         |
|---------------------------------|-------------|---------------------------------------------------|
| **1 — UI Skeleton**             | Completed   | Frameless Dracula-styled shell, custom grips      |
| **2 — Metadata & Basic Media**  | Completed   | Async folder scan, SQLite schema, thumbnail cache |
| **3 — Concurrency & GIF/Video** | In Progress |                                                   |

---

## Feature Checklist

- [x] **Custom PySide6 GUI** with Dracula theme and borderless window resizing grips
- [x] **Image ingestion** (JPEG, PNG) from deeply nested folders with threaded scanning  
- [x] **SQLite integration** for paths, tags, and favorites (Phase 2 DB schema)  
- [ ] **PostgreSQL** support (planned Phase 6 deployment)  
- [ ] **Tagging UI** (context-menu / modal)  
- [x] **Background loading** with `QThreadPool` / `QtConcurrent` for thumbnails  
- [ ] **GIF playback** with pause / play  
- [ ] **Video playback** via `QMediaPlayer`  
- [ ] **Group / folder assignment** and batch tagging tools  
- [ ] **Rename utility** synced to DB + filesystem  
- [ ] **Advanced features**: comments, annotations, FTS search, cloud sync



---

## Screenshots

| Gallery View                              | Search Results |
|-------------------------------------------|----------------|
| ![Gallery view](docs/screens/gallery.png) | ![Search view](docs/screens/search.png) |

> *Screenshots captured after Phase 2 - UI is subject to revision.*

---

## Roadmap (next milestone)

1. **Modal image viewer** with ← / → navigation and pre-fetch  
2. **GIF & video support** (Qt `QMovie` + `QMediaPlayer`)  
3. **Tag UX** – add / remove via context-menu  
4. **Performance guardrails** – lazy thumbnails for off-screen items  
