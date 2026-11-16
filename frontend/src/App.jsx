import React from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ProgressProvider, useProgress } from "./context/ProgressContext";
import { QuizProvider } from "./context/QuizContext";

import Login from "./pages/Login";
import SubjectSelection from "./pages/SubjectSelection";
import Assessment from "./pages/Assessment";
import Dashboard from "./pages/Dashboard";
import LearnTopic from "./pages/LearnTopic";
import Reports from "./pages/Reports";
import Badges from "./pages/Badges";
import CareerHub from "./pages/CareerHub";
import LoadingSpinner from "./components/LoadingSpinner";
import AIChatWidget from "./components/AIChatWidget";
import "./App.css";

function AppContent() {
  const { user, loading: authLoading } = useAuth();
  const { page } = useProgress();


  if (authLoading) {
    return <LoadingSpinner message="Getting things ready for you..." />;
  }

  // Enforce authentication
  if (!user) {
    return <Login />;
  }
  if (user.needs_subject_selection) {
    return <SubjectSelection />;
  }

  // Dynamic Routing based on Page State
  const renderPage = () => {
    switch (page) {
      case "select_subject":
        return <SubjectSelection />;
      case "assessment":
        return <Assessment />;
      case "dashboard":
        return <Dashboard />;
      case "learn_topic":
        return <LearnTopic />;
      case "reports":
        return <Reports />;
      case "badges":
        return <Badges />;
      case "career":
        return <CareerHub />;
      default:
        return <SubjectSelection />;
    }
  };

  return (
    <>
      <div className="bg-blob bg-blob-1"></div>
      <div className="bg-blob bg-blob-2"></div>
      {renderPage()}
      <AIChatWidget />
    </>
  );
}

function App() {
  return (
    <AuthProvider>
      <ProgressProvider>
        <QuizProvider>
          <AppContent />
        </QuizProvider>
      </ProgressProvider>
    </AuthProvider>
  );
}

export default App;
