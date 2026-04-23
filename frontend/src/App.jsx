import { useState } from "react";
import UploadPanel from "./components/UploadPanel";
import ResultsDashboard from "./components/ResultsDashboard";
import "./index.css";

export default function App() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalysis = async ({ file, startDate, endDate }) => {
    setLoading(true);
    setError(null);
    setResults(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("start_date", startDate);
    formData.append("end_date", endDate);

    try {
      const res = await fetch("http://localhost:8000/api/v1/analyze", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail?.message || data.detail || "Analysis failed");
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResults(null);
    setError(null);
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="brand-mark">AWA</div>
          <div className="header-text">
            <h1 className="site-title">AI Weekly Analyst</h1>
            <p className="site-sub">Description-first weekly recaps for real work reporting</p>
          </div>
        </div>
        <div className="header-chip">Built for weekly reporting</div>
      </header>

      <main className="main">
        {!results ? (
          <UploadPanel onSubmit={handleAnalysis} loading={loading} error={error} />
        ) : (
          <ResultsDashboard data={results} onReset={handleReset} />
        )}
      </main>

      <footer className="footer">
        <span>Weekly insights from FastAPI and your spreadsheet data</span>
      </footer>
    </div>
  );
}
