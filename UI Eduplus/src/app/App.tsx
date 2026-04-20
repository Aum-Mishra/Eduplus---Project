import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router";
import { useEffect, useState } from "react";
import { ThemeProvider } from "next-themes";
import { Dashboard } from "./components/Dashboard";
import { ChatbotInterface } from "./components/ChatbotInterface";
import { AIChatbotInterface } from "./components/AIChatbotInterface";
import { PredictionResult } from "./components/PredictionResult";
import { PlacementProbability } from "./components/PlacementProbability";
import { LoginPage } from "./components/LoginPage";
import { clearStoredSession, getStoredSession, onAuthChange, setStoredSession, StudentSession } from "./auth";

export default function App() {
  const [session, setSession] = useState<StudentSession | null>(() => getStoredSession());

  useEffect(() => {
    return onAuthChange(() => {
      setSession(getStoredSession());
    });
  }, []);

  const handleLogin = (nextSession: StudentSession) => {
    setStoredSession(nextSession);
    setSession(nextSession);
  };

  const handleLogout = () => {
    clearStoredSession();
    setSession(null);
  };

  return (
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
      <Router>
        <Routes>
          <Route
            path="/login"
            element={session ? <Navigate to="/dashboard" replace /> : <LoginPage onLogin={handleLogin} />}
          />

          <Route
            path="/"
            element={session ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />}
          />

          <Route
            path="/dashboard"
            element={session ? <Dashboard session={session} onLogout={handleLogout} /> : <Navigate to="/login" replace />}
          />
          <Route
            path="/chatbot"
            element={session ? <ChatbotInterface session={session} onLogout={handleLogout} /> : <Navigate to="/login" replace />}
          />
          <Route
            path="/ai-chatbot"
            element={session ? <AIChatbotInterface session={session} onLogout={handleLogout} /> : <Navigate to="/login" replace />}
          />
          <Route
            path="/predictions"
            element={session ? <PredictionResult session={session} /> : <Navigate to="/login" replace />}
          />
          <Route
            path="/placement-probability"
            element={session ? <PlacementProbability session={session} /> : <Navigate to="/login" replace />}
          />

          <Route path="*" element={<Navigate to={session ? "/dashboard" : "/login"} replace />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}