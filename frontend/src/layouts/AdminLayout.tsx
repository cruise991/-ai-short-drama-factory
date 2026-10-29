import React from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { 
  Film, 
  Radio, 
  UserCheck, 
  BookOpen, 
  Activity, 
  LogOut, 
  Globe, 
  Building2 
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { useTranslation } from '../locales/i18n';

export const AdminLayout: React.FC = () => {
  const { user, logout } = useAuthStore();
  const location = useLocation();
  const navigate = useNavigate();
  const { t, language, setLanguage } = useTranslation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { label: t('nav.projects') || '短剧创作工坊', path: '/', icon: <Film className="w-4 h-4" /> },
    { label: t('nav.avatars') || '数字人与资产', path: '/admin/avatars', icon: <UserCheck className="w-4 h-4" /> },
    { label: t('nav.live') || '智能直播编排', path: '/admin/live', icon: <Radio className="w-4 h-4" /> },
    { label: t('nav.knowledge') || '知识库与台本', path: '/admin/knowledge', icon: <BookOpen className="w-4 h-4" /> },
    { label: t('nav.monitoring') || '基础设施监控', path: '/admin/monitoring', icon: <Activity className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-[#0b0f19] text-gray-100">
      {/* Top Navigation Bar */}
      <header className="h-16 border-b border-white/10 bg-[#111827]/80 backdrop-blur-md sticky top-0 z-50 flex items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/30">
            LC
          </div>
          <div>
            <h1 className="text-base font-bold tracking-wide bg-gradient-to-r from-indigo-300 via-white to-purple-300 bg-clip-text text-transparent">
              LingCast · AutoDrama Studio
            </h1>
            <p className="text-[10px] text-gray-400">Enterprise AI Live & Short-Drama Engine</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Tenant Badge */}
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-300">
            <Building2 className="w-3.5 h-3.5" />
            <span>{user?.tenant_id || 'default'}</span>
          </div>

          {/* System Status Indicator */}
          <div className="flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
            <span className="text-xs text-gray-400 hidden md:inline">SRS & Pipeline Active</span>
          </div>

          {/* Language Switcher */}
          <button
            onClick={() => setLanguage(language === 'zh' ? 'en' : 'zh')}
            className="flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-lg border border-gray-700 hover:bg-gray-800 text-gray-300 transition-colors"
          >
            <Globe className="w-3.5 h-3.5" />
            <span>{language.toUpperCase()}</span>
          </button>

          {/* User Info & Logout */}
          <div className="flex items-center gap-3 border-l border-white/10 pl-4">
            <div className="text-right hidden sm:block">
              <p className="text-xs font-medium text-gray-200">{user?.username || 'Operator'}</p>
              <Badge size="sm" variant="info" className="capitalize">{user?.role || 'admin'}</Badge>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="text-gray-400 hover:text-red-400"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </header>

      <div className="flex flex-1">
        {/* Sidebar */}
        <aside className="w-64 border-r border-white/10 bg-[#0e1422]/70 backdrop-blur-sm p-4 flex flex-col gap-1 shrink-0">
          <div className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider px-3 mb-2">
            Console Navigation
          </div>
          {navItems.map((item) => {
            const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 shadow-sm'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                }`}
              >
                <span className={isActive ? 'text-indigo-400' : 'text-gray-500'}>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            );
          })}

          <div className="mt-auto pt-4 border-t border-white/10">
            <Link
              to="/viewer/demo"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between px-3 py-2 text-xs rounded-lg bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/30 transition-all"
            >
              <span>{t('nav.openViewer') || '打开观众端直播'}</span>
              <span>↗</span>
            </Link>
          </div>
        </aside>

        {/* Main Workspace Area */}
        <main className="flex-1 p-6 overflow-y-auto max-w-7xl mx-auto w-full">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
