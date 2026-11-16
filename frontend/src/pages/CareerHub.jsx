import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useProgress } from "../context/ProgressContext";
import { api } from "../services/api";
import logo from "../assets/logo.png";

export function CareerHub() {
  const { user, logout } = useAuth();
  const { setPage } = useProgress();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  const loadRecommendations = async () => {
    if (!user?.learner_id) return;
    setLoading(true);
    setError("");
    setData(null);
    try {
      const result = await api.getCareerRecommendations(user.learner_id);
      setData(result);
    } catch (err) {
      setError(err.message || "Failed to generate recommendations. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecommendations();
  }, [user]);

  const handleCopyCard = () => {
    if (!data?.endorsement_card_markdown) return;
    navigator.clipboard.writeText(data.endorsement_card_markdown).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    });
  };

  const matchColor = (score) => {
    if (score >= 80) return "#10b981";
    if (score >= 60) return "#f59e0b";
    return "#ef4444";
  };

  const levelBadgeColor = {
    Entry: "#6366f1",
    Junior: "#7D82B0",
    Mid: "#f59e0b",
    Senior: "#ef4444",
  };

  return (
    <div className="dashboard-container selection-container">
      {/* Navbar */}
      <header className="navbar">
        <div className="nav-brand">
          <img src={logo} alt="Evolyn Logo" className="brand-logo" style={{ height: "40px", marginRight: "12px" }} />
          <span className="subject-badge">CAREER HUB</span>
        </div>
        <div className="nav-actions">
          <button onClick={() => setPage("dashboard")} className="secondary-btn">⬅ Dashboard</button>
          <button onClick={() => setPage("badges")} className="secondary-btn">🏅 Badges</button>
          <button onClick={logout} className="logout-btn">Logout</button>
        </div>
      </header>

      <div style={{ maxWidth: "960px", margin: "0 auto", padding: "24px 16px" }}>

        {/* Hero Header */}
        <div className="glass-card" style={{ padding: "32px", marginBottom: "24px", textAlign: "center" }}>
          <div style={{ fontSize: "56px", marginBottom: "12px" }}>💼</div>
          <h2 style={{ margin: "0 0 8px", fontSize: "1.9rem" }}>AI Career Advisor</h2>
          <p style={{ color: "var(--text-secondary)", margin: "0 0 24px", maxWidth: "560px", marginLeft: "auto", marginRight: "auto" }}>
            Powered by Evolyn's AI agent, which analyzes your full learning journey to generate
            personalized job recommendations and a verified endorsement card for your GitHub.
          </p>
          <button
            className="start-dashboard-btn"
            onClick={loadRecommendations}
            disabled={loading}
            style={{ marginTop: "4px" }}
          >
            {loading ? "🤖 Analyzing your profile..." : "✨ Generate New Recommendations"}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="glass-card" style={{ padding: "20px", marginBottom: "20px", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171", textAlign: "center" }}>
            {error}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="glass-card" style={{ padding: "40px", textAlign: "center", marginBottom: "20px" }}>
            <div className="dot-typing" style={{ justifyContent: "center", marginBottom: "16px" }}>
              <span></span><span></span><span></span>
            </div>
            <p style={{ color: "var(--text-secondary)" }}>
              Evolyn AI is analyzing your quiz scores, topics, badges, and learning pace...
            </p>
          </div>
        )}

        {/* Results */}
        {data && !loading && (
          <>
            {/* Profile Snapshot */}
            <div className="glass-card" style={{ padding: "20px 28px", marginBottom: "20px" }}>
              <h3 style={{ margin: "0 0 16px" }}>📊 Your Profile Snapshot</h3>
              <div style={{ display: "flex", gap: "16px", flexWrap: "wrap" }}>
                {[
                  { label: "Subject", value: data.profile_snapshot?.subject?.toUpperCase() },
                  { label: "Level", value: data.profile_snapshot?.current_level },
                  { label: "Quiz Average", value: `${data.profile_snapshot?.quiz_average}%` },
                  { label: "Badges Earned", value: data.profile_snapshot?.badge_count },
                  { label: "GitHub", value: data.profile_snapshot?.github_username ? `@${data.profile_snapshot.github_username}` : "Not connected" },
                ].map((item) => (
                  <div key={item.label} className="glass-card" style={{ flex: "1", minWidth: "120px", padding: "12px 16px", textAlign: "center", border: "1px solid rgba(125,130,176,0.2)" }}>
                    <div style={{ fontSize: "1.2rem", fontWeight: "800", color: "#7D82B0" }}>{item.value}</div>
                    <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "4px" }}>{item.label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Skills Summary */}
            {data.skills_summary && (
              <div className="glass-card" style={{ padding: "24px 28px", marginBottom: "20px" }}>
                <h3 style={{ margin: "0 0 16px" }}>🧠 Skills Assessment</h3>
                <p style={{ margin: "0 0 16px", color: "var(--text-secondary)", fontStyle: "italic" }}>
                  {data.skills_summary.overall_readiness}
                </p>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                  <div>
                    <h4 style={{ margin: "0 0 10px", color: "#10b981", fontSize: "14px" }}>✅ Strengths</h4>
                    <ul style={{ margin: 0, paddingLeft: "18px", color: "var(--text-secondary)", fontSize: "13px" }}>
                      {(data.skills_summary.strengths || []).map((s, i) => (
                        <li key={i} style={{ marginBottom: "4px" }}>{s}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 style={{ margin: "0 0 10px", color: "#f59e0b", fontSize: "14px" }}>⚡ Areas to Improve</h4>
                    <ul style={{ margin: 0, paddingLeft: "18px", color: "var(--text-secondary)", fontSize: "13px" }}>
                      {(data.skills_summary.areas_to_improve || []).map((s, i) => (
                        <li key={i} style={{ marginBottom: "4px" }}>{s}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Job Recommendations */}
            <h3 style={{ margin: "0 0 16px" }}>🎯 Job Recommendations</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginBottom: "24px" }}>
              {(data.recommendations || []).map((job, idx) => (
                <div key={idx} className="glass-card career-job-card">
                  <div className="career-job-header">
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap", marginBottom: "6px" }}>
                        <h4 style={{ margin: 0, fontSize: "1.1rem" }}>{job.title}</h4>
                        <span style={{
                          padding: "2px 10px",
                          borderRadius: "20px",
                          fontSize: "11px",
                          fontWeight: "700",
                          background: (levelBadgeColor[job.level] || "#7D82B0") + "22",
                          color: levelBadgeColor[job.level] || "#7D82B0",
                          border: `1px solid ${(levelBadgeColor[job.level] || "#7D82B0")}44`,
                        }}>
                          {job.level}
                        </span>
                      </div>
                      <p style={{ margin: 0, color: "var(--text-secondary)", fontSize: "13px" }}>{job.description}</p>
                    </div>

                    {/* Match Score Ring */}
                    <div style={{ flexShrink: 0, textAlign: "center" }}>
                      <div style={{
                        width: "64px", height: "64px",
                        borderRadius: "50%",
                        border: `3px solid ${matchColor(job.match_score)}`,
                        display: "flex", alignItems: "center", justifyContent: "center",
                        flexDirection: "column",
                        boxShadow: `0 0 14px ${matchColor(job.match_score)}44`,
                      }}>
                        <span style={{ fontSize: "15px", fontWeight: "800", color: matchColor(job.match_score) }}>
                          {job.match_score}%
                        </span>
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--text-secondary)", marginTop: "4px" }}>Match</div>
                    </div>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginTop: "14px" }}>
                    <div>
                      <div style={{ fontSize: "11px", color: "#10b981", fontWeight: "700", marginBottom: "6px" }}>✅ Matched Skills</div>
                      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                        {(job.matched_skills || []).map((s) => (
                          <span key={s} style={{ padding: "2px 8px", borderRadius: "4px", fontSize: "11px", background: "rgba(16,185,129,0.12)", color: "#10b981", border: "1px solid rgba(16,185,129,0.2)" }}>{s}</span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: "11px", color: "#f59e0b", fontWeight: "700", marginBottom: "6px" }}>⚡ Missing Skills</div>
                      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                        {(job.missing_skills || []).map((s) => (
                          <span key={s} style={{ padding: "2px 8px", borderRadius: "4px", fontSize: "11px", background: "rgba(245,158,11,0.1)", color: "#f59e0b", border: "1px solid rgba(245,158,11,0.2)" }}>{s}</span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {job.companies?.length > 0 && (
                    <div style={{ marginTop: "12px", fontSize: "12px", color: "var(--text-secondary)" }}>
                      🏢 <strong>Companies hiring:</strong> {job.companies.join(" · ")}
                    </div>
                  )}

                  {job.tip && (
                    <div style={{ marginTop: "10px", padding: "10px 14px", borderRadius: "8px", background: "rgba(125,130,176,0.08)", borderLeft: "3px solid #7D82B0", fontSize: "12px", color: "var(--text-secondary)" }}>
                      💡 <strong>Tip:</strong> {job.tip}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Evolyn Endorsement Card */}
            {data.endorsement_card_markdown && (
              <div className="glass-card" style={{ padding: "24px 28px", marginBottom: "24px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                  <h3 style={{ margin: 0 }}>🏅 Evolyn AI Endorsement Card</h3>
                  <button
                    onClick={handleCopyCard}
                    style={{
                      padding: "8px 16px",
                      borderRadius: "8px",
                      border: "1px solid rgba(125,130,176,0.4)",
                      background: copied ? "rgba(16,185,129,0.15)" : "rgba(125,130,176,0.1)",
                      color: copied ? "#10b981" : "#7D82B0",
                      cursor: "pointer",
                      fontFamily: "inherit",
                      fontSize: "13px",
                      fontWeight: "600",
                      transition: "all 0.2s",
                    }}
                  >
                    {copied ? "✅ Copied!" : "📋 Copy Markdown"}
                  </button>
                </div>
                <p style={{ margin: "0 0 14px", color: "var(--text-secondary)", fontSize: "13px" }}>
                  Copy this Markdown and paste it into your GitHub Profile README to showcase your Evolyn certification publicly.
                </p>
                <pre style={{
                  margin: 0,
                  padding: "16px",
                  background: "rgba(0,0,0,0.3)",
                  borderRadius: "10px",
                  border: "1px solid rgba(255,255,255,0.08)",
                  color: "#c4cfde",
                  fontSize: "12px",
                  fontFamily: "'Fira Code', monospace",
                  overflowX: "auto",
                  whiteSpace: "pre-wrap",
                  lineHeight: "1.6",
                }}>
                  {data.endorsement_card_markdown}
                </pre>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default CareerHub;
