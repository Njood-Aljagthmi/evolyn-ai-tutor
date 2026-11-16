import React from "react";

function ProgressRing({ percent, label, caption, color }) {
  const radius = 38;
  const stroke = 6;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (Math.max(0, Math.min(100, percent)) / 100) * circumference;

  return (
    <div className="progress-ring-card">
      <div className="progress-ring-svg-wrapper">
        <svg width={(radius + stroke) * 2} height={(radius + stroke) * 2} className="progress-ring-svg">
          <defs>
            <filter id={`ring-glow-${label.replace(/[^a-zA-Z0-9]/g, '-')}`} x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <circle
            cx={radius + stroke}
            cy={radius + stroke}
            r={radius}
            fill="transparent"
            stroke="rgba(255, 255, 255, 0.05)"
            strokeWidth={stroke}
          />
          <circle
            cx={radius + stroke}
            cy={radius + stroke}
            r={radius}
            fill="transparent"
            stroke={color}
            strokeWidth={stroke}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            filter={`url(#ring-glow-${label.replace(/[^a-zA-Z0-9]/g, '-')})`}
            className="progress-ring-fill"
          />
        </svg>
        <div className="progress-ring-percentage">
          {percent.toFixed(0)}%
        </div>
      </div>
      <div className="progress-ring-meta">
        <span className="progress-ring-label">{label}</span>
        {caption && <span className="progress-ring-caption">{caption}</span>}
      </div>
    </div>
  );
}

export function ReportChart({ reportsData }) {
  if (!reportsData) return <p className="no-data">Insufficient data to display analytics charts.</p>;

  const { difficulty_performance = [], weakness_trends = [], timeline = [], milestones = [] } = reportsData;

  // 1. Difficulty Performance Rendering
  const maxDifficultyScore = 100;
  
  // 2. Timeline SVG calculation
  const renderTimelineSVG = () => {
    if (timeline.length === 0) return <p className="no-data">Complete some quizzes to track your progress here.</p>;

    const width = 600;
    const height = 150;
    const padding = 25;
    
    const xInterval = timeline.length > 1 ? (width - padding * 2) / (timeline.length - 1) : 0;
    const yScale = (score) => height - padding - (score / 100) * (height - padding * 2);

    const points = timeline.map((item, index) => ({
      x: padding + index * xInterval,
      y: yScale(item.score),
      ...item
    }));

    let pathD = "";
    if (points.length > 0) {
      pathD = `M ${points[0].x} ${points[0].y} ` + points.slice(1).map(p => `L ${p.x} ${p.y}`).join(" ");
    }

    return (
      <div className="svg-container">
        <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} className="analytics-svg">
          {/* Grid lines */}
          {[0, 25, 50, 75, 100].map(s => (
            <g key={s}>
              <line 
                x1={padding} 
                y1={yScale(s)} 
                x2={width - padding} 
                y2={yScale(s)} 
                stroke="rgba(255,255,255,0.08)" 
                strokeDasharray="4 4"
              />
              <text x={padding - 10} y={yScale(s) + 4} fill="rgba(255,255,255,0.4)" fontSize="10" textAnchor="end">{s}%</text>
            </g>
          ))}

          {/* Line Path */}
          {points.length > 1 && (
            <path 
              d={pathD} 
              fill="none" 
              stroke="url(#line-grad)" 
              strokeWidth="3" 
              className="line-path"
            />
          )}

          {/* Glowing Gradients */}
          <defs>
            <linearGradient id="line-grad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#818cf8" />
              <stop offset="50%" stopColor="#c084fc" />
              <stop offset="100%" stopColor="#f472b6" />
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Data Points */}
          {points.map((p, i) => (
            <g key={i} className="dot-group">
              <circle 
                cx={p.x} 
                cy={p.y} 
                r="5" 
                fill={p.score >= 70 ? "#34d399" : (p.score >= 50 ? "#facc15" : "#f87171")}
                stroke="#0f172a"
                strokeWidth="2"
                filter="url(#glow)"
              />
              <title>{`${p.topic}: ${p.score}% (${p.level})`}</title>
            </g>
          ))}
        </svg>
      </div>
    );
  };

  return (
    <div className="report-charts">
      {/* Quiz Score History Timeline */}
      <div className="chart-card">
        <h3>📈 Quiz Scores Progress Over Time</h3>
        {renderTimelineSVG()}
        <p className="caption">Hover over the data points to view topic-specific quiz scores and details.</p>
      </div>

      <div className="chart-columns">
        {/* Difficulty Average Performance */}
        <div className="chart-card half">
          <h3>🎓 Average Performance by Difficulty</h3>
          <div className="progress-rings-container">
            {["beginner", "intermediate", "advanced"].map((lvl) => {
              const item = difficulty_performance.find(d => d.level === lvl) || { level: lvl, avg_score: 0, total_quizzes: 0 };
              const percentage = Math.min(100, item.avg_score);
              const color = lvl === "beginner" ? "#34d399" : (lvl === "intermediate" ? "#facc15" : "#f87171");
              const levelLabel = lvl === "beginner" ? "Beginner" : (lvl === "intermediate" ? "Intermediate" : "Advanced");
              const icon = lvl === "beginner" ? "🟢" : (lvl === "intermediate" ? "🟡" : "🔴");
              return (
                <ProgressRing 
                  key={lvl}
                  percent={percentage}
                  label={`${levelLabel} ${icon}`}
                  caption={`Quizzes: ${item.total_quizzes}`}
                  color={color}
                />
              );
            })}
          </div>
        </div>

        {/* Weak Area Failure Counts */}
        <div className="chart-card half">
          <h3>⚠️ Mistakes Frequency by Topic</h3>
          {weakness_trends.length === 0 ? (
            <p className="no-data success-text">🎉 Excellent performance! No repeating mistakes in any topics.</p>
          ) : (
            <div className="bar-charts-list">
              {weakness_trends.slice(0, 5).map((item, idx) => {
                const maxFails = Math.max(...weakness_trends.map(w => w.fail_count));
                const fillWidth = maxFails > 0 ? (item.fail_count / maxFails) * 100 : 0;
                return (
                  <div key={idx} className="performance-bar-item">
                    <div className="bar-label">
                      <span>{item.topic.toUpperCase()}</span>
                      <span className="fail-count-tag">{item.fail_count} failed attempts</span>
                    </div>
                    <div className="bar-bg">
                      <div 
                        className="bar-fill fail-fill" 
                        style={{ 
                          width: `${fillWidth}%`, 
                          backgroundColor: "#ef4444",
                          boxShadow: "0 0 8px rgba(239, 68, 68, 0.4)"
                        }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ReportChart;
