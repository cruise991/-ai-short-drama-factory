import { useState, useEffect, type FormEvent } from 'react';
import { 
  X, Loader2, Sparkles, TrendingUp, Music, Film, 
  PenTool, Shirt, Video, CheckCircle2 
} from 'lucide-react';
import { projectsApi } from '../api/projects';
import { configApi, type BranchPresetsResponse } from '../api/config';
import { useTranslation } from '../locales/i18n';
import { CaptionStyleEditor } from './handdraw/CaptionStyleEditor';

interface CreateProjectModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

const CreateProjectModal = ({ onClose, onSuccess }: CreateProjectModalProps) => {
  const { t } = useTranslation();
  const [goal, setGoal] = useState('');
  const [branchType, setBranchType] = useState('short_drama');
  
  // Dynamic presets from backend
  const [presets, setPresets] = useState<BranchPresetsResponse | null>(null);
  const [availableIps, setAvailableIps] = useState<string[]>([]);
  const [selectedIp, setSelectedIp] = useState('');
  const [vibe, setVibe] = useState('赛博朋克风');
  const [trendEnabled, setTrendEnabled] = useState(false);

  // Transformation video parameters
  const [selectedCostume, setSelectedCostume] = useState('cyber_dress');
  const [selectedScene, setSelectedScene] = useState('cyber_street');
  const [selectedMotion, setSelectedMotion] = useState('model_spin');

  // Handdraw video parameters
  const [selectedHand, setSelectedHand] = useState('teacher-pen');
  const [selectedPaper, setSelectedPaper] = useState('#FBF9F1');
  const [selectedCaptionStyle, setSelectedCaptionStyle] = useState('pill_dark');
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    configApi.getBranchPresets()
      .then(data => {
        setPresets(data);
        if (data.ips && data.ips.length > 0) {
          setAvailableIps(data.ips);
          setSelectedIp(data.ips[0]);
        }
        if (data.costumes && Object.keys(data.costumes).length > 0) {
          setSelectedCostume(Object.keys(data.costumes)[0]);
        }
        if (data.scenes && Object.keys(data.scenes).length > 0) {
          setSelectedScene(Object.keys(data.scenes)[0]);
        }
        if (data.motions && Object.keys(data.motions).length > 0) {
          setSelectedMotion(Object.keys(data.motions)[0]);
        }
        if (data.hands && data.hands.length > 0) {
          setSelectedHand(data.hands[0].id);
        }
        if (data.caption_styles && data.caption_styles.length > 0) {
          setSelectedCaptionStyle(data.caption_styles[0].id);
        }
      })
      .catch(err => {
        console.error("Failed to load presets", err);
        // Fallback
        configApi.getAvailableIps().then(ips => {
          setAvailableIps(ips);
          if (ips.length > 0) setSelectedIp(ips[0]);
        });
      });
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
        selected_ip: branchType === 'dance_video' ? selectedIp : undefined,
        vibe: branchType === 'dance_video' ? vibe : undefined,
        trend_enabled: trendEnabled,
        costume_id: branchType === 'transformation_video' ? selectedCostume : undefined,
        scene_id: branchType === 'transformation_video' ? selectedScene : undefined,
        motion_id: branchType === 'transformation_video' ? selectedMotion : undefined,
        hand_preset: branchType === 'handdraw_video' ? selectedHand : undefined,
        caption_style: branchType === 'handdraw_video' ? selectedCaptionStyle : undefined,
      });
      onSuccess();
    } catch (err) {
      console.error(err);
      setError('Failed to create project. Please check backend logs.');
      setIsSubmitting(false);
    }
  };

  const branchCards = [
    {
      id: 'short_drama',
      title: t('modal.dramaBranch', 'AI 剧情连载短剧'),
      desc: t('modal.dramaDesc', '多镜头连载短剧，冲突反转与剧情大纲'),
      icon: Film,
      color: 'blue',
      borderClass: 'peer-checked:border-blue-500/80 peer-checked:bg-blue-950/20 text-blue-400'
    },
    {
      id: 'transformation_video',
      title: t('modal.transformationBranch', '换装变身反差短剧'),
      desc: t('modal.transformationDesc', '三段式反差变装 (Setup ➔ Glitch ➔ Reveal)，服装与场景自由切换'),
      icon: Shirt,
      color: 'rose',
      borderClass: 'peer-checked:border-rose-500/80 peer-checked:bg-rose-950/20 text-rose-400'
    },
    {
      id: 'dance_video',
      title: t('modal.danceBranch', 'AI 唱跳律动短视频'),
      desc: t('modal.danceDesc', '固定角色 IP 与高保真 BPM 音乐律动'),
      icon: Music,
      color: 'purple',
      borderClass: 'peer-checked:border-purple-500/80 peer-checked:bg-purple-950/20 text-purple-400'
    },
    {
      id: 'handdraw_video',
      title: t('modal.handdrawBranch', '手绘口播思维推演'),
      desc: t('modal.handdrawDesc', '逐笔手绘线稿、白板推演、戈尔曼双脑隐喻与曜石黑胶囊字幕'),
      icon: PenTool,
      color: 'emerald',
      borderClass: 'peer-checked:border-emerald-500/80 peer-checked:bg-emerald-950/20 text-emerald-400'
    },
    {
      id: 'neural_explainer',
      title: t('modal.explainerBranch', '神经画中画长解说'),
      desc: t('modal.explainerDesc', '深度知识长视频，数字人画中画与动态课件'),
      icon: Video,
      color: 'amber',
      borderClass: 'peer-checked:border-amber-500/80 peer-checked:bg-amber-950/20 text-amber-400'
    }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md">
      <div className="bg-[#0f1115] border border-gray-800 rounded-2xl shadow-[0_0_50px_rgba(0,0,0,0.5)] w-full max-w-3xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-gray-800/50 bg-gradient-to-r from-blue-900/20 to-transparent">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-lg text-blue-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-wide">
                {t('modal.title', '新建 AI 视频生成流水线')}
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">SaaS 矩阵引擎 · 覆盖 4 大核心短视频与知识长视频</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors p-1.5 rounded-lg hover:bg-gray-800">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Body */}
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
              {/* Branch Type Selector */}
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-3 uppercase tracking-wider">
                  选择业务视频分支 (PRODUCTION PIPELINE BRANCH)
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {branchCards.map((b) => {
                    const Icon = b.icon;
                    const isSelected = branchType === b.id;
                    return (
                      <label key={b.id} className="cursor-pointer group">
                        <input 
                          type="radio" 
                          name="branchType" 
                          value={b.id} 
                          checked={isSelected} 
                          onChange={() => setBranchType(b.id)} 
                          className="peer sr-only" 
                        />
                        <div className={`p-3.5 border rounded-xl bg-gray-900/40 group-hover:border-gray-700 transition-all flex flex-col justify-between h-full ${
                          isSelected ? b.borderClass : 'border-gray-800'
                        }`}>
                          <div className="flex items-start justify-between mb-2">
                            <Icon className={`w-5 h-5 ${isSelected ? 'text-white' : 'text-gray-400'}`} />
                            {isSelected && <CheckCircle2 className="w-4 h-4 text-white" />}
                          </div>
                          <div>
                            <span className="block text-gray-200 text-sm font-semibold mb-1">{b.title}</span>
                            <span className="text-[11px] text-gray-400 leading-snug line-clamp-2">{b.desc}</span>
                          </div>
                        </div>
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* Goal Input */}
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
                  {t('modal.promptLabel', '创意灵感与内容主题 (PROMPT)')}
                </label>
                <textarea 
                  value={goal}
                  onChange={e => setGoal(e.target.value)}
                  placeholder={
                    branchType === 'handdraw_video'
                      ? '例如：为什么越生气越容易做错决定？面向成年人，剖析杏仁核夺权机制，提供20秒呼吸降温法...'
                      : branchType === 'transformation_video'
                      ? '例如：赛博街头反差变身，从极简素雅穿搭到耀眼晚礼服的华丽蜕变...'
                      : t('modal.promptPlaceholder', '描述您的创意灵感或短剧剧情概要...')
                  }
                  className="w-full bg-gray-900/50 border border-gray-800 rounded-xl px-4 py-3 text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-500/50 focus:bg-gray-900 transition-all resize-none h-24 text-sm"
                  autoFocus
                />
              </div>

              {/* Branch 1: Transformation Video Specific Fields */}
              {branchType === 'transformation_video' && presets && (
                <div className="p-5 bg-gray-900/40 rounded-xl border border-gray-800 space-y-4">
                  <div className="flex items-center gap-2 text-rose-400 font-semibold text-xs uppercase tracking-wider">
                    <Shirt className="w-4 h-4" />
                    <span>变装反差专属资产配置 (Setup ➔ Glitch ➔ Reveal)</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-400 mb-1.5">变装服饰预设</label>
                      <select 
                        value={selectedCostume} 
                        onChange={e => setSelectedCostume(e.target.value)}
                        className="w-full bg-gray-950 border border-gray-700 text-gray-200 text-xs rounded-lg p-2.5 outline-none focus:border-rose-500"
                      >
                        {Object.entries(presets.costumes).map(([k, v]: [string, any]) => (
                          <option key={k} value={k}>{v.name || k}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-400 mb-1.5">置换场景氛围</label>
                      <select 
                        value={selectedScene} 
                        onChange={e => setSelectedScene(e.target.value)}
                        className="w-full bg-gray-950 border border-gray-700 text-gray-200 text-xs rounded-lg p-2.5 outline-none focus:border-rose-500"
                      >
                        {Object.entries(presets.scenes).map(([k, v]: [string, any]) => (
                          <option key={k} value={k}>{v.name || k}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-400 mb-1.5">变身卡点动作</label>
                      <select 
                        value={selectedMotion} 
                        onChange={e => setSelectedMotion(e.target.value)}
                        className="w-full bg-gray-950 border border-gray-700 text-gray-200 text-xs rounded-lg p-2.5 outline-none focus:border-rose-500"
                      >
                        {Object.entries(presets.motions).map(([k, v]: [string, any]) => (
                          <option key={k} value={k}>{v.name || k}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {/* Branch 2: Dance Video Specific Fields */}
              {branchType === 'dance_video' && (
                <div className="grid grid-cols-2 gap-4 p-5 bg-gray-900/40 rounded-xl border border-gray-800">
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">{t('modal.ipLabel', '角色 IP 预设')}</label>
                    <select 
                      value={selectedIp}
                      onChange={(e) => setSelectedIp(e.target.value)}
                      className="w-full bg-gray-950 border border-gray-700 text-gray-200 text-xs rounded-lg focus:ring-purple-500 focus:border-purple-500 block p-2.5"
                    >
                      {availableIps.map(ip => (
                        <option key={ip} value={ip}>{ip}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">{t('modal.vibeLabel', '视觉风格调性')}</label>
                    <select 
                      value={vibe}
                      onChange={(e) => setVibe(e.target.value)}
                      className="w-full bg-gray-950 border border-gray-700 text-gray-200 text-xs rounded-lg focus:ring-purple-500 focus:border-purple-500 block p-2.5"
                    >
                      <option value="赛博朋克风">赛博朋克 (Cyberpunk)</option>
                      <option value="清纯可爱风">清纯可爱 (Cute)</option>
                      <option value="暗黑哥特风">暗黑哥特 (Gothic)</option>
                      <option value="国风汉服">国风汉服 (Hanfu)</option>
                    </select>
                  </div>
                </div>
              )}

              {/* Branch 3: Handdraw Video Specific Fields */}
              {branchType === 'handdraw_video' && presets && (
                <div className="p-5 bg-gray-900/40 rounded-xl border border-gray-800 space-y-5">
                  <div className="flex items-center gap-2 text-emerald-400 font-semibold text-xs uppercase tracking-wider">
                    <PenTool className="w-4 h-4" />
                    <span>手绘白板视觉与字幕对比度引擎</span>
                  </div>

                  {/* Hands and Papers Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-400 mb-1.5">作画手部与用笔模型</label>
                      <select 
                        value={selectedHand} 
                        onChange={e => setSelectedHand(e.target.value)}
                        className="w-full bg-gray-950 border border-gray-700 text-gray-200 text-xs rounded-lg p-2.5 outline-none focus:border-emerald-500"
                      >
                        {presets.hands.map(h => (
                          <option key={h.id} value={h.id}>{h.name}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-400 mb-1.5">底板画纸质感</label>
                      <select 
                        value={selectedPaper} 
                        onChange={e => setSelectedPaper(e.target.value)}
                        className="w-full bg-gray-950 border border-gray-700 text-gray-200 text-xs rounded-lg p-2.5 outline-none focus:border-emerald-500"
                      >
                        {presets.papers.map(p => (
                          <option key={p.id} value={p.color}>{p.name}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Subtitle Style & Contrast Studio */}
                  <CaptionStyleEditor 
                    styles={presets.caption_styles}
                    selectedStyleId={selectedCaptionStyle}
                    onSelect={setSelectedCaptionStyle}
                    paperColor={selectedPaper}
                  />
                </div>
              )}

              {/* Trend Injection Toggle */}
              <div className="flex items-center justify-between p-4 border border-gray-800 rounded-xl bg-gray-900/30">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${trendEnabled ? 'bg-orange-500/20 text-orange-400' : 'bg-gray-800 text-gray-500'}`}>
                    <TrendingUp className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-200">{t('modal.trendTitle', '全网爆款信号实时注入 (Trend Research)')}</div>
                    <div className="text-xs text-gray-500">{t('modal.trendDesc', '联网抓取小红书、抖音、TikTok 爆款心智模型，优化故事开篇与悬念')}</div>
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
        
        {/* Footer */}
        <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-800/50 bg-gray-900/50">
          <button 
            type="button" 
            onClick={onClose}
            disabled={isSubmitting}
            className="px-5 py-2.5 text-sm font-medium text-gray-400 hover:text-white transition-colors"
          >
            {t('modal.cancel', '取消')}
          </button>
          <button 
            type="submit" 
            form="project-form"
            disabled={isSubmitting}
            className="flex items-center px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-xl transition-all shadow-[0_0_15px_rgba(37,99,235,0.4)] hover:shadow-[0_0_25px_rgba(37,99,235,0.6)] disabled:opacity-50 disabled:shadow-none"
          >
            {isSubmitting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
            {isSubmitting ? t('modal.submitting', '任务初始化中...') : t('modal.submit', '立即创建流水线')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateProjectModal;
