import { useState, useRef, useEffect } from "react";
import "./App.css";

// ── File type categories ──────────────────────
const CATEGORIES = {
  Images:      { icon: "🖼",  color: "#ee7878", exts: [".jpg",".jpeg",".png",".gif",".bmp",".svg",".webp",".ico",".tiff",".heic"] },
  Documents:   { icon: "📄", color: "#6cbce2", exts: [".pdf",".doc",".docx",".txt",".odt",".rtf",".xls",".xlsx",".ppt",".pptx",".csv",".md"] },
  Audio:       { icon: "🎵", color: "#e0d44b", exts: [".mp3",".wav",".flac",".aac",".ogg",".wma",".m4a",".opus"] },
  Videos:      { icon: "🎬", color: "#b69be6", exts: [".mp4",".mkv",".avi",".mov",".wmv",".flv",".webm",".m4v"] },
  Archives:    { icon: "🗜",  color: "#86d68d", exts: [".zip",".rar",".tar",".gz",".7z",".bz2",".xz",".iso"] },
  Code:        { icon: "💻", color: "#6cbce2", exts: [".py",".js",".ts",".html",".css",".java",".c",".cpp",".cs",".php",".rb",".go",".rs",".json",".xml",".yaml",".sh",".sql"] },
  Fonts:       { icon: "🔤", color: "#e6a76c", exts: [".ttf",".otf",".woff",".woff2",".eot"] },
  Executables: { icon: "⚙",  color: "#a0a8b5", exts: [".exe",".msi",".dmg",".apk",".deb",".rpm"] },
  Others:      { icon: "📦", color: "#9da4b0", exts: [] },
};

function getCategory(filename) {
  const ext = "." + filename.split(".").pop().toLowerCase();
  for (const [cat, info] of Object.entries(CATEGORIES)) {
    if (cat === "Others") continue;
    if (info.exts.includes(ext)) return cat;
  }
  return "Others";
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / 1048576).toFixed(1) + " MB";
}

// ── Animated counter ──────────────────────────
function AnimNum({ value }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = Math.ceil(value / 20);
    const t = setInterval(() => {
      start += step;
      if (start >= value) { setDisplay(value); clearInterval(t); }
      else setDisplay(start);
    }, 30);
    return () => clearInterval(t);
  }, [value]);
  return <span>{display}</span>;
}

function ProgressBar({ pct, color }) {
  return (
    <div className="prog-track">
      <div className="prog-fill" style={{ width: pct + "%", background: color, boxShadow: `0 0 8px ${color}88` }} />
    </div>
  );
}

function Toast({ msg, type }) {
  return <div className={`toast toast-${type}`}>{msg}</div>;
}

function CatCard({ name, count, total }) {
  const info = CATEGORIES[name];
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="cat-card">
      <div className="cat-card-top">
        <span className="cat-icon">{info.icon}</span>
        <span className="cat-count" style={{ color: info.color }}>{count}</span>
      </div>
      <div className="cat-name">{name}</div>
      <ProgressBar pct={pct} color={info.color} />
    </div>
  );
}

function FileRow({ file, category, status }) {
  const cat = CATEGORIES[category];
  const statusColor = status === "Moved" ? "#2dd4a0" : status === "Pending" ? "#f5c842" : "#f26464";
  return (
    <div className="file-row">
      <span className="file-icon">{cat?.icon || "📦"}</span>
      <span className="file-name">{file.name}</span>
      <span className="file-cat" style={{ color: cat?.color }}>{category}</span>
      <span className="file-size">{formatSize(file.size || 0)}</span>
      <span className="file-status" style={{ color: statusColor }}>{status}</span>
    </div>
  );
}

