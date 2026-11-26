export interface AppNotification {
  id: string;
  title: string;
  message: string;
  timestamp: string;
  type: 'absence' | 'shortage' | 'solver' | 'recovery' | 'system';
  severity: 'danger' | 'warning' | 'success' | 'info';
  actionUrl?: string;
  actionLabel?: string;
  read: boolean;
}

const STORAGE_KEY = 'ordivanta_notifications_store';
const EVENT_KEY = 'ordivanta-notification-update';

export const INITIAL_NOTIFICATIONS: AppNotification[] = [
  {
    id: 'notif_absence_marcus',
    title: 'Absence Call-Out: Marcus Vance',
    message: 'Robotic Welding Specialist reported medical leave on Cell 03. Immediate shift gap replacement required.',
    timestamp: '10m ago',
    type: 'absence',
    severity: 'danger',
    actionUrl: '/dashboard#action-queue',
    actionLabel: 'Assign Replacement',
    read: false,
  },
  {
    id: 'notif_shortage_welding',
    title: 'Critical Specialist Bottleneck',
    message: 'Only 3 certified Welding Level 4 technicians available across night shifts. Minimum 4 required.',
    timestamp: '25m ago',
    type: 'shortage',
    severity: 'warning',
    actionUrl: '/dashboard#bottleneck-matrix',
    actionLabel: 'Inspect Cell 03',
    read: false,
  },
  {
    id: 'notif_ot_david',
    title: 'Voluntary Overtime Consent Received',
    message: 'David Kim opted in for up to 8.0h voluntary overtime for upcoming production line surge.',
    timestamp: '1h ago',
    type: 'system',
    severity: 'info',
    actionUrl: '/worker?worker=emp_david',
    actionLabel: 'View Worker Record',
    read: true,
  },
];

export function getNotifications(): AppNotification[] {
  if (typeof window === 'undefined') return INITIAL_NOTIFICATIONS;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(INITIAL_NOTIFICATIONS));
      return INITIAL_NOTIFICATIONS;
    }
    return JSON.parse(raw);
  } catch (e) {
    return INITIAL_NOTIFICATIONS;
  }
}

export function addNotification(notif: Omit<AppNotification, 'id' | 'timestamp' | 'read'>): AppNotification {
  const newNotif: AppNotification = {
    ...notif,
    id: `notif_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
    timestamp: 'Just now',
    read: false,
  };

  if (typeof window !== 'undefined') {
    try {
      const current = getNotifications();
      // Keep max 20 notifications
      const updated = [newNotif, ...current.filter((n) => n.id !== newNotif.id)].slice(0, 20);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      window.dispatchEvent(new CustomEvent(EVENT_KEY, { detail: updated }));
    } catch (e) {
      console.warn('Failed to persist notification:', e);
    }
  }

  return newNotif;
}

export function markAllNotificationsRead(): void {
  if (typeof window === 'undefined') return;
  try {
    const current = getNotifications();
    const updated = current.map((n) => ({ ...n, read: true }));
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    window.dispatchEvent(new CustomEvent(EVENT_KEY, { detail: updated }));
  } catch (e) {
    console.warn('Failed to mark notifications read:', e);
  }
}

export function dismissNotification(id: string): void {
  if (typeof window === 'undefined') return;
  try {
    const current = getNotifications();
    const updated = current.filter((n) => n.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    window.dispatchEvent(new CustomEvent(EVENT_KEY, { detail: updated }));
  } catch (e) {
    console.warn('Failed to dismiss notification:', e);
  }
}

export function subscribeNotifications(callback: (notifications: AppNotification[]) => void): () => void {
  if (typeof window === 'undefined') return () => {};

  const handler = (e: Event) => {
    const customEvent = e as CustomEvent<AppNotification[]>;
    if (customEvent.detail) {
      callback(customEvent.detail);
    } else {
      callback(getNotifications());
    }
  };

  window.addEventListener(EVENT_KEY, handler);
  window.addEventListener('storage', handler);

  return () => {
    window.removeEventListener(EVENT_KEY, handler);
    window.removeEventListener('storage', handler);
  };
}
