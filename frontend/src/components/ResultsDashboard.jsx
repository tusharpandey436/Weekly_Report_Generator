import { useMemo, useState } from "react";
import WeekCard from "./WeekCard";
import MetricsSummary from "./MetricsSummary";

export default function ResultsDashboard({ data, onReset }) {
  const [activeWeek, setActiveWeek] = useState(0);

  const activeResult = data.weekly_results[activeWeek];

  const totals = useMemo(() => {
    return data.weekly_results.reduce(
      (acc, week) => {
        acc.descriptions += week.description_entries?.length || 0;
        acc.themes += week.theme_groups?.length || 0;
        acc.highlights += week.summary_points?.length || 0;
        return acc;
      },
      { descriptions: 0, themes: 0, highlights: 0 }
    );
  }, [data.weekly_results]);

  return (
    <div className="dashboard">
      <section className="dash-hero">
        <div className="hero-copy">
          <div className="hero-kicker">Weekly analysis ready</div>
          <h2 className="hero-title">{data.file_name}</h2>
          <p className="hero-sub">
            {data.start_date} to {data.end_date}. The cards below are built from the Description rows in your spreadsheet.
          </p>
          <div className="hero-actions">
            <button className="back-btn" onClick={onReset}>
              Back to new analysis
            </button>
            <div className="hero-badge">Description-first view</div>
          </div>
        </div>

        <div className="hero-stats">
          <div className="hero-stat">
            <span className="hero-stat-label">Weeks</span>
            <span className="hero-stat-value">{data.total_weeks_analyzed}</span>
          </div>
          <div className="hero-stat accent">
            <span className="hero-stat-label">Descriptions</span>
            <span className="hero-stat-value">{totals.descriptions}</span>
          </div>
          <div className="hero-stat">
            <span className="hero-stat-label">Themes</span>
            <span className="hero-stat-value">{totals.themes}</span>
          </div>
          <div className="hero-stat">
            <span className="hero-stat-label">Highlights</span>
            <span className="hero-stat-value">{totals.highlights}</span>
          </div>
        </div>
      </section>

      <div className="dash-body">
        <aside className="week-sidebar">
          <div className="sidebar-label">Weekly periods</div>
          {data.weekly_results.map((week, index) => (
            <button
              key={week.week_ending}
              className={`week-tab ${index === activeWeek ? "active" : ""}`}
              onClick={() => setActiveWeek(index)}
            >
              <span className="week-tab-num">Week {index + 1}</span>
              <span className="week-tab-date">w/e {week.week_ending}</span>
            </button>
          ))}
        </aside>

        <div className="dash-content">
          <WeekCard week={activeResult} index={activeWeek} />
          <MetricsSummary metrics={activeResult.stats.metrics} />
        </div>
      </div>
    </div>
  );
}
