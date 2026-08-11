import { useState } from "react";
import { AlertCircle, Eye, EyeOff, Loader2, Lock, User } from "lucide-react";
import { motion } from "motion/react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { StudentSession } from "../auth";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

interface LoginPageProps {
  onLogin: (session: StudentSession) => void;
}

export function LoginPage({ onLogin }: LoginPageProps) {
  const [studentId, setStudentId] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    const trimmedId = studentId.trim();
    const trimmedPassword = password.trim();

    if (!trimmedId || !trimmedPassword) {
      setError("Please enter Student ID and password");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: trimmedId, password: trimmedPassword }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        setError(data?.message || "Login failed");
        return;
      }

      onLogin({
        studentId: Number(data.student_id),
        name: data.name || `Student ${data.student_id}`,
      });
    } catch (err) {
      setError(`Unable to login: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#ececec] flex items-center justify-center p-4 sm:p-8">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: "easeOut" }}
        className="w-full max-w-[1400px]"
      >
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-16 items-start">
          <section className="lg:col-span-6 xl:col-span-7 order-2 lg:order-1">
            <div className="bg-gradient-to-br from-[#c8dfeb] via-[#c1dae8] to-[#a6c8da] rounded-sm border border-[#bdd4e1] shadow-sm min-h-[320px] relative overflow-hidden p-8 md:p-10">
              <div className="absolute inset-0 opacity-25 pointer-events-none" style={{
                backgroundImage:
                  "radial-gradient(circle at 10% 15%, #ffbf4d 2.5px, transparent 3px), radial-gradient(circle at 30% 10%, #ffc466 2.5px, transparent 3px), radial-gradient(circle at 50% 20%, #eab95f 2.5px, transparent 3px), radial-gradient(circle at 75% 12%, #f9cc73 2.5px, transparent 3px), radial-gradient(circle at 90% 22%, #e2b258 2.5px, transparent 3px)"
              }} />

              <div className="relative z-10">
                <div className="inline-flex items-end gap-2 mb-4">
                  <span className="text-5xl md:text-6xl font-black text-[#2d3f9b] leading-none">eduplus</span>
                  <span className="text-sm font-semibold bg-[#f39d34] text-white px-2 py-1 rounded">campus</span>
                </div>

                <p className="text-[#3a4fae] text-xl md:text-2xl font-bold">Revolutionising Education!</p>

                <div className="mt-8 grid grid-cols-1 sm:grid-cols-5 gap-6 items-center">
                  <div className="sm:col-span-3">
                    <p className="text-[96px] md:text-[120px] leading-none font-black text-[#2d3f9b]">100+</p>
                    <p className="text-4xl md:text-5xl font-black text-[#2d3f9b] leading-tight">HAPPY CLIENTS</p>
                    <p className="text-4xl md:text-5xl font-black text-[#b45b2d] leading-tight">ONBOARDED!</p>
                  </div>

                  <div className="sm:col-span-2 rounded-2xl border-2 border-[#6d76c5] bg-white/80 p-5">
                    <p className="text-[#f08f1a] text-4xl font-black leading-none">1L+</p>
                    <p className="text-[#4a56ad] text-2xl font-bold mb-2">Learners</p>
                    <div className="h-px bg-[#f1a95a] my-2" />
                    <p className="text-[#f08f1a] text-4xl font-black leading-none">50+</p>
                    <p className="text-[#4a56ad] text-2xl font-bold">Modules</p>
                  </div>
                </div>

                <div className="mt-8 inline-block rounded-full bg-[#3d4ca8] text-white px-6 py-2 text-xl font-semibold">
                  Thank you for trusting us.
                </div>

                <div className="mt-10 pt-4 border-t border-dashed border-[#3b82f6]">
                  <p className="text-[#2f80ed] text-4xl md:text-5xl font-black">Get in Touch</p>
                </div>
              </div>
            </div>

            <div className="mt-4 text-sm text-muted-foreground lg:hidden text-center">
              Unified student access portal
            </div>
          </section>

          <section className="lg:col-span-6 xl:col-span-5 order-1 lg:order-2 px-2 sm:px-6 lg:px-0">
            <div className="max-w-[660px] mx-auto">
              <div className="text-center mb-8">
                <div className="mx-auto h-14 w-14 rounded-sm bg-gradient-to-br from-[#0ca6df] to-[#2f52b5] flex items-center justify-center text-white font-black text-xl">
                  VI
                </div>
                <h1 className="text-[#233dc7] text-4xl md:text-5xl font-bold mt-6">Student Sign-In</h1>
              </div>

              <div className="space-y-6">
                <div>
                  <label className="block text-[#858585] text-xl mb-1.5">Username</label>
                  <div className="relative">
                    <User className="w-7 h-7 absolute -left-10 top-1/2 -translate-y-1/2 text-[#7c7c7c]" />
                    <Input
                      type="number"
                      placeholder="Enter Student ID"
                      className="h-16 text-3xl border border-[#c8ced9] bg-[#d7dde8] rounded-none focus-visible:ring-1 focus-visible:ring-[#2e69c8]"
                      value={studentId}
                      onChange={(e) => {
                        setStudentId(e.target.value);
                        setError(null);
                      }}
                      onKeyDown={(e) => e.key === "Enter" && handleLogin()}
                      disabled={loading}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[#858585] text-xl mb-1.5">Password</label>
                  <div className="relative">
                    <Lock className="w-7 h-7 absolute -left-10 top-1/2 -translate-y-1/2 text-[#7c7c7c]" />
                    <Input
                      type={showPassword ? "text" : "password"}
                      placeholder="Password"
                      className="h-16 text-3xl border border-[#c8ced9] bg-[#d7dde8] rounded-none pr-12 focus-visible:ring-1 focus-visible:ring-[#2e69c8]"
                      value={password}
                      onChange={(e) => {
                        setPassword(e.target.value);
                        setError(null);
                      }}
                      onKeyDown={(e) => e.key === "Enter" && handleLogin()}
                      disabled={loading}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((v) => !v)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[#7c7c7c]"
                      disabled={loading}
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? <EyeOff className="w-6 h-6" /> : <Eye className="w-6 h-6" />}
                    </button>
                  </div>
                </div>

                {error && (
                  <div className="p-3 rounded-sm bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-2">
                    <AlertCircle className="w-4 h-4" />
                    {error}
                  </div>
                )}

                <div className="text-center pt-1">
                  <Button
                    className="h-14 px-10 rounded-full bg-[#2a69c5] hover:bg-[#2158a8] text-white text-2xl tracking-wide shadow-md"
                    onClick={handleLogin}
                    disabled={loading}
                  >
                    {loading ? <Loader2 className="w-5 h-5 mr-2 animate-spin" /> : null}
                    SIGN IN
                  </Button>
                </div>

                <div className="flex items-center justify-between pt-4 text-[#2f4b82] text-3xl">
                  <button type="button" className="underline underline-offset-2 hover:text-[#1f3660]">Help</button>
                  <button type="button" className="underline underline-offset-2 hover:text-[#1f3660]">Forgot Password?</button>
                </div>

                <div className="flex items-center justify-center gap-4 pt-2">
                  <div className="border border-[#b9b9b9] rounded-lg px-4 py-2 bg-white text-base text-[#3d3d3d] font-medium">Google Play</div>
                  <div className="border border-[#b9b9b9] rounded-lg px-4 py-2 bg-white text-base text-[#3d3d3d] font-medium">App Store</div>
                </div>

                <p className="text-center text-xs text-muted-foreground pt-2">
                  Demo auth: password must match your Student ID.
                </p>
              </div>
            </div>
          </section>
        </div>
      </motion.div>
    </div>
  );
}
