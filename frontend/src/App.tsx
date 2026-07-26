import { useState, useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import OnboardingWizard from './components/OnboardingWizard'
import ProjectList from './components/ProjectList'
import LiveConsole from './components/LiveConsole'
import AssetGallery from './pages/AssetGallery'
import { LayoutDashboard, Settings, TerminalSquare } from 'lucide-react'

function App() {
  const [isConfigured, setIsConfigured] = useState<boolean>(false)
  const [currentView, setCurrentView] = useState<'dashboard' | 'settings'>('dashboard')
  const [showConsole, setShowConsole] = useState(false)

  useEffect(() => {
    const configStatus = localStorage.getItem('isConfigured')
    if (configStatus === 'true') {
      setIsConfigured(true)
    }
  }, [])

  if (!isConfigured) {
    return <OnboardingWizard onComplete={() => setIsConfigured(true)} />
  }

  return (
    <Routes>
      <Route path="/projects/:slug/assets" element={<AssetGallery />} />
      <Route path="/" element={
        <div className="flex h-screen bg-gray-900 text-gray-100 overflow-hidden font-sans selection:bg-blue-500/30">
          {/* Sidebar */}
          <aside className="w-64 bg-gray-950 border-r border-gray-800 flex flex-col">
            <div className="p-6 border-b border-gray-800">
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">
                AI Short Drama
              </h1>
              <p className="text-xs text-gray-500 mt-1">Factory Dashboard v1.0</p>
            </div>
            
            <nav className="flex-1 p-4 space-y-2">
              <button 
                onClick={() => setCurrentView('dashboard')}
                className={`w-full flex items-center px-4 py-3 rounded-xl transition-colors ${currentView === 'dashboard' ? 'bg-blue-600/10 text-blue-400' : 'text-gray-400 hover:bg-gray-900 hover:text-gray-200'}`}
              >
                <LayoutDashboard className="w-5 h-5 mr-3" />
                <span className="font-medium">Projects</span>
              </button>
              <button 
                onClick={() => setShowConsole(!showConsole)}
                className={`w-full flex items-center px-4 py-3 rounded-xl transition-colors ${showConsole ? 'bg-green-600/10 text-green-400' : 'text-gray-400 hover:bg-gray-900 hover:text-gray-200'}`}
              >
                <TerminalSquare className="w-5 h-5 mr-3" />
                <span className="font-medium">Live Console</span>
              </button>
            </nav>

            <div className="p-4 border-t border-gray-800">
              <button 
                onClick={() => setCurrentView('settings')}
                className={`w-full flex items-center px-4 py-3 rounded-xl transition-colors ${currentView === 'settings' ? 'bg-blue-600/10 text-blue-400' : 'text-gray-400 hover:bg-gray-900 hover:text-gray-200'}`}
              >
                <Settings className="w-5 h-5 mr-3" />
                <span className="font-medium">System Settings</span>
              </button>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1 flex flex-col overflow-y-auto bg-gray-900 relative">
            {currentView === 'dashboard' && <ProjectList />}
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
