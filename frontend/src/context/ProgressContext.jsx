import { createContext, useContext, useState, useEffect } from "react";
import { useAuth } from "./AuthContext";
import { api } from "../services/api";

const ProgressContext = createContext();

export function ProgressProvider({ children }) {
  const { user, idToken, setUser } = useAuth();
  const [subject, setSubject] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [reportsData, setReportsData] = useState(null);
  const [loadingProgress, setLoadingProgress] = useState(false);
  const [page, setPage] = useState("select_subject"); // select_subject, assessment, dashboard, learn_topic, reports
  const [promotionInfo, setPromotionInfo] = useState(null); // Displays congratulations popup

  // Hydrate page routing based on user state
  useEffect(() => {
    const hydrateRoute = async () => {
      if (user && !subject) {
        if (user.skill_level === "completed") {
          setPage("dashboard"); // Allow course completion review
        } else if (user.goal) {
          const matchedSubject = user.goal.toLowerCase().includes("python") ? "python" : (user.goal.toLowerCase().includes("java") ? "java" : null);
          if (matchedSubject) {
            try {
              const progress = await api.getProgress(user.learner_id, matchedSubject, idToken);
              setDashboardData(progress);
              setSubject(matchedSubject);
              if (!progress.assessment_taken) {
                setPage("assessment");
              } else {
                setPage("dashboard");
              }
            } catch (e) {
              setPage("select_subject");
            }
          } else {
            setPage("select_subject");
          }
        } else {
          setPage("select_subject");
        }
      }
    };
    hydrateRoute();
  }, [user, subject, idToken]);

  const loadProgress = async (currentSubject = subject) => {
    if (!user || !currentSubject || !idToken) return;
    setLoadingProgress(true);
    try {
      const data = await api.getProgress(user.learner_id, currentSubject, idToken);
      setDashboardData(data);
      // Sync level with profile state
      if (user.skill_level !== data.current_level) {
        setUser(prev => ({ ...prev, skill_level: data.current_level }));
      }
    } catch (err) {
      console.error("Failed to load progress:", err);
    }
    setLoadingProgress(false);
  };

  const handleSelectSubject = async (selectedSubject) => {
    if (!user || !idToken) return;
    setLoadingProgress(true);
    try {
      await api.selectSubject(user.learner_id, selectedSubject, idToken);
      setUser(prev => ({ 
        ...prev, 
        goal: `Master ${selectedSubject.toUpperCase()} programming`,
        needs_subject_selection: false
      }));
      setSubject(selectedSubject);

      // Check if user has taken assessment for this subject
      const progress = await api.getProgress(user.learner_id, selectedSubject, idToken);
      setDashboardData(progress);

      if (!progress.assessment_taken) {
        setPage("assessment");
      } else {
        setPage("dashboard");
      }
    } catch (err) {
      console.error("Subject selection failed:", err);
    }
    setLoadingProgress(false);
  };

  const loadReports = async () => {
    if (!user || !idToken) return;
    setLoadingProgress(true);
    try {
      const reports = await api.getReports(user.learner_id, idToken);
      setReportsData(reports);
    } catch (err) {
      console.error("Failed to load reports:", err);
    }
    setLoadingProgress(false);
  };

  const triggerSoftReset = async () => {
    if (!user || !subject || !idToken) return;
    setLoadingProgress(true);
    try {
      await api.softReset(user.learner_id, subject, idToken);
      setUser(prev => ({ 
        ...prev, 
        skill_level: "beginner", 
        goal: null,
        needs_subject_selection: true
      }));
      setSubject(null);
      setDashboardData(null);
      setReportsData(null);
      setPage("select_subject");
    } catch (err) {
      console.error("Soft reset failed:", err);
    }
    setLoadingProgress(false);
  };

  const verifyLevelRequirements = async () => {
    if (!user || !subject || !idToken) return;
    setLoadingProgress(true);
    try {
      const result = await api.verifyLevel(user.learner_id, subject, user.skill_level, idToken);
      if (result.status === "promoted") {
        setPromotionInfo(result);
        setUser(prev => ({ ...prev, skill_level: result.new_level }));
        await loadProgress();
      } else {
        alert(`You have completed all topics for this level, but your current average is ${result.level_average.toFixed(1)}%. You need at least 70% to level up. Please review the topics you found challenging and try again.`);
        await loadProgress();
      }
    } catch (err) {
      console.error("Failed to verify level progression:", err);
    }
    setLoadingProgress(false);
  };

  return (
    <ProgressContext.Provider value={{
      subject,
      dashboardData,
      reportsData,
      loadingProgress,
      page,
      promotionInfo,
      setPage,
      setPromotionInfo,
      loadProgress,
      handleSelectSubject,
      loadReports,
      triggerSoftReset,
      verifyLevelRequirements
    }}>
      {children}
    </ProgressContext.Provider>
  );
}

export function useProgress() {
  return useContext(ProgressContext);
}
