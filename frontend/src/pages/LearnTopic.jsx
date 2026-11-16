import React, { useEffect, useState } from "react";
import { useQuiz } from "../context/QuizContext";
import { useProgress } from "../context/ProgressContext";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import LoadingSpinner from "../components/LoadingSpinner";
import logo from "../assets/logo.png";
import ConfettiEffect from "../components/ConfettiEffect";

export function LearnTopic() {
  const { idToken } = useAuth();
  const { setPage } = useProgress();
  const {
    activeQuizType,
    questions,
    currentIndex,
    answers,
    loadingQuiz,
    submitting,
    quizResult,
    setQuizResult,
    setCurrentIndex,
    startTopicQuiz,
    answerQuestion,
    submitTopicQuiz,
    resetQuizState
  } = useQuiz();

  const [topicInfo, setTopicInfo] = useState(null);
  const [step, setStep] = useState("explain"); // explain, quiz, result
  const [explanation, setExplanation] = useState("");
  const [loadingExplain, setLoadingExplain] = useState(false);
  const [selectedOption, setSelectedOption] = useState("");

  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [availableVoices, setAvailableVoices] = useState([]);
  const [selectedVoiceName, setSelectedVoiceName] = useState("");

  // Load and filter English voices
  useEffect(() => {
    const loadVoices = () => {
      const voices = window.speechSynthesis.getVoices();
      const englishVoices = voices.filter(v => v.lang.startsWith("en"));
      setAvailableVoices(englishVoices);
      
      // Auto-select the best voice (online natural neural voice if available)
      if (englishVoices.length > 0 && !selectedVoiceName) {
        const bestVoice = englishVoices.find(v => v.name.toLowerCase().includes("natural") && v.name.toLowerCase().includes("online")) ||
                           englishVoices.find(v => v.name.toLowerCase().includes("natural")) ||
                           englishVoices.find(v => v.name.toLowerCase().includes("google")) ||
                           englishVoices.find(v => v.name.toLowerCase().includes("microsoft")) ||
                           englishVoices[0];
        if (bestVoice) {
          setSelectedVoiceName(bestVoice.name);
        }
      }
    };

    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;

    return () => {
      window.speechSynthesis.onvoiceschanged = null;
      window.speechSynthesis.cancel();
    };
  }, [selectedVoiceName]);

  const cleanTextForSpeech = (text) => {
    if (!text) return "";
    // 1. Remove code blocks entirely
    let clean = text.replace(/```[\s\S]*?```/g, " [Refer to the code example shown on screen] ");
    // 2. Remove headers
    clean = clean.replace(/#+\s+/g, "");
    // 3. Remove inline code backticks
    clean = clean.replace(/`([^`]+)`/g, "$1");
    // 4. Remove bold/italic formatting
    clean = clean.replace(/\*\*([^*]+)\*\*/g, "$1");
    clean = clean.replace(/\*([^*]+)\*/g, "$1");
    clean = clean.replace(/__([^_]+)__/g, "$1");
    clean = clean.replace(/_([^_]+)_/g, "$1");
    // 5. Remove markdown links
    clean = clean.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
    // 6. Replace multiple spaces and newlines
    clean = clean.replace(/\n+/g, " ");
    return clean.trim();
  };

  const handleSpeak = () => {
    if (isSpeaking) {
      if (isPaused) {
        window.speechSynthesis.resume();
        setIsPaused(false);
      } else {
        window.speechSynthesis.pause();
        setIsPaused(true);
      }
    } else {
      window.speechSynthesis.cancel(); // Stop any ongoing speech
      const spokenText = cleanTextForSpeech(explanation);
      const utterance = new SpeechSynthesisUtterance(spokenText);
      
      // Select the user-chosen voice
      const voice = availableVoices.find(v => v.name === selectedVoiceName);
      if (voice) {
        utterance.voice = voice;
      }
      
      // Fine-tune rate for maximum clarity (slightly slower than default)
      utterance.rate = 0.95;
      
      utterance.onend = () => {
        setIsSpeaking(false);
        setIsPaused(false);
      };
      
      utterance.onerror = () => {
        setIsSpeaking(false);
        setIsPaused(false);
      };

      window.speechSynthesis.speak(utterance);
      setIsSpeaking(true);
      setIsPaused(false);
    }
  };

  const handleStopSpeech = () => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
    setIsPaused(false);
  };

  // Retrieve topic metadata on mount
  useEffect(() => {
    const raw = sessionStorage.getItem("study_topic");
    if (raw) {
      const data = jsonParseSafe(raw);
      setTopicInfo(data);
      fetchLesson(data);
    } else {
      setPage("dashboard");
    }
    return () => {
      resetQuizState();
      window.speechSynthesis.cancel(); // Clean up voice on page leave
    };
  }, []);

  // Sync selected options when indices change
  useEffect(() => {
    setSelectedOption(answers[currentIndex] || "");
  }, [currentIndex, answers]);

  const jsonParseSafe = (str) => {
    try { return JSON.parse(str); } catch (_) { return null; }
  };

  const fetchLesson = async (data, bypassCache = false) => {
    if (!idToken) return;
    setLoadingExplain(true);
    try {
      const res = await api.explainTopic(
        data.learner_id || "student",
        data.subject || "python",
        data.difficulty || "beginner",
        data.topic,
        bypassCache,
        idToken
      );
      setExplanation(res.explanation);
      setStep("explain");
    } catch (err) {
      console.error("Failed to load explanation:", err);
      setExplanation("Sorry, we encountered an error loading the lesson explanation. Please try again.");
    }
    setLoadingExplain(false);
  };

  const handleStartQuiz = async (bypass = false) => {
    if (!topicInfo) return;
    await startTopicQuiz(topicInfo.topic, topicInfo.difficulty, bypass);
    setStep("quiz");
  };

  const handleNextQuestion = () => {
    if (!selectedOption) {
      alert("Please select an option to answer.");
      return;
    }
    answerQuestion(selectedOption);

    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setSelectedOption("");
    } else {
      const updatedAnswers = [...answers];
      updatedAnswers[currentIndex] = selectedOption;
      submitTopicQuiz(updatedAnswers);
      setStep("result");
    }
  };

  // Basic regex parser to convert Markdown tags to styled elements
  const parseMarkdown = (text) => {
    if (!text) return "";
    
    // Convert code blocks
    let parsed = text.replace(/```(?:python|java|javascript|css)?\n([\s\S]*?)```/g, '<pre class="code-block"><code>$1</code></pre>');
    // Convert headings
    parsed = parsed.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    parsed = parsed.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    parsed = parsed.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    // Convert bold text
    parsed = parsed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Convert lists
    parsed = parsed.replace(/^\s*-\s*(.*$)/gim, '<li>$1</li>');
    // Convert line breaks
    parsed = parsed.split("\n").map(line => {
      if (line.trim().startsWith("<") || line.trim() === "") return line;
      return `<p>${line}</p>`;
    }).join("");

    return <div dangerouslySetInnerHTML={{ __html: parsed }} />;
  };

  if (loadingExplain) return <LoadingSpinner message="✨ Evolyn AI is generating your personalized lesson..." />;
  if (loadingQuiz) return <LoadingSpinner message="Preparing your quiz questions..." />;
  if (submitting) return <LoadingSpinner message="Submitting your quiz and grading answers..." />;

  return (
    <div className="learn-topic-container selection-container">
      {/* Navbar header */}
      <header className="navbar">
        <div className="nav-brand">
          <img src={logo} alt="Evolyn Logo" className="brand-logo" style={{ height: "40px", marginRight: "12px" }} />
          <span className="subject-badge">{topicInfo?.topic.toUpperCase()}</span>
        </div>
        <button 
          onClick={() => {
            resetQuizState();
            setPage("dashboard");
          }} 
          className="logout-btn"
        >
          Return to Dashboard
        </button>
      </header>

      {/* 1. EXPLAIN STEP */}
      {step === "explain" && (
        <div className="glass-card lesson-card">
          <div className="voice-controls-panel" style={{ display: "flex", gap: "12px", alignItems: "center", marginBottom: "20px", background: "rgba(255, 255, 255, 0.05)", padding: "12px 16px", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.1)", flexWrap: "wrap" }}>
             <button 
               onClick={handleSpeak} 
               className="secondary-btn" 
               style={{ display: "flex", alignItems: "center", gap: "8px", background: isSpeaking ? (isPaused ? "rgba(108, 92, 231, 0.2)" : "rgba(253, 121, 168, 0.2)") : "rgba(255, 255, 255, 0.1)", border: "1px solid rgba(255, 255, 255, 0.2)", cursor: "pointer", transition: "all 0.2s" }}
             >
                 {isSpeaking ? (isPaused ? "▶️ Resume" : "⏸️ Pause") : "🔊 Listen to Lesson"}
             </button>
             {isSpeaking && (
                 <button 
                   onClick={handleStopSpeech} 
                   className="secondary-btn" 
                   style={{ padding: "8px 12px", background: "rgba(225, 112, 85, 0.2)", border: "1px solid rgba(255, 255, 255, 0.2)", cursor: "pointer" }}
                 >
                     ⏹️ Stop
                 </button>
             )}
             
             {availableVoices.length > 0 && (
               <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                 <label style={{ fontSize: "11px", opacity: 0.8 }}>Choose Voice:</label>
                 <select 
                   value={selectedVoiceName} 
                   onChange={(e) => {
                     setSelectedVoiceName(e.target.value);
                     if (isSpeaking) handleStopSpeech(); // Restart with new voice
                   }}
                   style={{ 
                     background: "rgba(0, 0, 0, 0.4)", 
                     color: "#fff", 
                     border: "1px solid rgba(255, 255, 255, 0.2)", 
                     borderRadius: "4px", 
                     padding: "6px 10px", 
                     fontSize: "12px", 
                     cursor: "pointer",
                     outline: "none"
                   }}
                 >
                   {availableVoices.map((v, idx) => (
                     <option key={idx} value={v.name} style={{ background: "#2a2d42" }}>
                       {v.name.replace("Microsoft", "MS").replace("English", "EN").replace("Desktop - ", "")}
                     </option>
                   ))}
                 </select>
               </div>
             )}
             
             <span style={{ fontSize: "12px", opacity: 0.7, marginLeft: "auto", display: "flex", alignItems: "center", gap: "6px" }}>
               {isSpeaking ? (isPaused ? "Voice Paused" : "🎙️ Evolyn speaking...") : "💡 Want to listen?"}
             </span>
          </div>

          <div className="lesson-body">
            {parseMarkdown(explanation)}
          </div>
          
          <div className="lesson-divider"></div>
          
          <div className="action-buttons-row">
            <button 
              onClick={() => handleStartQuiz(false)} 
              className="start-dashboard-btn"
            >
              ✅ I Understand — Start Comprehension Quiz
            </button>
            <button 
              onClick={() => fetchLesson(topicInfo, true)} 
              className="secondary-btn"
              disabled={loadingExplain}
            >
              🔄 Re-Explain Topic
            </button>
          </div>
        </div>
      )}

      {/* 2. QUIZ STEP */}
      {step === "quiz" && questions.length > 0 && (
        <div className="glass-card quiz-card">
          <div className="quiz-header">
            <span>📝 Topic Comprehension Quiz</span>
            <span>Question {currentIndex + 1} of {questions.length}</span>
          </div>

          <div className="progress-bar-container">
            <div className="progress-bar-fill" style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}></div>
          </div>

          <div className="question-body">
            <h3 className="question-text">{questions[currentIndex].question}</h3>

            <div className="options-list">
              {Object.entries(questions[currentIndex].options).map(([key, val]) => (
                <label 
                  key={key} 
                  className={`option-item ${selectedOption === key ? "selected" : ""}`}
                >
                  <input 
                    type="radio" 
                    name="topic-option" 
                    value={key} 
                    checked={selectedOption === key}
                    onChange={(e) => setSelectedOption(e.target.value)}
                  />
                  <span className="option-letter">{key}.</span>
                  <span className="option-value">{val}</span>
                </label>
              ))}
            </div>
          </div>

          <button 
            onClick={handleNextQuestion} 
            className="next-btn"
          >
            {currentIndex === questions.length - 1 ? "Submit Answers" : "Next Question →"}
          </button>
        </div>
      )}

      {/* 3. RESULT STEP */}
      {step === "result" && quizResult && (
        <div className="glass-card results-card">
          {quizResult.grade_status === "PASS" && <ConfettiEffect />}
          <div className="text-center">
            {quizResult.grade_status === "PASS" ? (
              <span className="congrats-trophy success-color">✅</span>
            ) : (
              <span className="congrats-trophy error-color">⚠️</span>
            )}
            <h2>Quiz Score: {quizResult.score.toFixed(0)}%</h2>
            
            <p className="large-text">
              Status:{" "}
              <strong className={`status-badge ${quizResult.grade_status}`}>
                {quizResult.grade_status === "PASS" ? "PASS 🟢" : (quizResult.grade_status === "RETRY" ? "RETRY REQUIRED 🟡" : "FAIL 🔴")}
              </strong>
            </p>
          </div>

          <div className="result-stats-row">
            <div className="result-stat-card">
              <span>Total Active Attempts</span>
              <h3>{quizResult.attempt_count}</h3>
            </div>
            <div className="result-stat-card">
              <span>Topic Rolling Average</span>
              <h3 className={quizResult.rolling_average >= 70 ? "pass-text" : "fail-text"}>
                {quizResult.rolling_average.toFixed(1)}%
              </h3>
            </div>
          </div>

          {/* Feedback messages based on grade tiers */}
          <div className="feedback-message-box">
            {quizResult.grade_status === "PASS" && (
              <p>🎉 Excellent! You have successfully mastered the concepts and met the topic passing requirements. This topic is now marked as completed.</p>
            )}
            {quizResult.grade_status === "RETRY" && (
              <p>⚠️ Your score is close to passing. We recommend re-reading the explanation or retaking the quiz to improve your rolling average.</p>
            )}
            {quizResult.grade_status === "FAIL" && (
              <p>❌ Topic not passed this time. Take some time to review the explanation and code examples, then try again with a new set of questions.</p>
            )}
          </div>

          {/* Detailed questions review */}
          {questions.length > 0 && (
            <div className="wrong-questions-review">
              <h4>🔍 Review Quiz Answers</h4>
              {questions.map((q, idx) => {
                const learnerAnswer = answers[idx];
                const isCorrect = learnerAnswer === q.correct_answer;
                
                return (
                  <div key={idx} className="wrong-q-item">
                    <p className="wrong-q-text">
                      {isCorrect ? "✅" : "❌"} 📌 {q.question}
                    </p>
                    <div className="options-feedback-list">
                      {Object.entries(q.options).map(([k, v]) => {
                        let itemClass = "";
                        if (k === q.correct_answer) itemClass = "correct-choice";
                        else if (k === learnerAnswer) itemClass = "incorrect-choice";
                        
                        return (
                          <div key={k} className={`option-feedback-item ${itemClass}`}>
                            <strong>{k}.</strong> {v}
                            {k === q.correct_answer && " (Correct Answer)"}
                            {k === learnerAnswer && " (Your Answer)"}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="action-buttons-row">
            {quizResult.grade_status === "PASS" ? (
              <button 
                onClick={() => {
                  resetQuizState();
                  setPage("dashboard");
                }}
                className="start-dashboard-btn"
              >
                Return to Dashboard →
              </button>
            ) : (
              <>
                <button 
                  onClick={() => {
                    setQuizResult(null);
                    setStep("explain");
                  }}
                  className="secondary-btn"
                >
                  🔄 Review Explanation
                </button>
                <button 
                  onClick={() => handleStartQuiz(true)} 
                  className="start-dashboard-btn"
                >
                  🔄 Retake Quiz (New Questions)
                </button>
                <button 
                  onClick={() => {
                    resetQuizState();
                    setPage("dashboard");
                  }}
                  className="secondary-btn link-btn"
                >
                  Return to Dashboard
                </button>
              </>
            )}
          </div>
        </div>
      )}

    </div>
  );
}

export default LearnTopic;
