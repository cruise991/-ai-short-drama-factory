import { useState, useEffect } from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import OnboardingWizard from './components/OnboardingWizard'
import ProjectList from './components/ProjectList'
import LiveConsole from './components/LiveConsole'
import AssetGallery from './pages/AssetGallery'
import ProjectDetail from './pages/ProjectDetail'
import DanceStudio from './pages/DanceStudio'
import { Login } from './pages/Login'
import { AdminLayout } from './layouts/AdminLayout'
import { ViewerLayout } from './layouts/ViewerLayout'
import { AvatarManager } from './pages/AvatarManager'
import { LiveOrchestrator } from './pages/LiveOrchestrator'
import { KnowledgeManager } from './pages/KnowledgeManager'
import { MonitoringView } from './pages/MonitoringView'
import { LiveViewer } from './pages/LiveViewer'
import { 
  LayoutDashboard, 
  Settings, 
  TerminalSquare, 
  Flame, 
  Globe, 
  Radio, 
  UserCheck, 
  Activity 
} from 'lucide-react'
import { useTranslation, type Language } from './locales/i18n'

function App() {
  const [isConfigured, setIsConfigured] = useState<boolean>(true)
  const [currentView, setCurrentView] = useState<'dashboard' | 'dance' | 'settings'>('dashboard')
  const [showConsole, setShowConsole] = useState(false)
  const { t, lang, setLanguage } = useTranslation()

  useEffect(() => {
    const configStatus = localStorage.getItem('isConfigured')
    if (configStatus === 'false') {
      setIsConfigured(false)
    }
  }, [])

  const toggleLanguage = () => {
    const nextLang: Language = lang === 'en' ? 'zh' : 'en'
    setLanguage(nextLang)
  }

  if (!isConfigured) {
    return <OnboardingWizard onComplete={() => setIsConfigured(true)} />
  }

  return (
    <Routes>
      {/* 1. Public Authentication Route */}
      <Route path="/login" element={<Login />} />

      {/* 2. Immersive Live Streaming Viewer Routes */}
      <Route path="/viewer" element={<ViewerLayout />}>
        <Route index element={<LiveViewer />} />
        <Route path=":roomId" element={<LiveViewer />} />
      </Route>
      <Route path="/live/:roomId" element={<ViewerLayout />}>
        <Route index element={<LiveViewer />} />
      </Route>

      {/* 3. Admin & Live Management Routes */}
      <Route path="/admin" element={<AdminLayout />}>
        <Route path="avatars" element={<AvatarManager />} />
        <Route path="live" element={<LiveOrchestrator />} />
        <Route path="knowledge" element={<KnowledgeManager />} />
        <Route path="monitoring" element={<MonitoringView />} />
      </Route>

      {/* 4. Short Drama Core Studio Routes (Preserved & Enhanced) */}
      <Route path="/projects/:slug" element={<ProjectDetail />} />
      <Route path="/projects/:slug/assets" element={<AssetGallery />} />
      <Route path="/dance" element={<DanceStudio />} />
      <Route path="/" element={
        <div className="flex h-screen bg-gray-900 text-gray-100 overflow-hidden font-sans selection:bg-pink-500/30">
          {/* Sidebar */}
          <aside className="w-64 bg-gray-950 border-r border-gray-800 flex flex-col justify-between">
            <div>
              <div className="p-6 border-b border-gray-800 flex items-center justify-between">
                <div>
                  <h1 className="text-xl font-bold bg-gradient-to-r from-pink-400 via-purple-300 to-indigo-400 bg-clip-text text-transparent">
                    {t('app.title')}
                  </h1>
                  <p className="text-xs text-gray-500 mt-1">{t('app.subtitle')}</p>
                </div>
              </div>
              
              <nav className="p-4 space-y-1.5">
                <button 
                  onClick={() => setCurrentView('dashboard')}
                  className={`w-full flex items-center px-4 py-2.5 rounded-xl transition-all ${
                    currentView === 'dashboard' 
                      ? 'bg-blue-600/10 text-blue-400 border border-blue-500/30 font-semibold shadow-lg shadow-blue-500/5' 
                      : 'text-gray-400 hover:bg-gray-900 hover:text-gray-200 border border-transparent'
                  }`}
                >
                  <LayoutDashboard className="w-5 h-5 mr-3" />
                  <span className="font-medium text-sm">{t('app.nav.drama')}</span>
                </button>

                <button 
                  onClick={() => setCurrentView('dance')}
                  className={`w-full flex items-center px-4 py-2.5 rounded-xl transition-all ${
                    currentView === 'dance' 
                      ? 'bg-gradient-to-r from-pink-500/20 to-purple-500/20 border border-pink-500/30 text-pink-300 font-semibold shadow-lg shadow-pink-500/10' 
                      : 'text-gray-400 hover:bg-gray-900 hover:text-gray-200 border border-transparent'
                  }`}
                >
                  <Flame className={`w-5 h-5 mr-3 ${currentView === 'dance' ? 'text-pink-400 animate-pulse' : ''}`} />
                  <span className="font-medium text-sm">{t('app.nav.dance')}</span>
                </button>

                {/* LingCast Expansion Links */}
                <div className="pt-2 pb-1">
                  <div className="px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">
                    LingCast 直播中台
                  </div>
                </div>

                <Link
                  to="/admin/live"
                  className="w-full flex items-center px-4 py-2.5 rounded-xl text-gray-400 hover:bg-gray-900 hover:text-gray-200 transition-colors text-sm"
                >
                  <Radio className="w-5 h-5 mr-3 text-indigo-400" />
                  <span>智能直播编排</span>
                </Link>

                <Link
                  to="/admin/avatars"
                  className="w-full flex items-center px-4 py-2.5 rounded-xl text-gray-400 hover:bg-gray-900 hover:text-gray-200 transition-colors text-sm"
                >
                  <UserCheck className="w-5 h-5 mr-3 text-purple-400" />
                  <span>数字人资产</span>
                </Link>

                <Link
                  to="/admin/monitoring"
                  className="w-full flex items-center px-4 py-2.5 rounded-xl text-gray-400 hover:bg-gray-900 hover:text-gray-200 transition-colors text-sm"
                >
                  <Activity className="w-5 h-5 mr-3 text-emerald-400" />
                  <span>基础设施监控</span>
                </Link>

                <button 
                  onClick={() => setShowConsole(!showConsole)}
                  className={`w-full flex items-center px-4 py-2.5 rounded-xl transition-colors ${showConsole ? 'bg-green-600/10 text-green-400 border border-green-500/30' : 'text-gray-400 hover:bg-gray-900 hover:text-gray-200 border border-transparent'}`}
                >
                  <TerminalSquare className="w-5 h-5 mr-3" />
                  <span className="font-medium text-sm">{t('app.nav.console')}</span>
                </button>
              </nav>
            </div>

            <div className="p-4 border-t border-gray-800 space-y-2">
              <button 
                onClick={toggleLanguage}
                className="w-full flex items-center justify-between px-4 py-2 rounded-xl text-gray-400 hover:bg-gray-900 hover:text-gray-200 transition-colors border border-gray-800/80 text-xs"
              >
                <div className="flex items-center">
                  <Globe className="w-4 h-4 mr-2 text-indigo-400" />
                  <span>Language</span>
                </div>
                <span className="text-[10px] font-bold font-mono bg-gray-800 px-2 py-0.5 rounded text-indigo-300">
                  {lang.toUpperCase()}
                </span>
              </button>

              <button 
                onClick={() => setCurrentView('settings')}
                className={`w-full flex items-center px-4 py-2 rounded-xl transition-colors text-xs ${currentView === 'settings' ? 'bg-blue-600/10 text-blue-400 font-semibold' : 'text-gray-400 hover:bg-gray-900 hover:text-gray-200'}`}
              >
                <Settings className="w-4 h-4 mr-2" />
                <span>{t('app.nav.settings')}</span>
              </button>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1 flex flex-col overflow-y-auto bg-gray-900 relative">
            {currentView === 'dashboard' && <ProjectList />}
            {currentView === 'dance' && <DanceStudio />}
            {currentView === 'settings' && (
              <OnboardingWizard 
                isSettingsMode={true} 
                onCancel={() => setCurrentView('dashboard')}
                onComplete={() => setCurrentView('dashboard')}
              />
            )}
            
            {/* Floating Live Console */}
            {showConsole && <LiveConsole onClose={() => setShowConsole(false)} />}
          </main>
        </div>
      } />
    </Routes>
  )
}

export default App
