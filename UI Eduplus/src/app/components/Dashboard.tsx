import { useEffect, useMemo, useState } from "react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Progress } from "./ui/progress";
import { Brain, Bell, LogOut, MessageSquare, BarChart3, FileText, TrendingUp, Home, Target, Building2, Clock, ChevronRight, Zap, Bot } from "lucide-react";
import { Link } from "react-router";
import { motion } from "motion/react";
import { StudentSession } from "../auth";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

interface DashboardProps {
  session: StudentSession;
  onLogout: () => void;
}

interface PredictionSnapshot {
  overall_placement_probability?: number;
  predicted_salary_lpa?: number;
  recommended_companies?: string | string[];
  predicted_job_role?: string;
}

interface ChatSession {
  chat_id: string;
  title: string;
  updated_at: string;
}

export function Dashboard({ session, onLogout }: DashboardProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [prediction, setPrediction] = useState<PredictionSnapshot | null>(null);
  const [recentChats, setRecentChats] = useState<ChatSession[]>([]);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        const [predictionResponse, historyResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/predictions/${session.studentId}`),
          fetch(`${API_BASE_URL}/chat-history/${session.studentId}`),
        ]);

        const predictionData = await predictionResponse.json();
        if (predictionResponse.ok && predictionData?.predictions) {
          setPrediction(predictionData.predictions);
        } else {
          setPrediction(null);
        }

        const historyData = await historyResponse.json();
        if (historyResponse.ok && Array.isArray(historyData?.chats)) {
          setRecentChats(historyData.chats.slice(0, 3));
        } else {
          setRecentChats([]);
        }
      } catch {
        setPrediction(null);
        setRecentChats([]);
      }
    };

    loadDashboardData();
  }, [session.studentId]);

  const recommendedCompanies = useMemo(() => {
    if (!prediction?.recommended_companies) return [] as string[];
    if (Array.isArray(prediction.recommended_companies)) return prediction.recommended_companies;
    return prediction.recommended_companies.split(",").map((c) => c.trim()).filter(Boolean);
  }, [prediction?.recommended_companies]);

  const placementValue = Math.round(prediction?.overall_placement_probability || 0);
  const salaryValue = prediction?.predicted_salary_lpa || 0;
  const roleReady = prediction?.predicted_job_role ? 100 : 0;

  const stats = [
    {
      label: "Placement Probability",
      value: placementValue,
      icon: Target,
      color: "from-[#003366] to-[#0055A4]",
      suffix: "%",
    },
    {
      label: "Predicted Salary",
      value: Number(salaryValue.toFixed(1)),
      icon: TrendingUp,
      color: "from-[#10B981] to-[#059669]",
      suffix: " LPA",
    },
    {
      label: "Eligible Companies",
      value: recommendedCompanies.length,
      icon: Building2,
      color: "from-[#FFC107] to-[#F59E0B]",
      suffix: "",
    },
    {
      label: "Prediction Readiness",
      value: roleReady,
      icon: BarChart3,
      color: "from-[#8B5CF6] to-[#7C3AED]",
      suffix: "%",
    },
  ];

  const navItems = [
    { icon: Home, label: "Dashboard", path: "/dashboard", active: true },
    { icon: Zap, label: "Placement Probability", path: "/placement-probability" },
    { icon: MessageSquare, label: "Chatbot", path: "/chatbot" },
    { icon: Bot, label: "AI Chatbot", path: "/ai-chatbot" },
    { icon: FileText, label: "My Predictions", path: "/predictions" },
  ];

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-card border-r border-border transition-all duration-300 hidden lg:flex flex-col`}>
        <div className="p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-[#003366] to-[#0055A4] rounded-xl flex items-center justify-center shrink-0">
              <Brain className="w-6 h-6 text-white" />
            </div>
            {sidebarOpen && (
              <div>
                <h1 className="text-lg" style={{ fontWeight: 700 }}>PlacementAI</h1>
                <p className="text-xs text-muted-foreground">Student Portal</p>
              </div>
            )}
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => (
            <Link key={item.label} to={item.path}>
              <button
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  item.active 
                    ? 'bg-primary text-primary-foreground' 
                    : 'hover:bg-muted text-foreground'
                }`}
              >
                <item.icon className="w-5 h-5 shrink-0" />
                {sidebarOpen && <span>{item.label}</span>}
              </button>
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t border-border">
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-destructive/10 text-destructive transition-colors" onClick={onLogout}>
            <LogOut className="w-5 h-5 shrink-0" />
            {sidebarOpen && <span>Logout</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Navbar */}
        <header className="bg-card border-b border-border px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
                <h2 className="text-2xl" style={{ fontWeight: 700 }}>Dashboard</h2>
              <p className="text-sm text-muted-foreground">Welcome back, {session.name} (ID: {session.studentId})</p>
            </div>
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" className="relative">
                <Bell className="w-5 h-5" />
                <span className="absolute top-2 right-2 w-2 h-2 bg-destructive rounded-full"></span>
              </Button>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-[#003366] to-[#0055A4] rounded-full flex items-center justify-center text-white">
                  {session.name?.charAt(0)?.toUpperCase() || "S"}
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <main className="flex-1 overflow-auto p-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {stats.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="p-6 hover:shadow-lg transition-shadow duration-300">
                  <div className="flex items-start justify-between mb-4">
                    <div className={`w-12 h-12 bg-gradient-to-br ${stat.color} rounded-xl flex items-center justify-center`}>
                      <stat.icon className="w-6 h-6 text-white" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">{stat.label}</p>
                    <p className="text-3xl" style={{ fontWeight: 700 }}>
                      {stat.value}{stat.suffix}
                    </p>
                    {typeof stat.value === "number" && stat.suffix === "%" && (
                      <Progress value={stat.value} className="h-2" />
                    )}
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recent Chat History */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-xl" style={{ fontWeight: 600 }}>Recent Chat History</h3>
                  <p className="text-sm text-muted-foreground">Your latest AI conversations</p>
                </div>
                <Link to="/chatbot">
                  <Button variant="ghost" size="sm">
                    View All
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </Link>
              </div>
              <div className="space-y-4">
                {recentChats.map((chat) => (
                  <div key={chat.chat_id} className="flex items-start gap-4 p-4 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer">
                    <div className="w-10 h-10 bg-gradient-to-br from-[#003366] to-[#0055A4] rounded-lg flex items-center justify-center shrink-0">
                      <MessageSquare className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="truncate mb-1" style={{ fontWeight: 500 }}>{chat.title}</p>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Clock className="w-3 h-3" />
                        <span>{new Date(chat.updated_at).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                ))}
                {recentChats.length === 0 && (
                  <p className="text-sm text-muted-foreground">No chat history for this student yet.</p>
                )}
              </div>
            </Card>

            {/* Personalized Companies */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-xl" style={{ fontWeight: 600 }}>Recommended Companies</h3>
                  <p className="text-sm text-muted-foreground">Based on your latest prediction</p>
                </div>
                <Button variant="ghost" size="sm">
                  View All
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
              <div className="space-y-3">
                {recommendedCompanies.map((company, index) => (
                  <div key={index} className="flex items-center justify-between p-4 rounded-lg border border-border hover:border-primary/50 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="text-2xl">🏢</div>
                      <div>
                        <p style={{ fontWeight: 600 }}>{company}</p>
                        <p className="text-sm text-muted-foreground">Recommended profile match</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm" style={{ fontWeight: 600, color: '#10B981' }}>Top Match</p>
                    </div>
                  </div>
                ))}
                {recommendedCompanies.length === 0 && (
                  <p className="text-sm text-muted-foreground">
                    No personalized company recommendations yet. Generate a prediction first.
                  </p>
                )}
              </div>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
}