import { useRef, useState } from "react";

export default function UploadPanel({ onSubmit, loading, error }) {
  const [file, setFile] = useState(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef();

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped?.name.endsWith(".xlsx")) setFile(dropped);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!file || !startDate || !endDate) return;
    onSubmit({ file, startDate, endDate });
  };

  const isReady = file && startDate && endDate && !loading;

  return (
    <div className="upload-wrapper">
      <section className="upload-card">
        <div className="card-header card-header-hero">
          <span className="card-tag">Step 1 of 2</span>
          <h2 className="card-title">Turn one spreadsheet into a weekly story</h2>
          <p className="card-desc">
            Upload your Excel file, choose the date range, and we will extract Description rows into a polished weekly report.
          </p>
          <div className="hero-points">
            <span className="mini-pill">Description-first</span>
            <span className="mini-pill">Theme grouping</span>
            <span className="mini-pill">Weekly summary</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="upload-form">
          <div
            className={`dropzone ${dragging ? "dragging" : ""} ${file ? "has-file" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current.click()}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".xlsx"
              hidden
              onChange={(e) => setFile(e.target.files[0])}
            />
            {file ? (
              <div className="file-info">
                <div className="file-icon">
                  <XlsxIcon />
                </div>
                <div>
                  <div className="file-name">{file.name}</div>
                  <div className="file-size">{(file.size / 1024).toFixed(1)} KB - Ready</div>
                </div>
                <button
                  type="button"
                  className="file-remove"
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                  }}
                >
                  x
                </button>
              </div>
            ) : (
              <div className="drop-prompt">
                <div className="drop-icon">
                  <UploadIcon />
                </div>
                <div className="drop-text">
                  <strong>Drop your .xlsx file here</strong>
                  <span>or click to browse</span>
                </div>
              </div>
            )}
          </div>

          <div className="date-grid">
            <div className="date-group">
              <label className="date-label">Start Date</label>
              <input
                type="date"
                className="date-input"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
              />
            </div>
            <div className="date-group">
              <label className="date-label">End Date</label>
              <input
                type="date"
                className="date-input"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                required
              />
            </div>
          </div>

          {error && (
            <div className="error-banner">
              <span className="error-icon">!</span>
              <span>{error}</span>
            </div>
          )}

          <div className="submit-row">
            <button type="submit" className={`submit-btn ${loading ? "loading" : ""}`} disabled={!isReady}>
              {loading ? (
                <span className="btn-loading">
                  <span className="spinner" />
                  Analysing weeks...
                </span>
              ) : (
                <span>Run weekly analysis</span>
              )}
            </button>
            <div className="submit-note">Best results come from a populated Description column.</div>
          </div>
        </form>
      </section>

      <aside className="feature-rail">
        <div className="feature-rail-header">
          <div className="feature-rail-title">What gets analyzed</div>
          <div className="feature-rail-sub">Only the useful stuff</div>
        </div>
        {[
          { icon: "01", label: "Weekly bucketing", desc: "Mon-Sun grouping" },
          { icon: "02", label: "Description parsing", desc: "Main work notes" },
          { icon: "03", label: "Theme grouping", desc: "Similar work merged" },
          { icon: "04", label: "Weekly summary", desc: "Executive recap" },
        ].map((f) => (
          <div className="feature-item" key={f.label}>
            <span className="feature-icon">{f.icon}</span>
            <div>
              <div className="feature-label">{f.label}</div>
              <div className="feature-desc">{f.desc}</div>
            </div>
          </div>
        ))}
      </aside>
    </div>
  );
}

const UploadIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="17 8 12 3 7 8" />
    <line x1="12" y1="3" x2="12" y2="15" />
  </svg>
);

const XlsxIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="8" y1="13" x2="16" y2="13" />
    <line x1="8" y1="17" x2="16" y2="17" />
    <line x1="10" y1="9" x2="14" y2="9" />
  </svg>
);
