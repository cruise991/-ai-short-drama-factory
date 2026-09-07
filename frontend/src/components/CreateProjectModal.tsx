import { useState, useEffect, type FormEvent } from 'react';
import { X, Loader2, Sparkles, TrendingUp, Music, Film } from 'lucide-react';
import { projectsApi } from '../api/projects';
import { configApi } from '../api/config';
import { useTranslation } from '../locales/i18n';

interface CreateProjectModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

const CreateProjectModal = ({ onClose, onSuccess }: CreateProjectModalProps) => {
  const { t } = useTranslation();
  const [goal, setGoal] = useState('');
  const [branchType, setBranchType] = useState('short_drama');
  const [availableIps, setAvailableIps] = useState<string[]>([]);
  const [selectedIp, setSelectedIp] = useState('');
  const [vibe, setVibe] = useState('赛博朋克风');
  const [trendEnabled, setTrendEnabled] = useState(false);
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    configApi.getAvailableIps()
      .then(ips => {
        setAvailableIps(ips);
        if (ips.length > 0) setSelectedIp(ips[0]);
      })
      .catch(err => console.error("Failed to load IPs", err));
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) {
      setError(t('modal.goalEmpty', 'Project goal cannot be empty.'));
      return;
    }
    
    setIsSubmitting(true);
    setError('');
    
    try {
      await projectsApi.createProject({
        goal,
        format_type: 'vertical',
        branch_type: branchType,
        selected_ip: selectedIp,
        vibe: vibe,
        trend_enabled: trendEnabled
      });
      onSuccess();
    } catch (err) {
      console.error(err);
      setError('Failed to create project. Please check backend logs.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md">
      <div className="bg-[#0f1115] border border-gray-800 rounded-2xl shadow-[0_0_50px_rgba(0,0,0,0.5)] w-full max-w-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[90vh]">
        <div className="flex justify-between items-center px-6 py-4 border-b border-gray-800/50 bg-gradient-to-r from-blue-900/20 to-transparent">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-lg text-blue-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-bold text-white tracking-wide">{t('modal.title', 'Initialize Creative Pipeline')}</h2>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors p-1 rounded-md hover:bg-gray-800">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="overflow-y-auto flex-1 p-6 custom-scrollbar">
          <form id="project-form" onSubmit={handleSubmit}>
            {error && (
              <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm flex items-center gap-3">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                </span>
                {error}
              </div>
            )}
            
            <div className="space-y-6">
              {/* Branch Type */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-3 uppercase tracking-wider">{t('modal.branch', 'CREATIVE BRANCH')}</label>
                <div className="grid grid-cols-2 gap-4">
                  <label className="cursor-pointer group">
                    <input type="radio" name="branchType" value="short_drama" checked={branchType === 'short_drama'} onChange={() => setBranchType('short_drama')} className="peer sr-only" />
                    <div className="p-4 border border-gray-800 rounded-xl bg-gray-900/50 group-hover:border-gray-700 peer-checked:border-blue-500/50 peer-checked:bg-blue-900/10 transition-all flex flex-col gap-2">
                      <Film className={`w-6 h-6 ${branchType === 'short_drama' ? 'text-blue-400' : 'text-gray-500'}`} />
                      <div>
                        <span className="block text-gray-200 font-medium">{t('modal.dramaBranch', 'Original Short Drama')}</span>
                        <span className="text-xs text-gray-500">{t('modal.dramaDesc', 'Auto-generate multi-shot scripts & visual hooks')}</span>
                      </div>
                    </div>
                  </label>
                  <label className="cursor-pointer group">
                    <input type="radio" name="branchType" value="dance_video" checked={branchType === 'dance_video'} onChange={() => setBranchType('dance_video')} className="peer sr-only" />
                    <div className="p-4 border border-gray-800 rounded-xl bg-gray-900/50 group-hover:border-gray-700 peer-checked:border-purple-500/50 peer-checked:bg-purple-900/10 transition-all flex flex-col gap-2">
                      <Music className={`w-6 h-6 ${branchType === 'dance_video' ? 'text-purple-400' : 'text-gray-500'}`} />
                      <div>
                        <span className="block text-gray-200 font-medium">{t('modal.danceBranch', 'AI Dance Short Video')}</span>
                        <span className="text-xs text-gray-500">{t('modal.danceDesc', 'Select fixed character IP & dynamic choreography')}</span>
                      </div>
                    </div>
                  </label>
                </div>
              </div>

              {/* Goal Input */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2 uppercase tracking-wider">
                  {t('modal.promptLabel', 'CREATIVE PROMPT')}
                </label>
                <textarea 
                  value={goal}
                  onChange={e => setGoal(e.target.value)}
                  placeholder={t('modal.promptPlaceholder', 'Describe your creative idea...')}
                  className="w-full bg-gray-900/50 border border-gray-800 rounded-xl px-4 py-3 text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-500/50 focus:bg-gray-900 transition-all resize-none h-24"
                  autoFocus
                />
              </div>

              {/* Conditional Fields for Dance Video */}
              {branchType === 'dance_video' && (
                <div className="grid grid-cols-2 gap-6 p-5 bg-gray-900/30 rounded-xl border border-gray-800/50">
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-2 uppercase tracking-wider">{t('modal.ipLabel', 'CHARACTER IP PRESET')}</label>
                    <select 
                      value={selectedIp}
                      onChange={(e) => setSelectedIp(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5"
                    >
                      {availableIps.map(ip => (
                        <option key={ip} value={ip}>{ip}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 mb-2 uppercase tracking-wider">{t('modal.vibeLabel', 'VISUAL STYLE & VIBE')}</label>
                    <select 
                      value={vibe}
                      onChange={(e) => setVibe(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5"
                    >
                      <option value="赛博朋克风">赛博朋克 (Cyberpunk)</option>
                      <option value="清纯可爱风">清纯可爱 (Cute)</option>
                      <option value="暗黑哥特风">暗黑哥特 (Gothic)</option>
                      <option value="国风汉服">国风汉服 (Hanfu)</option>
                    </select>
                  </div>
                </div>
              )}

              {/* Toggles */}
              <div className="flex items-center justify-between p-4 border border-gray-800 rounded-xl bg-gray-900/30">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${trendEnabled ? 'bg-orange-500/20 text-orange-400' : 'bg-gray-800 text-gray-500'}`}>
                    <TrendingUp className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-200">{t('modal.trendTitle', 'Trend Research & Web Signals')}</div>
                    <div className="text-xs text-gray-500">{t('modal.trendDesc', 'Real-time web signals from Xiaohongshu & TikTok injected into planning')}</div>
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" checked={trendEnabled} onChange={(e) => setTrendEnabled(e.target.checked)} />
                  <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-orange-500"></div>
                </label>
              </div>

            </div>
          </form>
        </div>
        
        <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-800/50 bg-gray-900/50">
          <button 
            type="button" 
            onClick={onClose}
            disabled={isSubmitting}
            className="px-5 py-2.5 text-sm font-medium text-gray-400 hover:text-white transition-colors"
          >
            {t('modal.cancel', 'Cancel')}
          </button>
          <button 
            type="submit" 
            form="project-form"
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="flex items-center px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-xl transition-all shadow-[0_0_15px_rgba(37,99,235,0.4)] hover:shadow-[0_0_25px_rgba(37,99,235,0.6)] disabled:opacity-50 disabled:shadow-none"
          >
            {isSubmitting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
            {isSubmitting ? t('modal.submitting', 'Submitting...') : t('modal.submit', 'Submit Project')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateProjectModal;
