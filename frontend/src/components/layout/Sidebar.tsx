import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Radar, AlertTriangle, ScrollText } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
}

const navItems: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/scans', label: 'Scans', icon: Radar },
  { to: '/findings', label: 'Findings', icon: AlertTriangle },
  { to: '/audit', label: 'Audit Log', icon: ScrollText },
];

interface SidebarProps {
  runningScans?: number;
}

export function Sidebar({ runningScans = 0 }: SidebarProps) {
  return (
    <aside className="w-60 shrink-0 border-r border-border-subtle bg-bg-secondary flex flex-col">
      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        <p className="px-3 mb-3 text-[10px] font-semibold tracking-widest uppercase text-text-tertiary">
          Navigation
        </p>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-bg-tertiary text-text-primary border-l-2 border-accent ml-0 pl-[10px]'
                  : 'text-text-secondary hover:bg-bg-tertiary/50 hover:text-text-primary border-l-2 border-transparent ml-0 pl-[10px]'
              }`
            }
          >
            <item.icon
              size={17}
              strokeWidth={1.8}
              className="shrink-0 group-[.active]:text-accent"
            />
            <span className="flex-1">{item.label}</span>
            {item.label === 'Scans' && runningScans > 0 && (
              <span className="flex items-center justify-center min-w-[20px] h-5 rounded-full bg-accent/15 text-accent text-[11px] font-semibold px-1.5 tabular-nums">
                {runningScans}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-border-subtle">
        <p className="text-[10px] text-text-tertiary tracking-wide">
          SentinelClaw &middot; Autonomous Pentesting
        </p>
      </div>
    </aside>
  );
}
