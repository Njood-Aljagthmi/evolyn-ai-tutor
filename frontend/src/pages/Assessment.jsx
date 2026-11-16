import React, { useEffect, useState } from "react";
import { useQuiz } from "../context/QuizContext";
import { useProgress } from "../context/ProgressContext";
import LoadingSpinner from "../components/LoadingSpinner";

export function Assessment() {
  const { 
    questions, 
    currentIndex, 
    answers, 
    loadingQuiz, 
    submitting, 
    quizResult,
    startAssessment,
    answerQuestion,
    setCurrentIndex,
    submitAssessment,
    resetQuizState
  } = useQuiz();

  const { subject, setPage } = useProgress();
  const [selectedOption, setSelectedOption] = useState("");

  // Load diagnostic test questions on start
  useEffect(() => {
    startAssessment();
    return () => resetQuizState();
  }, [subject]);

  // Sync selected answer when question index changes
  useEffect(() => {
    setSelectedOption(answers[currentIndex] || "");
  }, [currentIndex, answers]);

  const handleNext = () => {
    if (!selectedOption) {
      alert("Please select an answer to continue.");
      return;
    }
    
    answerQuestion(selectedOption);

    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setSelectedOption("");
    } else {
      // Last question -> Submit
      const updatedAnswers = [...answers];
      updatedAnswers[currentIndex] = selectedOption;
      submitAssessment(updatedAnswers);
    }
  };

  if (loadingQuiz) return <LoadingSpinner message="🤖 Evolyn AI is crafting your personalized placement test..." />;
  if (submitting) return <LoadingSpinner message="Analyzing your answers and generating your customized learning plan..." />;

  // Display results page on completion
  if (quizResult) {
    const { assigned_level, scores, weak_topics = [] } = quizResult;
    return (
      <div className="assessment-results-page selection-container">
        <div className="glass-card results-card">
          <h2>🎉 Assessment Completed!</h2>
          <p className="subtitle">Your answers have been analyzed to determine your level and build your adaptive path.</p>

          <div className="results-grid">
            <div className="level-badge-container">
              <span>Assigned Skill Level:</span>
              <span className={`level-badge ${assigned_level}`}>
                {assigned_level === "beginner" ? "Beginner 🟢" : (assigned_level === "intermediate" ? "Intermediate 🟡" : "Advanced 🔴")}
              </span>
            </div>

            <div className="scores-table">
              <h4>📊 Performance Results by Difficulty</h4>
              <div className="score-row">
                <span>Basics & Beginner Level:</span>
                <span className="bold">{scores.beginner} / 4</span>
              </div>
              <div className="score-row">
                <span>Intermediate Level:</span>
                <span className="bold">{scores.intermediate} / 4</span>
              </div>
              <div className="score-row">
                <span>Advanced Level:</span>
                <span className="bold">{scores.advanced} / 4</span>
              </div>
            </div>
          </div>

          {weak_topics.length > 0 && (
            <div className="weak-topics-section">
              <h4>⚠️ Topics Needing Focus (Weak Areas)</h4>
              <ul>
                {weak_topics.map((item, idx) => (
                  <li key={idx}>
                    <strong>{item.topic}</strong> ({item.difficulty} level)
                  </li>
                ))}
              </ul>
            </div>
          )}

          <button 
            onClick={() => {
              resetQuizState();
              setPage("dashboard");
            }}
            className="start-dashboard-btn"
          >
            Go to My Learning Path →
          </button>
        </div>
      </div>
    );
  }

  if (questions.length === 0) return <p className="no-data">Failed to generate questions. Please try again.</p>;

  const currentQuestion = questions[currentIndex];
  const progressPercent = ((currentIndex + 1) / questions.length) * 100;

  return (
    <div className="assessment-page selection-container">
      <div className="glass-card quiz-card">
        {/* Header progress info */}
        <div className="quiz-header">
          <span className="quiz-title">📝 Placement Assessment (12 Questions)</span>
          <span className="quiz-counter">Question {currentIndex + 1} of {questions.length}</span>
        </div>

        <div className="progress-bar-container">
          <div className="progress-bar-fill" style={{ width: `${progressPercent}%` }}></div>
        </div>

        <div className="question-body">
          <span className={`difficulty-indicator ${currentQuestion.difficulty}`}>
            {currentQuestion.difficulty === "beginner" ? "Beginner 🟢" : (currentQuestion.difficulty === "intermediate" ? "Intermediate 🟡" : "Advanced 🔴")}
          </span>
          <p className="topic-text">Topic: {currentQuestion.topic}</p>
          <h3 className="question-text">{currentQuestion.question}</h3>

          <div className="options-list">
            {Object.entries(currentQuestion.options).map(([key, value]) => (
              <label 
                key={key} 
                className={`option-item ${selectedOption === key ? "selected" : ""}`}
              >
                <input 
                  type="radio" 
                  name="quiz-option" 
                  value={key} 
                  checked={selectedOption === key}
                  onChange={(e) => setSelectedOption(e.target.value)}
                />
                <span className="option-letter">{key}.</span>
                <span className="option-value">{value}</span>
              </label>
            ))}
          </div>
        </div>

        <button 
          onClick={handleNext} 
          className="next-btn"
        >
          {currentIndex === questions.length - 1 ? "Finish Assessment & Generate Plan" : "Next Question →"}
        </button>
      </div>
    </div>
  );
}

export default Assessment;
