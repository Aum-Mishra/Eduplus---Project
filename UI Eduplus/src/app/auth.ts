export interface StudentSession {
  studentId: number;
  name: string;
}

const AUTH_STORAGE_KEY = "eduplus-auth-student";
const AUTH_EVENT = "eduplus-auth-changed";

export function getStoredSession(): StudentSession | null {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as StudentSession;

    if (!parsed || !Number.isFinite(parsed.studentId) || parsed.studentId <= 0) {
      return null;
    }

    return {
      studentId: Number(parsed.studentId),
      name: parsed.name || `Student ${parsed.studentId}`,
    };
  } catch {
    return null;
  }
}

export function setStoredSession(session: StudentSession): void {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
  window.dispatchEvent(new CustomEvent(AUTH_EVENT));
}

export function clearStoredSession(): void {
  localStorage.removeItem(AUTH_STORAGE_KEY);
  localStorage.removeItem("lastStudentId");
  window.dispatchEvent(new CustomEvent(AUTH_EVENT));
}

export function onAuthChange(callback: () => void): () => void {
  const listener = () => callback();
  window.addEventListener(AUTH_EVENT, listener as EventListener);
  return () => window.removeEventListener(AUTH_EVENT, listener as EventListener);
}
