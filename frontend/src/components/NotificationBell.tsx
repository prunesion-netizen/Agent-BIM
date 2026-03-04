/**
 * NotificationBell — Clopoțel notificări cu dropdown panel și polling.
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "../contexts/AuthProvider";

type Notification = {
  id: number;
  project_id: number | null;
  category: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string | null;
};

const CATEGORY_ICONS: Record<string, string> = {
  bep: "\u{1F4CB}",
  verification: "\u{1F50D}",
  cde_change: "\u{1F4C1}",
  clash: "\u{26A0}\uFE0F",
  deadline: "\u{23F0}",
  info: "\u{2139}\uFE0F",
};

function timeAgo(iso: string | null): string {
  if (!iso) return "";
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "acum";
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h`;
  const days = Math.floor(hrs / 24);
  return `${days}z`;
}

export default function NotificationBell() {
  const { authFetch, token } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [open, setOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  const fetchCount = useCallback(async () => {
    if (!token) return;
    try {
      const res = await authFetch("/api/notifications/count");
      if (res.ok) {
        const data = await res.json();
        setUnreadCount(data.unread_count);
      }
    } catch {
      // silent
    }
  }, [authFetch, token]);

  const fetchNotifications = useCallback(async () => {
    if (!token) return;
    try {
      const res = await authFetch("/api/notifications?limit=20");
      if (res.ok) {
        const data: Notification[] = await res.json();
        setNotifications(data);
        setUnreadCount(data.filter((n) => !n.is_read).length);
      }
    } catch {
      // silent
    }
  }, [authFetch, token]);

  // Poll every 30s
  useEffect(() => {
    fetchCount();
    const interval = setInterval(fetchCount, 30000);
    return () => clearInterval(interval);
  }, [fetchCount]);

  // Load full list when opening
  useEffect(() => {
    if (open) fetchNotifications();
  }, [open, fetchNotifications]);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  const markRead = async (id: number) => {
    try {
      await authFetch(`/api/notifications/${id}/read`, { method: "POST" });
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch {
      // silent
    }
  };

  const markAllRead = async () => {
    try {
      await authFetch("/api/notifications/read-all", { method: "POST" });
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch {
      // silent
    }
  };

  return (
    <div className="notif-bell-container" ref={panelRef}>
      <button
        className="notif-bell-btn"
        onClick={() => setOpen(!open)}
        title="Notificari"
        aria-label={`Notificari${unreadCount > 0 ? ` (${unreadCount} necitite)` : ""}`}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {unreadCount > 0 && (
          <span className="notif-bell-badge">{unreadCount > 9 ? "9+" : unreadCount}</span>
        )}
      </button>

      {open && (
        <div className="notif-panel">
          <div className="notif-panel-header">
            <span className="notif-panel-title">Notificari</span>
            {unreadCount > 0 && (
              <button className="notif-mark-all" onClick={markAllRead}>
                Marcheaza toate citite
              </button>
            )}
          </div>

          <div className="notif-panel-list">
            {notifications.length === 0 ? (
              <div className="notif-empty">Nicio notificare.</div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`notif-item ${n.is_read ? "notif-read" : "notif-unread"}`}
                  onClick={() => !n.is_read && markRead(n.id)}
                >
                  <span className="notif-item-icon">
                    {CATEGORY_ICONS[n.category] || CATEGORY_ICONS.info}
                  </span>
                  <div className="notif-item-body">
                    <div className="notif-item-title">{n.title}</div>
                    <div className="notif-item-msg">{n.message}</div>
                  </div>
                  <span className="notif-item-time">{timeAgo(n.created_at)}</span>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
