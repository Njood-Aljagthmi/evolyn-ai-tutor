import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import { useProgress } from "../context/ProgressContext";
import { api } from "../services/api";

export function AIChatWidget() {
  const { user } = useAuth();
  const { subject } = useProgress();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputVal, setInputVal] = useState("");
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [micError, setMicError] = useState("");
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  // Support Mode States
  const [viewMode, setViewMode] = useState("chat"); // "chat" or "support"
  const [supportCategory, setSupportCategory] = useState("Technical Issue");
  const [supportMessage, setSupportMessage] = useState("");
  const [supportEmail, setSupportEmail] = useState("");
  const [supportLoading, setSupportLoading] = useState(false);
  const [supportSuccess, setSupportSuccess] = useState(false);

  useEffect(() => {
    if (user?.email) {
      setSupportEmail(user.email);
    }
  }, [user]);

  const handleSupportSubmit = async (e) => {
    e.preventDefault();
    if (!supportMessage.trim() || !user?.learner_id || supportLoading) return;

    setSupportLoading(true);
    try {
      await api.submitSupportTicket(
        user.learner_id,
        supportEmail || user.email || "",
        supportCategory,
        supportMessage
      );
      setSupportSuccess(true);
      setSupportMessage("");
    } catch (err) {
      console.error("Support submission failed:", err);
      alert("Failed to submit support ticket. Please try again later.");
    } finally {
      setSupportLoading(false);
    }
  };

  // Auto-scroll to bottom of chat when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen) scrollToBottom();
  }, [messages, isOpen]);

  // Load session history when chat is opened
  useEffect(() => {
    if (isOpen && user?.learner_id) {
      loadSessionHistory();
    }
  }, [isOpen, user]);

  // Stop recognition on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const loadSessionHistory = async () => {
    try {
      const res = await api.getSession(user.learner_id);
      if (res && res.session_history) {
        setMessages(res.session_history);
      }
    } catch (err) {
      console.error("Failed to load chat history:", err);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputVal.trim() || loading || !user?.learner_id) return;

    const userText = inputVal;
    setInputVal("");

    const updatedMessages = [...messages, { role: "user", message: userText }];
    setMessages(updatedMessages);
    setLoading(true);

    try {
      const res = await api.sendChatMessage(
        user.learner_id,
        userText,
        subject || "python",
        user.skill_level || "beginner"
      );

      if (res && res.session_history) {
        setMessages(res.session_history);
      } else if (res && res.reply) {
        setMessages([...updatedMessages, { role: "assistant", message: res.reply }]);
      }
    } catch (err) {
      console.error("Chat error:", err);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", message: "Sorry, failed to connect to AI Tutor. Please try again later." }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    if (!user?.learner_id) return;
    if (window.confirm("Are you sure you want to completely clear your chat history?")) {
      try {
        await api.clearSession(user.learner_id);
        setMessages([]);
      } catch (err) {
        console.error("Failed to clear chat session:", err);
      }
    }
  };

  const handleMicClick = () => {
    setMicError("");

    // Stop if already listening
    if (isListening) {
      if (recognitionRef.current) recognitionRef.current.stop();
      setIsListening(false);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setMicError("⚠️ Voice input not supported. Please use Chrome or Edge.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;

    recognition.lang = "en-US";
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognition.continuous = false;

    recognition.onstart = () => setIsListening(true);

    recognition.onresult = (event) => {
      let transcript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      setInputVal(transcript);
    };

    recognition.onerror = (event) => {
      setIsListening(false);
      if (event.error === "not-allowed") {
        setMicError("⚠️ Microphone access denied. Allow mic permission and try again.");
      } else if (event.error !== "no-speech") {
        setMicError(`⚠️ Voice error: ${event.error}`);
      }
    };

    recognition.onend = () => setIsListening(false);

    recognition.start();
  };

  return (
    <div className="ai-chat-widget-container">
      {/* Floating Action Button */}
      <button
        className={`chat-toggle-btn ${isOpen ? "open" : ""}`}
        onClick={() => setIsOpen(!isOpen)}
        title="Chat with AI Tutor"
      >
        {isOpen ? "✖" : "💬"}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="chat-window-overlay glass-card">
          <div className="chat-window-header">
            <div className="header-info">
              <span className="bot-avatar">🤖</span>
              <div>
                <h4>AI Assistant Tutor</h4>
                <span className="online-tag">Active Now</span>
              </div>
            </div>
            <div className="header-actions">
              <button 
                type="button" 
                onClick={() => {
                  setViewMode(viewMode === "chat" ? "support" : "chat");
                  setSupportSuccess(false);
                  setSupportMessage("");
                }} 
                className="support-toggle-btn"
                title={viewMode === "chat" ? "Support / Report Issue" : "Back to Chat"}
              >
                {viewMode === "chat" ? "🛠️ Support" : "💬 Chat"}
              </button>
              {viewMode === "chat" && (
                <button onClick={handleClear} className="clear-chat-btn" title="Clear Chat">
                  🔄 Clear
                </button>
              )}
            </div>
          </div>

          {viewMode === "chat" ? (
            <>
              <div className="chat-window-messages">
                {messages.length === 0 ? (
                  <div className="empty-chat-state">
                    <span className="wave-icon">👋</span>
                    <p>Hello! I am your AI Assistant Tutor.</p>
                    <p className="empty-sub">
                      Ask me any question about {subject === "java" ? "Java" : "Python"} — by typing or using the 🎙️ microphone button!
                    </p>
                  </div>
                ) : (
                  messages.map((msg, index) => (
                    <div
                      key={index}
                      className={`message-bubble-wrapper ${msg.role === "user" ? "user-wrapper" : "bot-wrapper"}`}
                    >
                      <div className={`message-bubble ${msg.role === "user" ? "user-bubble" : "bot-bubble"}`}>
                        <p className="msg-text">{msg.message}</p>
                      </div>
                    </div>
                  ))
                )}

                {loading && (
                  <div className="message-bubble-wrapper bot-wrapper">
                    <div className="message-bubble bot-bubble loading-bubble">
                      <div className="dot-typing">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Mic error strip */}
              {micError && (
                <p style={{
                  margin: "0",
                  padding: "6px 14px",
                  fontSize: "12px",
                  color: "#f87171",
                  background: "rgba(239,68,68,0.08)",
                  borderTop: "1px solid rgba(239,68,68,0.15)"
                }}>
                  {micError}
                </p>
              )}

              <form onSubmit={handleSend} className="chat-window-input-area">
                {/* Microphone Button */}
                <button
                  type="button"
                  onClick={handleMicClick}
                  className={`chat-mic-btn ${isListening ? "mic-listening" : ""}`}
                  title={isListening ? "Stop listening" : "Speak your question"}
                  disabled={loading}
                >
                  {isListening ? "🔴" : "🎙️"}
                </button>

                <input
                  type="text"
                  placeholder={isListening ? "Listening… speak now" : "Ask a programming question..."}
                  value={inputVal}
                  onChange={(e) => setInputVal(e.target.value)}
                  disabled={loading}
                  className="chat-input-field"
                />

                <button
                  type="submit"
                  className="chat-send-btn"
                  disabled={!inputVal.trim() || loading}
                >
                  Send
                </button>
              </form>
            </>
          ) : (
            <div className="support-form-container">
              <div className="support-form-header">
                <h3>🛠️ Technical Support</h3>
                <p className="support-sub">Describe your issue and we'll get back to you via email.</p>
              </div>

              {supportSuccess ? (
                <div className="support-success-state">
                  <span className="success-checkmark">✅</span>
                  <h4>Ticket Submitted!</h4>
                  <p>We've received your ticket. We'll contact you soon at <strong>{supportEmail}</strong>.</p>
                  <button
                    type="button"
                    onClick={() => {
                      setViewMode("chat");
                      setSupportSuccess(false);
                      setSupportMessage("");
                    }}
                    className="support-back-btn"
                  >
                    Back to Chat
                  </button>
                </div>
              ) : (
                <form onSubmit={handleSupportSubmit} className="support-form">
                  <div className="support-form-group">
                    <label className="support-label">Email Address</label>
                    <input
                      type="email"
                      required
                      value={supportEmail}
                      onChange={(e) => setSupportEmail(e.target.value)}
                      placeholder="name@example.com"
                      className="support-field"
                    />
                  </div>

                  <div className="support-form-group">
                    <label className="support-label">Category</label>
                    <select
                      value={supportCategory}
                      onChange={(e) => setSupportCategory(e.target.value)}
                      className="support-field"
                    >
                      <option value="Technical Issue">Technical Issue (System Bugs, Crashes)</option>
                      <option value="Content Issue">Content Issue (Explanation, Quizzes)</option>
                      <option value="Suggestion">Suggestion / Feature Request</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>

                  <div className="support-form-group">
                    <label className="support-label">Message</label>
                    <textarea
                      required
                      rows="4"
                      value={supportMessage}
                      onChange={(e) => setSupportMessage(e.target.value)}
                      placeholder="Please describe the issue in detail..."
                      className="support-field support-textarea"
                    />
                  </div>

                  <div className="support-form-actions">
                    <button
                      type="submit"
                      disabled={supportLoading || !supportMessage.trim()}
                      className="support-submit-btn"
                    >
                      {supportLoading ? "Submitting..." : "Submit Ticket"}
                    </button>
                    <button
                      type="button"
                      onClick={() => setViewMode("chat")}
                      className="support-cancel-btn"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default AIChatWidget;
