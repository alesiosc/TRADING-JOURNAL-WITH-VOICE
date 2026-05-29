import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { LayoutDashboard, ClipboardList, Upload, Menu, X, TrendingUp, Server } from 'lucide-react';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/trades', label: 'Trades', icon: ClipboardList },
  { to: '/nt8', label: 'NT8', icon: Server },
  { to: '/import', label: 'Import', icon: Upload },
];

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-[#F8FAFC]">
      {sidebarOpen && (
        <div className="fixed inset-0 z-20 bg-black/20 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      <aside className={`
        fixed inset-y-0 left-0 z-30 w-60 bg-white border-r border-[#E9EDF2] transform transition-transform duration-200 ease-in-out
        lg:relative lg:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-5 border-b border-[#E9EDF2]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[#2563EB] to-[#3B82F6] flex items-center justify-center shadow-sm">
              <TrendingUp size={16} className="text-white" />
            </div>
            <div>
              <h1 className="text-[15px] font-semibold text-[#0F172A] tracking-tight">Journal</h1>
              <p className="text-[10px] font-medium text-[#94A3B8] tracking-wider uppercase">Trading</p>
            </div>
          </div>
          <button onClick={() => setSidebarOpen(false)} className="lg:hidden text-[#94A3B8] hover:text-[#475569]">
            <X size={18} />
          </button>
        </div>

        {/* Nav */}
        <nav className="mt-5 px-3 space-y-0.5">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? 'sidebar-link-active' : 'sidebar-link-inactive'}`
              }
            >
              <item.icon size={18} className="shrink-0" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Bottom section */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-[#E9EDF2]">
          <div className="flex items-center gap-2.5 px-3 py-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#2563EB] to-[#3B82F6] flex items-center justify-center text-[10px] font-bold text-white">
              C
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-[#0F172A] truncate">Trader</p>
              <p className="text-[10px] text-[#94A3B8]">Local Journal</p>
            </div>
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile top bar */}
        <header className="h-14 border-b border-[#E9EDF2] bg-white flex items-center px-4 lg:hidden">
          <button onClick={() => setSidebarOpen(true)} className="text-[#64748B] hover:text-[#0F172A] mr-3">
            <Menu size={20} />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#2563EB] to-[#3B82F6] flex items-center justify-center">
              <TrendingUp size={14} className="text-white" />
            </div>
            <h1 className="text-sm font-semibold text-[#0F172A]">Journal</h1>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6 md:p-8 lg:p-10 max-w-7xl mx-auto w-full">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
