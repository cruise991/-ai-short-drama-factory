import { useState, useEffect } from 'react';
import { Settings, Save } from 'lucide-react';
import { configApi } from '../api/config';

interface OnboardingWizardProps {
  onComplete: () => void;
  isSettingsMode?: boolean;
  onCancel?: () => void;
}

export default function OnboardingWizard({ onComplete, isSettingsMode, onCancel }: OnboardingWizardProps) {
  const [loading, setLoading] = useState(true);
  const [config, setConfig] = useState<any>({ env: {}, yaml: {} });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const data = await configApi.getSystemConfig();
      setConfig(data);
    } catch (error) {
      console.error('Failed to load config', error);
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    setSaving(true);
    try {
      await configApi.updateSystemConfig({
        env_vars: config.env,
        yaml_vars: config.yaml
      });
      onComplete();
    } catch (error) {
      console.error('Failed to save config', error);
    } finally {
      setSaving(false);
    }
  };


  const handleEnvChange = (key: string, value: string) => {
    setConfig({ ...config, env: { ...config.env, [key]: value } });
  };

  if (loading) return <div className="p-8 text-center text-white">Loading Configuration...</div>;

  return (
    <div className={`w-full bg-gray-900 text-white p-8 flex justify-center items-start ${isSettingsMode ? 'pt-8' : 'min-h-screen pt-16'}`}>
      <div className="w-full max-w-3xl bg-gray-800 rounded-xl shadow-2xl p-8 border border-gray-700">
        <div className="flex items-center gap-3 mb-6">
          <Settings className="w-8 h-8 text-blue-400" />
          <h1 className="text-2xl font-bold text-gray-100">
            {isSettingsMode ? 'System Settings' : 'System Initialization Wizard'}
          </h1>
        </div>
        
        <p className="text-gray-400 mb-8">
          {isSettingsMode 
            ? 'Update the core system models and API keys below. Changes will be saved to your local configuration.'
            : 'Welcome to the AI Short Drama Content Factory. Before starting the orchestrator, you can review and configure the core system models and API keys below.'
          }
        </p>

        <div className="space-y-6">
          <div className="bg-gray-900/50 p-6 rounded-lg border border-gray-700">
            <h2 className="text-xl font-semibold mb-4 text-blue-300">Production LLM Routing</h2>
            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Image Generation Model</label>
                <input 
                  type="text" 
                  value={config.env.PRODUCTION_IMAGE_MODEL || ''} 
                  onChange={(e) => handleEnvChange('PRODUCTION_IMAGE_MODEL', e.target.value)}
                  className="w-full bg-gray-800 border border-gray-600 rounded p-2 focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Video Generation Model</label>
                <input 
                  type="text" 
                  value={config.env.PRODUCTION_VIDEO_MODEL || ''} 
                  onChange={(e) => handleEnvChange('PRODUCTION_VIDEO_MODEL', e.target.value)}
                  className="w-full bg-gray-800 border border-gray-600 rounded p-2 focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>
          </div>

          <div className="bg-gray-900/50 p-6 rounded-lg border border-gray-700">
            <h2 className="text-xl font-semibold mb-4 text-green-300">Storage & Media</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Storage Provider</label>
                <select 
                  value={config.env.STORAGE_PROVIDER || 'local'} 
                  onChange={(e) => handleEnvChange('STORAGE_PROVIDER', e.target.value)}
                  className="w-full bg-gray-800 border border-gray-600 rounded p-2 focus:border-green-500 focus:outline-none"
                >
                  <option value="local">Local MinIO</option>
                  <option value="r2">Cloudflare R2</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Public Media URL</label>
                <input 
                  type="text" 
                  value={config.env.PUBLIC_MEDIA_URL || ''} 
                  onChange={(e) => handleEnvChange('PUBLIC_MEDIA_URL', e.target.value)}
                  className="w-full bg-gray-800 border border-gray-600 rounded p-2 focus:border-green-500 focus:outline-none"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 flex justify-end gap-4">
          {isSettingsMode ? (
            <button 
              onClick={() => onCancel && onCancel()}
              className="px-6 py-2 rounded-lg font-medium text-gray-300 bg-gray-700 hover:bg-gray-600 transition-colors"
            >
              Cancel
            </button>
          ) : (
            <button 
              onClick={() => onComplete()}
              className="px-6 py-2 rounded-lg font-medium text-gray-300 bg-gray-700 hover:bg-gray-600 transition-colors"
            >
              Use Default Setup
            </button>
          )}
          <button 
            onClick={saveConfig}
            disabled={saving}
            className="px-6 py-2 rounded-lg font-medium text-white bg-blue-600 hover:bg-blue-500 transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {saving ? 'Saving...' : <><Save className="w-4 h-4" /> {isSettingsMode ? 'Save Settings' : 'Save & Initialize'}</>}
          </button>
        </div>
      </div>
    </div>
  );
}
