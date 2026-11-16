import React, { useEffect, useState } from "react";
import { useProgress } from "../context/ProgressContext";
import ReportChart from "../components/ReportChart";
import LoadingSpinner from "../components/LoadingSpinner";
import logo from "../assets/logo.png";

export function Reports() {
  const { reportsData, loadingProgress, loadReports, triggerSoftReset, setPage } = useProgress();
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  useEffect(() => {
    loadReports();
  }, []);

  if (loadingProgress && !reportsData) return <LoadingSpinner message="Analyzing learning data and compiling reports..." />;

  const { attempts = [], milestones = [] } = reportsData || {};

  const handleResetConfirm = async () => {
    setShowResetConfirm(false);
    await triggerSoftReset();
  };

  return (
    <div className="reports-page-container selection-container">
      {/* Header bar */}
      <header className="navbar">
        <div className="nav-brand">
          <img src={logo} alt="Evolyn Logo" className="brand-logo" style={{ height: "40px", marginRight: "12px" }} />
          <span className="subject-badge" style={{ background: "linear-gradient(135deg, #7D82B0, #557F8C)" }}>Reports</span>
        </div>
        <button onClick={() => setPage("dashboard")} className="logout-btn">Return to Dashboard</button>
      </header>

      {/* Main Charts & Data */}
      {reportsData ? (
        <div className="reports-content">
          
          {/* Custom SVG Analytics Graphics */}
          <ReportChart reportsData={reportsData} />

          {/* Connected Milestones Timeline */}
          {milestones.length > 0 && (
            <div className="glass-card milestones-card">
              <h3>🏆 Promotion Milestones</h3>
              <div className="milestones-timeline">
                {milestones.map((ms, idx) => (
                  <div key={idx} className="timeline-node">
                    <span className="node-icon">🏅</span>
                    <div className="node-details">
                      <p className="node-title">Promoted to level <strong>{ms.current_level.toUpperCase()}</strong></p>
                      <span className="node-date">{ms.created_at ? ms.created_at.slice(0, 16) : ""}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Historical Attempts Table Logs */}
          <div className="glass-card attempts-table-card">
            <h3>📝 Detailed Quiz Attempts Log</h3>
            <p className="subtitle">This log displays all active and past (archived) attempts to track your concept comprehension over time.</p>
            
            {attempts.length === 0 ? (
              <p className="no-data">You have not made any quiz attempts yet.</p>
            ) : (
              <div className="table-responsive">
                <table className="attempts-table">
                  <thead>
                    <tr>
                      <th>Attempt No.</th>
                      <th>Date & Time</th>
                      <th>Topic Name</th>
                      <th>Level</th>
                      <th>Achieved Score</th>
                      <th>Attempt Status</th>
                      <th>Log Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {attempts.map((att, idx) => {
                      const passStatus = att.score >= 70 ? "PASS" : (att.score >= 50 ? "RETRY" : "FAIL");
                      const isArchived = att.status === "archived";
                      
                      return (
                        <tr key={att.id || idx}>
                          <td>#{attempts.length - idx}</td>
                          <td>{att.created_at ? att.created_at.slice(0, 16) : ""}</td>
                          <td><strong>{att.topic.toUpperCase()}</strong></td>
                          <td>
                            <span className={`difficulty-badge-cell ${att.level}`}>
                              {att.level}
                            </span>
                          </td>
                          <td className="bold">{att.score.toFixed(0)}%</td>
                          <td>
                            <span className={`status-badge-cell ${passStatus}`}>
                              {passStatus === "PASS" ? "PASS 🟢" : (passStatus === "RETRY" ? "RETRY 🟡" : "FAIL 🔴")}
                            </span>
                          </td>
                          <td>
                            <span className={`archive-badge-cell ${att.status}`}>
                              {isArchived ? "Archived 📦" : "Active ⚡"}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Bottom Settings / Action zone */}
          <div className="glass-card danger-zone-card">
            <h3>🔄 Reset Course Progress (Soft Reset)</h3>
            <p>
              You can reset your current active programming course and return to select a new language.
              <strong> Note:</strong> This will clear your current active learning progress and topics,
              but it <u>will preserve all your past score records and analytical timeline graphs</u> to show your long-term improvement.
            </p>
            <button 
              onClick={() => setShowResetConfirm(true)} 
              className="start-dashboard-btn reset-danger-btn"
            >
              Reset Course Progress
            </button>
          </div>

        </div>
      ) : (
        <p className="no-data">Failed to load performance reports.</p>
      )}

      {/* Confirmation Dialog Modal */}
      {showResetConfirm && (
        <div className="modal-overlay">
          <div className="glass-card modal-card congrats-card text-center">
            <span className="congrats-trophy warning-color">⚠️</span>
            <h2>Confirm Course Reset</h2>
            <p className="large-text">Are you sure you want to clear your current progress?</p>
            <p className="caption text-center">
              You will be redirected to the subject selection page. Your current score history will be archived and preserved as historical logs.
            </p>

            <div className="action-buttons-row">
              <button 
                onClick={() => setShowResetConfirm(false)} 
                className="secondary-btn"
              >
                Cancel
              </button>
              <button 
                onClick={handleResetConfirm} 
                className="start-dashboard-btn reset-danger-btn"
              >
                Confirm & Reset Progress
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default Reports;
