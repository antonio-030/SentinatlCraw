import { Outlet } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { TopBar } from './TopBar';
import { Sidebar } from './Sidebar';
import { api } from '../../services/api';

export function AppLayout() {
  // Poll system status every 10 seconds
  const { data: status } = useQuery({
    queryKey: ['status'],
    queryFn: api.status,
    refetchInterval: 10_000,
    retry: 1,
  });

  const systemOnline = !!status;
  const runningScans = status?.scans.running ?? 0;

  return (
    <div className="flex h-screen w-full flex-col bg-bg-primary">
      <TopBar systemOnline={systemOnline} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar runningScans={runningScans} />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