function DropZone({ onFiles }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef();

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const items = [...e.dataTransfer.files];
    if (items.length) onFiles(items);
  };

  return (
    <div
      className={`dropzone ${dragging ? "dragging" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current.click()}
    >
      <div className="drop-emoji">📂</div>
      <div className="drop-title">Drop files here to preview</div>
      <div className="drop-sub">or click to select files from your computer</div>
      <div className="drop-btn">Browse Files</div>
      <input ref={inputRef} type="file" multiple hidden onChange={(e) => onFiles([...e.target.files])} />
    </div>
  );
}

export default function App() {
  const [files, setFiles]         = useState([]);
  const [organized, setOrganized] = useState(false);
  const [animating, setAnimating] = useState(false);
  const [toast, setToast]         = useState(null);
  const [tab, setTab]             = useState("preview");
  const [statuses, setStatuses]   = useState({});

  const showToast = (msg, type = "success") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleFiles = (incoming) => {
    const mapped = incoming.map((f) => ({ name: f.name, size: f.size, category: getCategory(f.name) }));
    setFiles(mapped);
    setOrganized(false);
    const s = {};
    mapped.forEach((f) => (s[f.name] = "Pending"));
    setStatuses(s);
    setTab("preview");
  };

  const categoryCounts = () => {
    const counts = {};
    files.forEach((f) => { counts[f.category] = (counts[f.category] || 0) + 1; });
    return counts;
  };

  const handleOrganise = () => {
    if (!files.length) return;
    setAnimating(true);
    setTab("log");
    files.forEach((f, i) => {
      setTimeout(() => {
        setStatuses((prev) => ({ ...prev, [f.name]: "Moved" }));
        if (i === files.length - 1) {
          setOrganized(true);
          setAnimating(false);
          showToast(`✅ ${files.length} files organised successfully!`, "success");
        }
      }, 200 * (i + 1));
    });
  };

  const handleReset = () => {
    setFiles([]); setOrganized(false); setStatuses({}); setTab("preview");
    showToast("🔄 Reset complete", "info");
  };

  const counts = categoryCounts();
  const activeCats = Object.entries(counts).filter(([, v]) => v > 0);
  const movedCount = Object.values(statuses).filter((s) => s === "Moved").length;

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <div className="logo">📂</div>
          <div>
            <div className="logo-title">File Organizer</div>
            <div className="logo-sub">Organize files with me </div>
          </div>
        </div>
        <div className="header-right">
          {files.length > 0 && <div className="badge">{files.length} file{files.length !== 1 ? "s" : ""} loaded</div>}
          <div className="badge badge-blue">Python Backend Ready</div>
        </div>
      </header>

      <main className="main">
        {files.length === 0 ? (
          <div>
            <h1 className="page-title">Organise your files</h1>
            <p className="page-sub">Drop or select files — the app will sort them into folders by type automatically.</p>
            <DropZone onFiles={handleFiles} />
            <div className="legend-label">Supported Categories</div>
            <div className="legend-grid">
              {Object.entries(CATEGORIES).map(([name, info]) => (
                <div key={name} className="legend-item">
                  <span>{info.icon}</span>
                  <span className="legend-name">{name}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div>
            {/* Stat cards */}
            <div className="stats-row">
              {[
                { label: "Total Files",  value: files.length,  color: "#4f8ef7", icon: "📁" },
                { label: "Categories",   value: activeCats.length, color: "#7c5cfc", icon: "🗂" },
                { label: "Files Moved",  value: movedCount,    color: "#2dd4a0", icon: "✅" },
              ].map((s) => (
                <div key={s.label} className="stat-card">
                  <div className="stat-icon">{s.icon}</div>
                  <div>
                    <div className="stat-value" style={{ color: s.color }}><AnimNum value={s.value} /></div>
                    <div className="stat-label">{s.label}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Category breakdown */}
            {activeCats.length > 0 && (
              <div className="breakdown">
                <div className="section-label">Breakdown</div>
                <div className="cat-grid">
                  {activeCats.map(([cat, count]) => (
                    <CatCard key={cat} name={cat} count={count} total={files.length} />
                  ))}
                </div>
              </div>
            )}

            {/* Tabs */}
            <div className="tabs">
              {["preview", "log"].map((t) => (
                <button key={t} className={`tab-btn ${tab === t ? "active" : ""}`} onClick={() => setTab(t)}>
                  {t === "preview" ? "📋 Preview" : "📜 Activity Log"}
                </button>
              ))}
            </div>

            {/* File list */}
            <div className="file-list">
              <div className="file-list-header">
                <span style={{ width: 24 }} />
                <span style={{ flex: 1 }}>Filename</span>
                <span style={{ width: 90, textAlign: "right" }}>Category</span>
                <span style={{ width: 60, textAlign: "right" }}>Size</span>
                <span style={{ width: 56, textAlign: "right" }}>Status</span>
              </div>
              {files.map((f) => (
                <FileRow key={f.name} file={f} category={f.category}
                  status={tab === "preview" ? "Pending" : (statuses[f.name] || "Pending")} />
              ))}
            </div>

            {/* Actions */}
            <div className="actions">
              {!organized ? (
                <button className="btn-organise" onClick={handleOrganise} disabled={animating}>
                  {animating ? "⏳ Organising..." : "🚀 Organise Files"}
                </button>
              ) : (
                <div className="btn-done">✅ Organisation Complete</div>
              )}
              <button className="btn-reset" onClick={handleReset}>↩ Reset</button>
            </div>

            <div className="info-box">
              💡 This UI shows a <strong>live preview</strong> of how your files will be sorted.
              Actual file moving happens via <code>file_organizer.py</code> in your terminal.
            </div>

            

          </div>
        )}

      </main>

      {/* Neo-Brutalist Footer */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-left-side">
            <span className="footer-logo-emoji">📂</span>
            <span className="footer-brand">File Organizer</span>
          </div>
          <div className="footer-center">
            Built for <span className="footer-highlight">Synent Technologies</span> · Task 5
          </div>
          <div className="footer-right-side">
            <a href="#docs" className="footer-link">Documentation</a>
            <a href="#github" className="footer-link">GitHub</a>
          </div>
        </div>
      </footer>

      {toast && <Toast msg={toast.msg} type={toast.type} />}
    </div>
  );
}
        
    

      

