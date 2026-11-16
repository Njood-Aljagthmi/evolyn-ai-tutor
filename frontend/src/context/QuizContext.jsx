import { createContext, useContext, useState } from "react";
import { useAuth } from "./AuthContext";
import { useProgress } from "./ProgressContext";
import { api } from "../services/api";

const QuizContext = createContext();

export function QuizProvider({ children }) {
  const { user, idToken, setUser } = useAuth();
  const { subject, loadProgress, setPage } = useProgress();
  
  const [activeQuizType, setActiveQuizType] = useState(null); // assessment, topic
  const [topicName, setTopicName] = useState("");
  const [topicLevel, setTopicLevel] = useState("");
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState([]); // Array for answers
  const [attemptToken, setAttemptToken] = useState(null);
  
  const [loadingQuiz, setLoadingQuiz] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [quizResult, setQuizResult] = useState(null);

  // Setup Assessment Quiz
  const startAssessment = async () => {
    if (!subject || !idToken) return;
    setLoadingQuiz(true);
    setQuizResult(null);
    try {
      const data = await api.generateAssessment(subject, idToken);
      // Flatten questions: 4 beginner, 4 intermediate, 4 advanced
      const flattened = [
        ...data.beginner,
        ...data.intermediate,
        ...data.advanced
      ];
      setQuestions(flattened);
      setCurrentIndex(0);
      setAnswers(Array(flattened.length).fill(""));
      setActiveQuizType("assessment");
    } catch (err) {
      console.error("Failed to load assessment:", err);
      alert("An error occurred while loading the assessment quiz. Please try again later.");
    }
    setLoadingQuiz(false);
  };

  // Setup Topic Quiz
  const startTopicQuiz = async (name, level, bypassCache = false) => {
    if (!subject || !idToken) return;
    setLoadingQuiz(true);
    setQuizResult(null);
    setTopicName(name);
    setTopicLevel(level);
    try {
      const data = await api.generateTopicQuiz(subject, level, name, bypassCache, idToken);
      setQuestions(data.questions);
      setAttemptToken(data.attempt_token);
      setCurrentIndex(0);
      setAnswers(Array(data.questions.length).fill(""));
      setActiveQuizType("topic");
    } catch (err) {
      console.error("Failed to load topic quiz:", err);
      alert("An error occurred while loading the topic quiz. Please try again later.");
    }
    setLoadingQuiz(false);
  };

  const answerQuestion = (choice) => {
    setAnswers(prev => {
      const updated = [...prev];
      updated[currentIndex] = choice;
      return updated;
    });
  };

  const submitAssessment = async (answersOverride) => {
    if (!user || !subject || !idToken) return;
    setSubmitting(true);
    try {
      const finalAnswers = answersOverride || answers;
      // Re-group user answers by difficulty
      const quizData = {
        beginner: questions.slice(0, 4),
        intermediate: questions.slice(4, 8),
        advanced: questions.slice(8, 12)
      };
      
      const userAnswersData = {
        beginner: finalAnswers.slice(0, 4),
        intermediate: finalAnswers.slice(4, 8),
        advanced: finalAnswers.slice(8, 12)
      };

      const result = await api.submitAssessment(
        user.learner_id,
        subject,
        quizData,
        userAnswersData,
        idToken
      );

      setQuizResult(result);
      setUser(prev => ({ ...prev, skill_level: result.assigned_level }));
      await loadProgress();
    } catch (err) {
      console.error("Assessment submission failed:", err);
      alert("Failed to submit the assessment. Please try again.");
    }
    setSubmitting(false);
  };

  const submitTopicQuiz = async (answersOverride) => {
    if (!user || !subject || !idToken) return;
    setSubmitting(true);
    try {
      const finalAnswers = answersOverride || answers;
      const result = await api.submitTopicQuiz(
        user.learner_id,
        subject,
        topicLevel,
        topicName,
        questions,
        finalAnswers,
        attemptToken,
        idToken
      );
      setQuizResult(result);
      await loadProgress();
    } catch (err) {
      console.error("Quiz submission failed:", err);
      alert(err.message || "Failed to submit the quiz. It might have already been submitted.");
    }
    setSubmitting(false);
  };

  const resetQuizState = () => {
    setQuestions([]);
    setCurrentIndex(0);
    setAnswers([]);
    setQuizResult(null);
    setAttemptToken(null);
    setActiveQuizType(null);
  };

  return (
    <QuizContext.Provider value={{
      activeQuizType,
      topicName,
      topicLevel,
      questions,
      currentIndex,
      answers,
      loadingQuiz,
      submitting,
      quizResult,
      setQuizResult,
      setCurrentIndex,
      startAssessment,
      startTopicQuiz,
      answerQuestion,
      submitAssessment,
      submitTopicQuiz,
      resetQuizState
    }}>
      {children}
    </QuizContext.Provider>
  );
}

export function useQuiz() {
  return useContext(QuizContext);
}
