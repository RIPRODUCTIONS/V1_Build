"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

type Toast = { id: number; message: string; type?: "success" | "error" | "info" };

type ToastContextValue = {
  show: (message: string, type?: Toast["type"]) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const idRef = useRef(1);

  const show = useCallback((message: string, type: Toast["type"] = "info") => {
    const id = idRef.current++;
    setToasts((prev) => [...prev, { id, message, type }]);
    // auto dismiss
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  }, []);

  const value = useMemo(() => ({ show }), [show]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed right-4 top-4 z-50 space-y-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={
              "min-w-[240px] rounded px-4 py-2 shadow text-white " +
              (t.type === "success" ? "bg-green-600" : t.type === "error" ? "bg-red-600" : "bg-gray-900")
            }
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
