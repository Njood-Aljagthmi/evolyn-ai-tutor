import React, { useEffect } from "react";
import { useProgress } from "../context/ProgressContext";
import { useAuth } from "../context/AuthContext";
import { useQuiz } from "../context/QuizContext";
import LoadingSpinner from "../components/LoadingSpinner";
import logo from "../assets/logo.png";
import ConfettiEffect from "../components/ConfettiEffect";

export function Dashboard() {
  const { 
    subject, 
    dashboardData, 
    loadingProgress, 
    promotionInfo,
    setPage, 
    setPromotionInfo,
    loadProgress, 
    verifyLevelRequirements,
    triggerSoftReset 
  } = useProgress();

  const { user, logout } = useAuth();
  const { startTopicQuiz } = useQuiz();

  // Load progress on mount or subject change
  useEffect(() => {
    loadProgress();
  }, [subject]);

  if (loadingProgress && !dashboardData) return <LoadingSpinner message="Loading learning progress profile..." />;
  if (!dashboardData) return <p className="no-data">No progress data found. Please select a subject first.</p>;

  const { current_level, plan_title, recommended_next_step, topics = [], weak_areas = [] } = dashboardData;

  const allTopicsCompleted = topics.length > 0 && topics.every(t => t.status === "done");
  const isCourseCompleted = current_level === "completed";

  const renderNextSteps = (nextStepStr) => {
    if (!nextStepStr) return null;
    let parsedArray = null;
    try {
      const parsed = JSON.parse(nextStepStr);
      if (Array.isArray(parsed)) {
        parsedArray = parsed;
      }
    } catch (e) {
      // If it's not JSON, check if it contains newline or comma separated items
      if (typeof nextStepStr === "string") {
        if (nextStepStr.includes("\n")) {
          parsedArray = nextStepStr.split("\n").map(s => s.trim()).filter(Boolean);
        } else if (nextStepStr.includes(",")) {
          parsedArray = nextStepStr.split(",").map(s => s.trim()).filter(Boolean);
        }
      }
    }

    // Helper to normalize strings for comparison (removes spaces, underscores, hyphens, lowercase)
    const cleanTopicName = (name) => {
      if (!name) return "";
      return name.replace(/[_\-\s]+/g, "").trim().toLowerCase();
    };

    if (parsedArray && parsedArray.length > 0) {
      return (
        <ul className="next-steps-list" style={{ paddingLeft: "20px", marginTop: "10px", listStyleType: "disc" }}>
          {parsedArray.map((step, idx) => {
            const cleanStep = cleanTopicName(step);
            const isTopicDone = topics.some(t => 
              cleanTopicName(t.topic) === cleanStep && t.status === "done"
            );

            return (
              <li 
                key={idx} 
                style={{ 
                  marginBottom: "6px", 
                  textTransform: "capitalize",
                  textDecoration: isTopicDone ? "line-through" : "none",
                  opacity: isTopicDone ? 0.5 : 1,
                  color: isTopicDone ? "#94a3b8" : "inherit"
                }}
              >
                {step.replace(/_/g, " ")} {isTopicDone && "✓"}
              </li>
            );
          })}
        </ul>
      );
    }

    return <p style={{ marginTop: "6px" }}>{nextStepStr}</p>;
  };

  return (
    <div className="dashboard-container selection-container">
      {/* Top Navbar */}
      <header className="navbar">
        <div className="nav-brand">
          <img src={logo} alt="Evolyn Logo" className="brand-logo" style={{ height: "40px", marginRight: "12px" }} />
          <span className="subject-badge">{subject?.toUpperCase()}</span>
        </div>
        <div className="nav-actions">
          <button onClick={() => setPage("select_subject")} className="secondary-btn">🔄 Switch Subject</button>
          <button onClick={() => setPage("reports")} className="secondary-btn">📊 Analytics</button>
          <button onClick={() => setPage("badges")} className="secondary-btn">🏅 Badges</button>
          <button onClick={() => setPage("career")} className="secondary-btn">💼 Career Hub</button>
          <button onClick={logout} className="logout-btn">Logout</button>
        </div>
      </header>

      {/* Main Content Layout */}
      <div className="dashboard-grid">
        
        {/* Right Sidebar: Profile Status & Plan */}
        <div className="dashboard-sidebar">
          
          {/* Profile overview */}
          <div className="glass-card profile-info-card">
            <div className="profile-header">
              <span className="profile-large-icon">👩‍💻</span>
              <div>
                <h3>{user?.displayName || "Learner"}</h3>
                <p>{user?.email}</p>
              </div>
            </div>
            
            <div className="status-row">
              <span>Current Level:</span>
              <span className={`level-badge ${current_level}`}>
                {isCourseCompleted ? "🎉 Completed" : (current_level === "beginner" ? "Beginner 🟢" : (current_level === "intermediate" ? "Intermediate 🟡" : "Advanced 🔴"))}
              </span>
            </div>
          </div>

          {/* Personalized Plan summary */}
          <div className="glass-card plan-summary-card">
            <h3>📋 Adaptive Study Plan</h3>
            <h4 className="plan-title">{plan_title}</h4>
            <div className="next-step-box">
              <strong>Recommended Next Step:</strong>
              {renderNextSteps(recommended_next_step)}
            </div>
          </div>

          {/* Weak areas list */}
          <div className="glass-card weak-areas-card">
            <h3>⚠️ Active Weak Areas ({weak_areas.length})</h3>
            {weak_areas.length === 0 ? (
              <p className="success-text">🎉 Excellent! No active weak areas to review.</p>
            ) : (
              <ul className="weak-list">
                {weak_areas.map((wa, idx) => (
                  <li key={idx} className="weak-item">
                    <span className="topic-name">{wa.topic}</span>
                    <span className="weakness-desc">{wa.weakness}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Left Section: Subject Topic Roadmap & Completion Details */}
        <div className="dashboard-main">
          
          {/* If Course Completed */}
          {isCourseCompleted ? (
            <div className="glass-card completion-card text-center">
              <ConfettiEffect />
              <span className="trophy-icon">🏆</span>
              <h2>🎉 Congratulations!</h2>
              <p>You have successfully completed the advanced learning path for {subject?.toUpperCase()}!</p>
              <div className="completion-options">
                <p>Features now unlocked for you:</p>
                <ul>
                  <li>✅ Review any topic across all three levels freely</li>
                  <li>✅ Browse quiz history and detailed score reports</li>
                  <li>✅ View full analytics, reports, and progress timelines</li>
                </ul>
              </div>
              
              <div className="action-buttons-row">
                <button 
                  onClick={() => triggerSoftReset()}
                  className="start-dashboard-btn reset-btn"
                >
                  🔄 Learn a New Language (Reset Active Progress)
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Learning Roadmap List */}
              <div className="glass-card roadmap-card">
                <h3>🗺️ Learning Roadmap</h3>
                <p className="subtitle">Complete topics in order. Qualify for promotion with a rolling average of 70%.</p>

                <div className="roadmap-topics">
                  {topics.map((t, idx) => {
                    const isDone = t.status === "done";
                    const isActive = t.status === "active";
                    const isLocked = t.status === "locked";
                    
                    let statusIcon = "🔒";
                    if (isDone) statusIcon = "✅";
                    else if (isActive) statusIcon = "📖";

                    return (
                      <div key={idx} className={`roadmap-item ${t.status}`}>
                        <div className="topic-meta">
                          <span className="topic-icon">{statusIcon}</span>
                          <div className="topic-details">
                            <h4>{t.topic.toUpperCase()}</h4>
                            <span className="topic-difficulty-tag">{t.difficulty}</span>
                          </div>
                        </div>

                        <div className="topic-stats">
                          <div className="stat-unit">
                            <span className="stat-label">Attempts:</span>
                            <span className="stat-val">{t.attempt_count}</span>
                          </div>
                          <div className="stat-unit">
                            <span className="stat-label">Last Score:</span>
                            <span className="stat-val">{t.last_score > 0 ? `${t.last_score.toFixed(0)}%` : "-"}</span>
                          </div>
                          <div className="stat-unit">
                            <span className="stat-label">Average:</span>
                            <span className={`stat-val rolling-val ${t.rolling_average >= 70 ? "pass" : "fail"}`}>
                              {t.rolling_average > 0 ? `${t.rolling_average.toFixed(1)}%` : "-"}
                            </span>
                          </div>
                        </div>

                        <div className="topic-action">
                          {isActive && (
                            <button 
                              onClick={() => {
                                // Save selected topic in localStorage/session
                                sessionStorage.setItem("study_topic", JSON.stringify(t));
                                setPage("learn_topic");
                              }}
                              className="study-btn"
                            >
                              Study Topic
                            </button>
                          )}
                          {isDone && (
                            <button 
                              onClick={() => {
                                sessionStorage.setItem("study_topic", JSON.stringify(t));
                                setPage("learn_topic");
                              }}
                              className="study-btn review-btn"
                            >
                              Review Topic
                            </button>
                          )}
                          {isLocked && <button className="study-btn disabled" disabled>Locked</button>}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* All topics done -> Verify promotion */}
              {allTopicsCompleted && (
                <div className="glass-card promotion-action-card text-center">
                  <h3>🎯 Level Requirements Completed!</h3>
                  <p>You have studied all level topics. Click the check button below to verify criteria for the next level.</p>
                  <button 
                    onClick={verifyLevelRequirements} 
                    className="start-dashboard-btn"
                    disabled={loadingProgress}
                  >
                    {loadingProgress ? "Verifying..." : "Check Promotion & Advance Level →"}
                  </button>
                </div>
              )}
            </>
          )}

        </div>
      </div>

      {/* Promotion/Congrats Modal */}
      {promotionInfo && (
        <div className="modal-overlay">
          <div className="glass-card modal-card congrats-card text-center">
            <ConfettiEffect />
            <span className="congrats-trophy">🎖️</span>
            <h2>Congratulations! Promoted Successfully!</h2>
            <p className="large-text">You have been promoted from level <strong>{promotionInfo.current_level.toUpperCase()}</strong></p>
            <p className="large-text">to level <strong>{promotionInfo.new_level.toUpperCase()}</strong> 🎉</p>
            
            <div className="modal-stat-box">
              <span>Achieved Level Average:</span>
              <h3>{promotionInfo.level_average.toFixed(1)}%</h3>
            </div>

            <button 
              onClick={() => {
                setPromotionInfo(null);
                loadProgress();
              }}
              className="start-dashboard-btn"
            >
              Continue to New Study Topics
            </button>
          </div>
        </div>
      )}

    </div>
  );
}

export default Dashboard;
