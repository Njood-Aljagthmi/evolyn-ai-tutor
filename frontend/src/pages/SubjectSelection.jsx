import React from "react";
import { useProgress } from "../context/ProgressContext";
import { useAuth } from "../context/AuthContext";

export function SubjectSelection() {
  const { handleSelectSubject, loadingProgress } = useProgress();
  const { user, logout } = useAuth();

  return (
    <div className="selection-container">
      <header className="navbar">
        <div className="nav-profile">
          <span className="profile-icon">👤</span>
          <span>Welcome, {user?.displayName}</span>
        </div>
        <button onClick={logout} className="logout-btn">Logout</button>
      </header>

      <div className="selection-content">
        <div className="title-block">
          <h2>Choose Your Learning Path</h2>
          <p>Select a programming language to generate your personalized adaptive learning plan</p>
        </div>

        <div className="subject-cards">
          {/* Python Course Card */}
          <div 
            onClick={() => !loadingProgress && handleSelectSubject("python")}
            className="subject-card python-card"
          >
            <div className="subject-icon">🐍</div>
            <h3>Python Programming</h3>
            <p>Learn Python fundamentals, data structures, functions, OOP, and advanced concepts.</p>
            <span className="enter-btn">Start Learning →</span>
          </div>

          {/* Java Course Card */}
          <div 
            onClick={() => !loadingProgress && handleSelectSubject("java")}
            className="subject-card java-card"
          >
            <div className="subject-icon">☕</div>
            <h3>Java Programming</h3>
            <p>Study Java syntax, OOP inheritance, exceptions, JVM memory, and streams.</p>
            <span className="enter-btn">Start Learning →</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SubjectSelection;
