import { useState, useEffect, useCallback } from 'react';
import { X, CheckCircle, AlertTriangle, XCircle, Info } from 'lucide-react';
import { clsx } from 'clsx';

export type ToastType = 'success' | 'warning' | 'error' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
}

const icons = {
  success: CheckCircle,
  warning: AlertTriangle,
  error: XCircle,
  info: Info,
};

const colors = {
  success: 'border-status-success/30 bg-status-success/10 text-status-success',
  warning: 'border-severity-medium/30 bg-severity-medium/10 text-severity-medium',
  error: 'border-severity-critical/30 bg-severity-critical/10 text-severity-critical',
  info: 'border-accent/30 bg-accent/10 text-accent',
};

// Globaler Toast-State (einfach, kein Zustand-Store nötig)
let addToastFn: ((toast: Omit<Toast, 'id'>) => void) | null = null;

export function showToast(type: ToastType, title: string, message?: string) {
  addToastFn?.({ type, title, message });
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = Date.now().toString(36) + Math.random().toString(36).slice(2);
    setToasts(prev => [...prev, { ...toast, id }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 5000);
  }, []);

  useEffect(() => {
    addToastFn = addToast;
    return () => { addToastFn = null; };
  }, [addToast]);

  const dismiss = (id: string) => setToasts(prev => prev.filter(t => t.id !== id));

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map(toast => {
        const Icon = icons[toast.type];
        return (
          <div
            key={toast.id}
            className={clsx(
              'flex items-start gap-3 rounded-lg border p-3 shadow-lg backdrop-blur-sm',
              'animate-[slideIn_0.2s_ease-out] bg-bg-elevated',
              colors[toast.type],
            )}
          >
            <Icon size={16} className="shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary">{toast.title}</p>
              {toast.message && (
                <p className="text-xs text-text-secondary mt-0.5">{toast.message}</p>
              )}
            </div>
            <button onClick={() => dismiss(toast.id)} className="shrink-0 text-text-tertiary hover:text-text-primary">
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
