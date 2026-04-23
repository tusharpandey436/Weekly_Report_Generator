export default function MetricsSummary({ metrics }) {
  const columns = {};

  Object.entries(metrics).forEach(([key, val]) => {
    const isSum = key.endsWith("_sum");
    const isMean = key.endsWith("_mean");
    if (!isSum && !isMean) return;

    const col = isSum ? key.replace("_sum", "") : key.replace("_mean", "");
    if (!columns[col]) columns[col] = {};
    if (isSum) columns[col].sum = val;
    if (isMean) columns[col].mean = val;
  });

  const rows = Object.entries(columns);
  if (rows.length === 0) return null;

  const fmt = (v) =>
    typeof v === "number"
      ? v % 1 === 0
        ? v.toLocaleString()
        : v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      : "—";

  return (
    <section className="metrics-block">
      <div className="metrics-header">
        <span className="metrics-title">Supporting Metrics</span>
        <span className="metrics-sub">{rows.length} column{rows.length !== 1 ? "s" : ""}</span>
      </div>
      <div className="metrics-table-wrap">
        <table className="metrics-table">
          <thead>
            <tr>
              <th>Column</th>
              <th className="num">Weekly Total</th>
              <th className="num">Average Per Day</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([col, vals]) => (
              <tr key={col}>
                <td className="col-name">{col}</td>
                <td className="num">{fmt(vals.sum)}</td>
                <td className="num secondary">{fmt(vals.mean)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
