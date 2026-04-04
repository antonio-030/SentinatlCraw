import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { TopBar } from './TopBar';
import { Sidebar } from './Sidebar';
import { api } from '../../services/api';

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const { data: status } = useQuery({
    queryKey: ['status'],
    queryFn: api.status,
    refetchInterval: 10_000,
    retry: 1,
  });

  const systemOnline = !!status;
  const runningScans = status?.scans.running ?? 0;

  return (
    <div className="flex h-[100dvh] w-full flex-col bg-bg-primary">
      <TopBar
        systemOnline={systemOnline}
        onMenuToggle={() => setSidebarOpen(!sidebarOpen)}
      />
      <div className="flex flex-1 overflow-hidden relative">
        {/* Mobile Overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-30 bg-black/60 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar — Desktop: immer sichtbar, Mobile: Slide-Over */}
        <div className={`
          fixed inset-y-0 left-0 z-40 w-64 transform transition-transform duration-200 ease-out
          lg:static lg:z-auto lg:translate-x-0 lg:w-60
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        `}>
          <Sidebar
            runningScans={runningScans}
            onNavigate={() => setSidebarOpen(false)}
          />
        </div>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
