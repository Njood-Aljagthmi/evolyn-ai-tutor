const API_BASE_URL = "https://ai-tutoring-agent.onrender.com";

/**
 * Custom fetch wrapper with exponential backoff retry logic for resilience.
 */
async function fetchWithRetry(url, options = {}, retries = 3, delay = 1000) {
  try {
    const response = await fetch(url, options);
    
    // If rate limited or server error, trigger a retry
    if (!response.ok && (response.status === 429 || response.status >= 500)) {
      if (retries > 0) {
        // console.warn(`API temporary error (${response.status}). Retrying in ${delay}ms... (${retries} attempts left)`);
        await new Promise(resolve => setTimeout(resolve, delay));
        return fetchWithRetry(url, options, retries - 1, delay * 2);
      }
    }
    return response;
  } catch (error) {
    if (retries > 0) {
      // console.warn(`API network failure. Retrying in ${delay}ms... (${retries} attempts left)`);
      await new Promise(resolve => setTimeout(resolve, delay));
      return fetchWithRetry(url, options, retries - 1, delay * 2);
    }
    throw error;
  }
}

/**
 * Base API requester
 */
async function request(endpoint, method = "GET", body = null, token = null) {
  const headers = {
    "Content-Type": "application/json",
  };
  
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const options = {
    method,
    headers,
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetchWithRetry(`${API_BASE_URL}${endpoint}`, options);
  
  if (!response.ok) {
    let errorDetail = "API request failed";
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.message || errorDetail;
    } catch (_) {
      errorDetail = await response.text() || errorDetail;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Authentication
  auth: (idToken) => request("/api/auth", "POST", { idToken }),

  // Subject selection
  selectSubject: (learnerId, subject, token) => 
    request("/api/select_subject", "POST", { learner_id: learnerId, subject }, token),

  // Assessment
  generateAssessment: (subject, token) => 
    request(`/api/assessment/generate?subject=${subject}&_t=${Date.now()}`, "GET", null, token),
    
  submitAssessment: (learnerId, subject, quiz, answers, token) => 
    request("/api/assessment/submit", "POST", { learner_id: learnerId, subject, quiz, answers }, token),

  // Progress Dashboard
  getProgress: (learnerId, subject, token) => 
    request(`/api/progress?learner_id=${learnerId}&subject=${subject}`, "GET", null, token),

  explainTopic: (learnerId, subject, level, topic, bypassCache = false, token) => 
    request("/api/topic/explain", "POST", { learner_id: learnerId, subject, level, topic, bypass_cache: bypassCache }, token),

  generateTopicQuiz: (subject, level, topic, bypassCache, token) => 
    request("/api/topic/quiz/generate", "POST", { subject, level, topic, bypass_cache: bypassCache }, token),

  submitTopicQuiz: (learnerId, subject, level, topic, questions, answers, attemptToken, token) => 
    request("/api/topic/quiz/submit", "POST", { 
      learner_id: learnerId, 
      subject, 
      level, 
      topic, 
      questions, 
      answers, 
      attempt_token: attemptToken 
    }, token),

  // Level validation
  verifyLevel: (learnerId, subject, level, token) => 
    request("/api/level/verify", "POST", { learner_id: learnerId, subject, level }, token),

  // Reports
  getReports: (learnerId, token) => 
    request(`/api/reports?learner_id=${learnerId}`, "GET", null, token),

  // Reset
  softReset: (learnerId, subject, token) => 
    request("/api/reset", "POST", { learner_id: learnerId, subject }, token),

  // Chatbot Integration
  sendChatMessage: (learnerId, message, language, level, topK = 3) => 
    request("/chat", "POST", { learner_id: learnerId, message, language, level, top_k: topK }),

  getSession: (learnerId) => 
    request(`/session/${learnerId}`, "GET"),

  clearSession: (learnerId) => 
    request(`/session/${learnerId}`, "DELETE"),

  // ── Phase 1: Badges ──────────────────────────────────────────────────────
  getBadges: (learnerId) =>
    request(`/api/badges/${learnerId}`, "GET"),

  // ── Phase 2: GitHub OAuth ─────────────────────────────────────────────────
  // NOTE: GitHub connect redirects the browser — do window.location.href instead of fetch
  getGitHubConnectUrl: (learnerId) =>
    `https://ai-tutoring-agent.onrender.com/github/connect?learner_id=${learnerId}`,

  pushBadgeToGitHub: (learnerId, badgeId, badgeTitle, badgeEmoji, badgeColor, subject) =>
    request("/github/push-badge", "POST", {
      learner_id: learnerId,
      badge_id: badgeId,
      badge_title: badgeTitle,
      badge_emoji: badgeEmoji,
      badge_color: badgeColor,
      subject,
    }),

  // ── Phase 3: Career Hub ───────────────────────────────────────────────────
  getCareerRecommendations: (learnerId) =>
    request(`/api/career/${learnerId}`, "GET"),

  // Support Ticketing
  submitSupportTicket: (learnerId, email, category, message, token) =>
    request("/api/support/ticket", "POST", { learner_id: learnerId, email, category, message }, token),
};

export default api;

