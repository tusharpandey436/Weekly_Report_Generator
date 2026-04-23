export default function WeekCard({ week, index }) {
  const bullets = week.summary_points && week.summary_points.length ? week.summary_points : [week.ai_summary];
  const descriptionLog = week.description_entries && week.description_entries.length ? week.description_entries : [];
  const themeGroups = week.theme_groups && week.theme_groups.length ? week.theme_groups : [];
  const weekSummary = week.week_summary || week.ai_summary;
  const summarySections = week.week_summary_sections && week.week_summary_sections.length ? week.week_summary_sections : [];

  return (
    <article className="week-card">
      <div className="week-card-header">
        <div className="week-heading-copy">
          <div className="week-badge">Week {index + 1}</div>
          <h3 className="week-ending">Week ending {week.week_ending}</h3>
        </div>
        <div className="week-header-meta">
          <span className="meta-chip">Description-led</span>
          <span className="meta-chip subtle">Filtered and grouped</span>
        </div>
      </div>

      <section className="summary-block">
        <div className="summary-label">
          <span className="ai-dot" />
          Weekly Summary
        </div>
        {summarySections.length > 0 ? (
          <div className="executive-summary-grid">
            {summarySections.map((section) => (
              <div className="executive-summary-card" key={section.title}>
                <div className="executive-summary-title">{section.title}</div>
                <p className="executive-summary-text">{section.text}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="summary-paragraph">{weekSummary}</p>
        )}
      </section>

      <section className="summary-block">
        <div className="summary-label">
          <span className="ai-dot" />
          Weekly Work Highlights
        </div>
        <ul className="summary-bullets">
          {bullets.map((bullet, idx) => (
            <li key={`${idx}-${bullet}`} className="summary-bullet">
              {bullet}
            </li>
          ))}
        </ul>
      </section>

      {themeGroups.length > 0 && (
        <section className="summary-block theme-block">
          <div className="summary-label">
            <span className="ai-dot" />
            Work Themes
          </div>
          <div className="theme-grid">
            {themeGroups.slice(0, 8).map((group) => (
              <div className="theme-card" key={group.theme}>
                <div className="theme-card-head">
                  <span className="theme-name">{group.theme}</span>
                  <span className="theme-count">{group.count}</span>
                </div>
                <ul className="theme-entries">
                  {group.entries.slice(0, 4).map((entry, idx) => (
                    <li key={`${group.theme}-${idx}`} className="theme-entry">
                      {entry}
                    </li>
                  ))}
                </ul>
                {group.entries.length > 4 && (
                  <div className="theme-more">+ {group.entries.length - 4} more entries</div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {descriptionLog.length > 0 && (
        <section className="summary-block description-block">
          <div className="summary-label">
            <span className="ai-dot" />
            Description Log
          </div>
          <div className="description-log">
            {descriptionLog.slice(0, 50).map((entry, idx) => (
              <div key={`${idx}-${entry}`} className="description-item">
                <span className="description-bullet" />
                <span className="description-text">{entry}</span>
              </div>
            ))}
          </div>
          {descriptionLog.length > 50 && (
            <div className="description-more">+ {descriptionLog.length - 50} more description entries</div>
          )}
        </section>
      )}

      <div className="insight-row">
        <div className="insight-card peak">
          <div className="insight-icon">Peak</div>
          <div>
            <div className="insight-title">Peak Work Day</div>
            <div className="insight-value">{week.peak_day || "-"}</div>
          </div>
        </div>
        <div className="insight-card trend">
          <div className="insight-icon">Trend</div>
          <div>
            <div className="insight-title">Trend vs Previous Week</div>
            <div className="insight-value trend-text">
              {week.trend_vs_previous_week || "No previous week data."}
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}
