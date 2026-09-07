import { useState, useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import OnboardingWizard from './components/OnboardingWizard'
import ProjectList from './components/ProjectList'
import LiveConsole from './components/LiveConsole'
import AssetGallery from './pages/AssetGallery'
import ProjectDetail from './pages/ProjectDetail'
import DanceStudio from './pages/DanceStudio'
import { LayoutDashboard, Settings, TerminalSquare, Flame, Globe } from 'lucide-react'
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
              
              <nav className="p-4 space-y-2">
                <button 
                  onClick={() => setCurrentView('dashboard')}
                  className={`w-full flex items-center px-4 py-3 rounded-xl transition-all ${
                    currentView === 'dashboard' 
                      ? 'bg-blue-600/10 text-blue-400 border border-blue-500/30 font-semibold shadow-lg shadow-blue-500/5' 
                      : 'text-gray-400 hover:bg-gray-900 hover:text-gray-200 border border-transparent'
                  }`}
                >
                  <LayoutDashboard className="w-5 h-5 mr-3" />
                  <span className="font-medium">{t('app.nav.drama')}</span>
                </button>

                <button 
                  onClick={() => setCurrentView('dance')}
                  className={`w-full flex items-center px-4 py-3 rounded-xl transition-all ${
                    currentView === 'dance' 
                      ? 'bg-gradient-to-r from-pink-500/20 to-purple-500/20 border border-pink-500/30 text-pink-300 font-semibold shadow-lg shadow-pink-500/10' 
                      : 'text-gray-400 hover:bg-gray-900 hover:text-gray-200 border border-transparent'
                  }`}
                >
                  <Flame className={`w-5 h-5 mr-3 ${currentView === 'dance' ? 'text-pink-400 animate-pulse' : ''}`} />
                  <span className="font-medium">{t('app.nav.dance')}</span>
                </button>

                <button 
                  onClick={() => setShowConsole(!showConsole)}
                  className={`w-full flex items-center px-4 py-3 rounded-xl transition-colors ${showConsole ? 'bg-green-600/10 text-green-400 border border-green-500/30' : 'text-gray-400 hover:bg-gray-900 hover:text-gray-200 border border-transparent'}`}
                >
                  <TerminalSquare className="w-5 h-5 mr-3" />
                  <span className="font-medium">{t('app.nav.console')}</span>
                </button>
              </nav>
            </div>

            <div className="p-4 border-t border-gray-800 space-y-2">
              <button 
                onClick={toggleLanguage}
                className="w-full flex items-center justify-between px-4 py-2.5 rounded-xl text-gray-400 hover:bg-gray-900 hover:text-gray-200 transition-colors border border-gray-800/80 text-sm"
              >
                <div className="flex items-center">
                  <Globe className="w-4 h-4 mr-2.5 text-indigo-400" />
                  <span>Language</span>
                </div>
                <span className="text-xs font-bold font-mono bg-gray-800 px-2 py-0.5 rounded text-indigo-300">
                  {lang.toUpperCase()}
                </span>
              </button>

              <button 
                onClick={() => setCurrentView('settings')}
                className={`w-full flex items-center px-4 py-2.5 rounded-xl transition-colors text-sm ${currentView === 'settings' ? 'bg-blue-600/10 text-blue-400 font-semibold' : 'text-gray-400 hover:bg-gray-900 hover:text-gray-200'}`}
              >
                <Settings className="w-4 h-4 mr-2.5" />
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
