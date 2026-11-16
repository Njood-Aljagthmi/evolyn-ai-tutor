import React, { useEffect, useState, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import { useProgress } from "../context/ProgressContext";
import { api } from "../services/api";
import logo from "../assets/logo.png";

const RARITY_ORDER = { Legendary: 0, Epic: 1, Rare: 2, Uncommon: 3, Common: 4 };

export function Badges() {
  const { user, logout } = useAuth();
  const { setPage } = useProgress();
  const [badgeData, setBadgeData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [pushing, setPushing] = useState({});
  const [pushMessages, setPushMessages] = useState({});
  const [filter, setFilter] = useState("all"); // "all" | "earned" | "locked"

  const loadBadges = useCallback(async () => {
    if (!user?.learner_id) return;
    try {
      setLoading(true);
      const data = await api.getBadges(user.learner_id);
      setBadgeData(data);
    } catch (err) {
      console.error("Failed to load badges:", err);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    loadBadges();

    // Handle GitHub OAuth callback redirect
    const params = new URLSearchParams(window.location.search);
    if (params.get("github_connected") === "true") {
      const ghUser = params.get("github_user");
      window.history.replaceState({}, "", window.location.pathname);
      setTimeout(() => loadBadges(), 500);
      alert(`✅ Successfully connected GitHub account: @${ghUser}`);
    }
    if (params.get("github_error")) {
      window.history.replaceState({}, "", window.location.pathname);
      alert("❌ Failed to connect GitHub. Please try again.");
    }
  }, [loadBadges]);

  const handleConnectGitHub = () => {
    if (!user?.learner_id) return;
    const url = api.getGitHubConnectUrl(user.learner_id);
    window.location.href = url;
  };

  const handlePushBadge = async (badge) => {
    if (!badge.earned || !badgeData?.github_connected) return;
    setPushing((p) => ({ ...p, [badge.badge_id]: true }));
    setPushMessages((p) => ({ ...p, [badge.badge_id]: "" }));

    try {
      const res = await api.pushBadgeToGitHub(
        user.learner_id,
        badge.badge_id,
        badge.title,
        badge.emoji,
        badge.color,
        badge.subject
      );
      const msg = res.status === "already_pushed"
        ? "Already on GitHub! ✓"
        : `Pushed to @${badgeData.github_username}! 🎉`;
      setPushMessages((p) => ({ ...p, [badge.badge_id]: msg }));
    } catch (err) {
      const detail = err.message || "Push failed.";
      setPushMessages((p) => ({ ...p, [badge.badge_id]: `⚠️ ${detail}` }));
    } finally {
      setPushing((p) => ({ ...p, [badge.badge_id]: false }));
    }
  };

  const sortedBadges = badgeData?.badges
    ? [...badgeData.badges].sort((a, b) => {
        if (a.earned && !b.earned) return -1;
        if (!a.earned && b.earned) return 1;
        return (RARITY_ORDER[a.rarity] ?? 9) - (RARITY_ORDER[b.rarity] ?? 9);
      })
    : [];

  const filtered = sortedBadges.filter((b) => {
    if (filter === "earned") return b.earned;
    if (filter === "locked") return !b.earned;
    return true;
  });

  const earnedCount = sortedBadges.filter((b) => b.earned).length;

  return (
    <div className="dashboard-container selection-container">
      {/* Navbar */}
      <header className="navbar">
        <div className="nav-brand">
          <img src={logo} alt="Evolyn Logo" className="brand-logo" style={{ height: "40px", marginRight: "12px" }} />
          <span className="subject-badge">BADGES</span>
        </div>
        <div className="nav-actions">
          <button onClick={() => setPage("dashboard")} className="secondary-btn">⬅ Dashboard</button>
          <button onClick={() => setPage("career")} className="secondary-btn">💼 Career Hub</button>
          <button onClick={logout} className="logout-btn">Logout</button>
        </div>
      </header>

      <div style={{ maxWidth: "900px", margin: "0 auto", padding: "24px 16px" }}>
        {/* Header Section */}
        <div className="glass-card" style={{ padding: "28px 32px", marginBottom: "24px", textAlign: "center" }}>
          <div style={{ fontSize: "56px", marginBottom: "12px" }}>🏅</div>
          <h2 style={{ margin: "0 0 8px", fontSize: "1.8rem" }}>Achievement Badges</h2>
          <p style={{ color: "var(--text-secondary)", margin: "0 0 20px" }}>
            Earn badges through your learning journey and showcase them on your GitHub profile.
          </p>

          {/* Stats row */}
          <div style={{ display: "flex", gap: "16px", justifyContent: "center", flexWrap: "wrap", marginBottom: "20px" }}>
            <div className="glass-card" style={{ padding: "12px 24px", border: "1px solid rgba(125,130,176,0.3)" }}>
              <div style={{ fontSize: "1.6rem", fontWeight: "800", color: "#7D82B0" }}>{earnedCount}</div>
              <div style={{ fontSize: "12px", color: "var(--text-secondary)" }}>Earned</div>
            </div>
            <div className="glass-card" style={{ padding: "12px 24px", border: "1px solid rgba(125,130,176,0.3)" }}>
              <div style={{ fontSize: "1.6rem", fontWeight: "800", color: "var(--text-secondary)" }}>
                {sortedBadges.length - earnedCount}
              </div>
              <div style={{ fontSize: "12px", color: "var(--text-secondary)" }}>Locked</div>
            </div>
            <div className="glass-card" style={{ padding: "12px 24px", border: "1px solid rgba(125,130,176,0.3)" }}>
              <div style={{ fontSize: "1.6rem", fontWeight: "800", color: badgeData?.github_connected ? "#10b981" : "var(--text-secondary)" }}>
                {badgeData?.github_connected ? `@${badgeData.github_username}` : "—"}
              </div>
              <div style={{ fontSize: "12px", color: "var(--text-secondary)" }}>GitHub</div>
            </div>
          </div>

          {/* GitHub Connect Button */}
          {badgeData && !badgeData.github_connected ? (
            <button className="start-dashboard-btn" onClick={handleConnectGitHub} style={{ marginTop: "4px" }}>
              <span style={{ marginRight: "8px" }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style={{ verticalAlign: "middle" }}>
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.44 9.8 8.2 11.38.6.11.82-.26.82-.58v-2.03c-3.34.72-4.04-1.61-4.04-1.61-.54-1.38-1.32-1.75-1.32-1.75-1.08-.74.08-.72.08-.72 1.2.08 1.83 1.23 1.83 1.23 1.06 1.82 2.78 1.29 3.46.99.1-.77.42-1.29.76-1.59-2.66-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.13-.3-.54-1.52.12-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 0 1 3-.4c1.02 0 2.04.14 3 .4 2.28-1.55 3.29-1.23 3.29-1.23.66 1.66.25 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.81 5.62-5.48 5.92.43.37.81 1.1.81 2.22v3.29c0 .32.22.7.83.58C20.57 21.8 24 17.3 24 12c0-6.63-5.37-12-12-12z"/>
                </svg>
              </span>
              Connect GitHub to Push Badges
            </button>
          ) : badgeData?.github_connected ? (
            <div style={{ display: "inline-flex", alignItems: "center", gap: "8px", padding: "10px 20px", borderRadius: "10px", background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.3)", color: "#10b981", fontSize: "14px" }}>
              ✅ GitHub Connected as <strong>@{badgeData.github_username}</strong>
            </div>
          ) : null}
        </div>

        {/* Filter Tabs */}
        <div style={{ display: "flex", gap: "10px", marginBottom: "20px" }}>
          {["all", "earned", "locked"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                padding: "8px 20px",
                borderRadius: "8px",
                border: "1px solid",
                borderColor: filter === f ? "rgba(125,130,176,0.6)" : "rgba(255,255,255,0.1)",
                background: filter === f ? "rgba(125,130,176,0.2)" : "transparent",
                color: filter === f ? "#fff" : "var(--text-secondary)",
                cursor: "pointer",
                fontFamily: "inherit",
                fontWeight: "600",
                fontSize: "13px",
                textTransform: "capitalize",
                transition: "all 0.2s",
              }}
            >
              {f === "all" ? `All (${sortedBadges.length})` : f === "earned" ? `Earned (${earnedCount})` : `Locked (${sortedBadges.length - earnedCount})`}
            </button>
          ))}
        </div>

        {/* Badge Grid */}
        {loading ? (
          <div style={{ textAlign: "center", padding: "60px", color: "var(--text-secondary)" }}>
            Loading badges...
          </div>
        ) : (
          <div className="badges-grid">
            {filtered.map((badge) => (
              <BadgeCard
                key={badge.badge_id}
                badge={badge}
                githubConnected={badgeData?.github_connected}
                onPush={() => handlePushBadge(badge)}
                pushing={pushing[badge.badge_id]}
                pushMessage={pushMessages[badge.badge_id]}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// BadgeCard Component
// ─────────────────────────────────────────────────────────────────────────────

function BadgeCard({ badge, githubConnected, onPush, pushing, pushMessage }) {
  const rarityColors = {
    Legendary: "#fbbf24",
    Epic: "#ef4444",
    Rare: "#8b5cf6",
    Uncommon: "#7D82B0",
    Common: "#6b7280",
  };

  const rarityColor = rarityColors[badge.rarity] || "#7D82B0";

  return (
    <div
      className={`badge-card ${badge.earned ? "badge-earned" : "badge-locked"}`}
      style={{
        "--badge-color": badge.color,
        "--badge-glow": badge.glow,
        "--rarity-color": rarityColor,
      }}
    >
      {/* Rarity tag */}
      <div className="badge-rarity-tag" style={{ color: rarityColor, borderColor: rarityColor + "44" }}>
        {badge.rarity}
      </div>

      {/* Emoji + glow ring */}
      <div className={`badge-emoji-ring ${badge.earned ? "ring-earned" : "ring-locked"}`}>
        <span className="badge-emoji">{badge.earned ? badge.emoji : "🔒"}</span>
      </div>

      {/* Text content */}
      <h4 className="badge-title">{badge.title}</h4>
      <p className="badge-description">{badge.description}</p>

      {badge.earned && badge.earned_at && (
        <p className="badge-date">
          Earned {new Date(badge.earned_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
        </p>
      )}

      {/* GitHub push button */}
      {badge.earned && (
        <div style={{ marginTop: "auto", paddingTop: "12px" }}>
          {githubConnected ? (
            <>
              <button
                className="badge-push-btn"
                onClick={onPush}
                disabled={pushing}
              >
                {pushing ? "Pushing..." : (
                  <>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style={{ marginRight: "6px", verticalAlign: "middle" }}>
                      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.44 9.8 8.2 11.38.6.11.82-.26.82-.58v-2.03c-3.34.72-4.04-1.61-4.04-1.61-.54-1.38-1.32-1.75-1.32-1.75-1.08-.74.08-.72.08-.72 1.2.08 1.83 1.23 1.83 1.23 1.06 1.82 2.78 1.29 3.46.99.1-.77.42-1.29.76-1.59-2.66-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.13-.3-.54-1.52.12-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 0 1 3-.4c1.02 0 2.04.14 3 .4 2.28-1.55 3.29-1.23 3.29-1.23.66 1.66.25 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.81 5.62-5.48 5.92.43.37.81 1.1.81 2.22v3.29c0 .32.22.7.83.58C20.57 21.8 24 17.3 24 12c0-6.63-5.37-12-12-12z"/>
                    </svg>
                    Push to GitHub
                  </>
                )}
              </button>
              {pushMessage && (
                <p style={{ margin: "6px 0 0", fontSize: "11px", color: pushMessage.includes("⚠") ? "#f87171" : "#10b981", textAlign: "center" }}>
                  {pushMessage}
                </p>
              )}
            </>
          ) : (
            <p style={{ fontSize: "11px", color: "var(--text-secondary)", margin: "0", textAlign: "center" }}>
              Connect GitHub to push this badge
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default Badges;
