import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { useTranslation } from '../locales/i18n';
import client from '../api/client';
import { 
  UserCheck, 
  Plus, 
  Video, 
  Volume2, 
  ShieldCheck, 
  Film,
  Play,
  Eye,
  Radio,
  ExternalLink,
  Sparkles,
  ShoppingBag,
  CheckCircle2,
  Trash2
} from 'lucide-react';
import { DynamicAvatarView } from '../components/DynamicAvatarView';

interface AvatarItem {
  id: number;
  name: string;
  avatar_type: string;
  voice_id: string;
  preview_url?: string;
  status: string;
  config_json?: string;
}

interface SceneItem {
  id: number;
  title: string;
  video_url: string;
  duration: number;
  resolution: string;
  is_loop: boolean;
}

export const AvatarManager: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [avatars, setAvatars] = useState<AvatarItem[]>([]);
  const [scenes, setScenes] = useState<SceneItem[]>([]);
  const [activeTab, setActiveTab] = useState<'avatars' | 'scenes'>('avatars');
  
  // 数字人直播模板实时预览弹窗状态
  const [previewAvatar, setPreviewAvatar] = useState<AvatarItem | null>(null);
  const [previewTemplate, setPreviewTemplate] = useState<'luxury' | 'tech' | 'green'>('luxury');
  const [isPlayingVoice, setIsPlayingVoice] = useState(false);

  // 新建数字人弹窗状态
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState('lingcast_live');
  const [newVoice, setNewVoice] = useState('zh-CN-XiaoxiaoNeural');
  const [newPreviewUrl, setNewPreviewUrl] = useState('https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500&auto=format&fit=crop&q=60');
  
  // 新建场景切片状态
  const [showSceneModal, setShowSceneModal] = useState(false);
  const [newSceneTitle, setNewSceneTitle] = useState('');
  const [newSceneUrl, setNewSceneUrl] = useState('');

  const loadData = async () => {
    try {
      const [avRes, scRes] = await Promise.all([
        client.get('/api/v1/avatars'),
        client.get('/api/v1/avatars/scenes'),
      ]);
      setAvatars(avRes.data || []);
      setScenes(scRes.data || []);
    } catch (e) {
      console.warn('Failed to load avatars/scenes', e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateAvatar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;

    try {
      await client.post('/api/v1/avatars', {
        name: newName.trim(),
        avatar_type: newType,
        voice_id: newVoice,
        preview_url: newPreviewUrl || null,
        status: 'active',
        config_json: JSON.stringify({ licensing_status: 'verified', sample_rate: 16000 }),
      });
      setShowCreateModal(false);
      setNewName('');
      loadData();
    } catch (err) {
      console.error('Create avatar error', err);
    }
  };

  const handleCreateScene = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSceneTitle.trim() || !newSceneUrl.trim()) return;

    try {
      await client.post('/api/v1/avatars/scenes', {
        title: newSceneTitle.trim(),
        video_url: newSceneUrl.trim(),
        duration: 15.0,
        resolution: '1080x1920',
        is_loop: true,
      });
      setShowSceneModal(false);
      setNewSceneTitle('');
      setNewSceneUrl('');
      loadData();
    } catch (err) {
      console.error('Create scene error', err);
    }
  };

  const handleToggleAvatarStatus = async (av: AvatarItem) => {
    const nextStatus = av.status === 'active' ? 'archived' : 'active';
    try {
      await client.put(`/api/v1/avatars/${av.id}`, {
        status: nextStatus,
        config_json: JSON.stringify({ licensing_status: nextStatus === 'active' ? 'verified' : 'unlicensed' })
      });
      if (previewAvatar && previewAvatar.id === av.id) {
        setPreviewAvatar({ ...previewAvatar, status: nextStatus });
      }
      loadData();
    } catch (err) {
      console.error('Update avatar status error', err);
    }
  };

  const handleDeleteAvatar = async (av: AvatarItem) => {
    if (!window.confirm(`确定要彻底删除数字人形象【${av.name}】(ID: #${av.id}) 吗？此操作不可恢复。`)) {
      return;
    }
    try {
      await client.delete(`/api/v1/avatars/${av.id}`);
      if (previewAvatar && previewAvatar.id === av.id) {
        if (typeof window !== 'undefined' && window.speechSynthesis) {
          window.speechSynthesis.cancel();
        }
        setPreviewAvatar(null);
        setIsPlayingVoice(false);
      }
      await loadData();
    } catch (err: any) {
      console.error('Delete avatar error', err);
      alert(`删除失败: ${err.response?.data?.detail || err.message || '未知错误'}`);
    }
  };

  const handleToggleVoicePreview = () => {
    if (isPlayingVoice) {
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      setIsPlayingVoice(false);
    } else {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const text = '哈喽各位宝贝们！欢迎来到我们的直播间。今天这款爆款好物立减50元，正品保真包邮！喜欢的宝宝赶紧点击右下角小黄车下单抢购吧！';
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'zh-CN';
        utterance.rate = 1.05;
        utterance.pitch = 1.0;

        const voices = window.speechSynthesis.getVoices();
        const zhVoice = voices.find(v => v.lang.includes('zh') || v.name.includes('Chinese') || v.name.includes('Xiaoxiao') || v.name.includes('Tingting'));
        if (zhVoice) {
          utterance.voice = zhVoice;
        }

        utterance.onstart = () => setIsPlayingVoice(true);
        utterance.onend = () => setIsPlayingVoice(false);
        utterance.onerror = () => setIsPlayingVoice(false);

        window.speechSynthesis.speak(utterance);
        setIsPlayingVoice(true);
      } else {
        setIsPlayingVoice(true);
        setTimeout(() => setIsPlayingVoice(false), 4500);
      }
    }
  };

  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const handleApplyToLive = (av: AvatarItem) => {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    navigate(`/admin/live?avatar_id=${av.id}`);
  };

  return (
    <div className="space-y-6">
      {/* 顶部标题与切换栏 */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-100 flex items-center gap-2">
            <UserCheck className="w-5 h-5 text-indigo-400" />
            <span>{t('avatar.title')}</span>
          </h2>
          <p className="text-xs text-gray-400 mt-1">{t('avatar.subtitle')}</p>
        </div>

        <div className="flex items-center gap-3">
          {activeTab === 'avatars' ? (
            <Button
              variant="primary"
              onClick={() => setShowCreateModal(true)}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              {t('avatar.createAvatar')}
            </Button>
          ) : (
            <Button
              variant="primary"
              onClick={() => setShowSceneModal(true)}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              {t('avatar.addScene')}
            </Button>
          )}
        </div>
      </div>

      {/* 选项卡切换 */}
      <div className="flex items-center gap-2 border-b border-white/10 pb-2">
        <button
          onClick={() => setActiveTab('avatars')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'avatars'
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          <UserCheck className="w-4 h-4" />
          <span>数字人形象库 ({avatars.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('scenes')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'scenes'
              ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          <Film className="w-4 h-4" />
          <span>背景场景切片库 ({scenes.length})</span>
        </button>
      </div>

      {/* 选项卡内容 1: 数字人列表 */}
      {activeTab === 'avatars' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {avatars.map((av) => {
            const isVerified = av.status === 'active';
            return (
              <Card key={av.id} interactive className="flex flex-col justify-between overflow-hidden group">
                <div 
                  className="relative h-48 -mx-5 -mt-5 mb-4 overflow-hidden bg-gray-900 cursor-pointer"
                  onClick={() => setPreviewAvatar(av)}
                >
                  <img
                    src={av.preview_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500&auto=format&fit=crop&q=60'}
                    alt={av.name}
                    className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-300 opacity-90 group-hover:opacity-100"
                  />
                  <div className="absolute top-3 right-3">
                    <Badge variant={isVerified ? 'success' : 'danger'} size="sm">
                      {isVerified ? t('avatar.statusActive') : t('avatar.statusArchived')}
                    </Badge>
                  </div>
                  <div className="absolute bottom-2 left-3 flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-black/70 backdrop-blur-md text-[11px] text-gray-200">
                    <Video className="w-3.5 h-3.5 text-indigo-400" />
                    <span className="font-mono">{av.avatar_type}</span>
                  </div>
                  <div className="absolute inset-0 bg-indigo-950/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <span className="px-3 py-1.5 rounded-xl bg-black/80 backdrop-blur-md text-xs text-indigo-300 flex items-center gap-1.5 border border-indigo-500/30 shadow-lg">
                      <Play className="w-3.5 h-3.5 text-indigo-400 fill-indigo-400" />
                      点击预览直播模板
                    </span>
                  </div>
                </div>

                <div className="space-y-2.5">
                  <h3 className="font-semibold text-gray-100 text-base flex items-center gap-1.5">
                    {av.name}
                  </h3>

                  {/* 肖像合规状态 */}
                  <div className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg border ${
                    isVerified 
                      ? 'text-emerald-400 bg-emerald-950/40 border-emerald-500/20' 
                      : 'text-rose-400 bg-rose-950/40 border-rose-500/20'
                  }`}>
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>{isVerified ? `${t('avatar.verified')} (深度合成合规已备案)` : '未完成肖像授权 (禁止开播)'}</span>
                  </div>

                  <div className="flex items-center gap-1.5 text-xs text-indigo-300 pt-1">
                    <Volume2 className="w-3.5 h-3.5" />
                    <span className="font-mono">{av.voice_id}</span>
                  </div>
                </div>

                <div className="pt-4 mt-4 border-t border-white/10 flex items-center justify-between gap-2">
                  <span className="text-[11px] text-gray-500 font-mono shrink-0">ID: #{av.id}</span>
                  <div className="flex items-center gap-1.5 flex-wrap justify-end">
                    <Button 
                      variant="secondary" 
                      size="sm"
                      leftIcon={<Eye className="w-3.5 h-3.5" />}
                      onClick={() => setPreviewAvatar(av)}
                    >
                      {t('avatar.preview')}
                    </Button>
                    <Button
                      variant={isVerified ? 'primary' : 'secondary'}
                      size="sm"
                      leftIcon={<Radio className="w-3.5 h-3.5" />}
                      onClick={() => handleApplyToLive(av)}
                    >
                      设为开播
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-rose-400 hover:text-rose-300 hover:bg-rose-950/40 p-1.5"
                      title="删除此形象"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteAvatar(av);
                      }}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* 选项卡内容 2: 背景场景库 */}
      {activeTab === 'scenes' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {scenes.map((sc) => (
            <Card key={sc.id} className="p-4 space-y-3">
              <div className="aspect-[9/16] bg-gray-900 rounded-xl overflow-hidden relative flex items-center justify-center border border-white/10">
                <Film className="w-10 h-10 text-indigo-500/40 animate-pulse" />
                <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/70 text-[10px] text-gray-300 font-mono">
                  {sc.resolution} · {sc.duration}s
                </div>
                {sc.is_loop && (
                  <div className="absolute top-2 right-2 px-2 py-0.5 rounded bg-indigo-500/30 text-[10px] text-indigo-300">
                    无缝循环
                  </div>
                )}
              </div>
              <h4 className="font-semibold text-gray-100 text-sm">{sc.title}</h4>
              <p className="text-[11px] text-gray-400 font-mono truncate">{sc.video_url}</p>
            </Card>
          ))}
        </div>
      )}

      {/* 新建数字人弹窗 */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="w-full max-w-md p-6 space-y-4">
            <h3 className="text-base font-bold text-gray-100">{t('avatar.createAvatar')}</h3>
            <form onSubmit={handleCreateAvatar} className="space-y-3 text-xs">
              <div>
                <label className="text-gray-300 block mb-1">{t('avatar.name')}</label>
                <Input
                  placeholder="如: 小婉 (官方智能带货主播)"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="text-gray-300 block mb-1">{t('avatar.avatarType')}</label>
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value)}
                  className="w-full bg-gray-900 border border-white/15 rounded-xl px-3 py-2 text-gray-200 text-xs focus:outline-none focus:border-indigo-500"
                >
                  <option value="lingcast_live">LingCast Live (实时口型驱动)</option>
                  <option value="2d_nerf">2D NeRF 高清神经辐射场</option>
                  <option value="wav2lip">Wav2Lip 极速轻量驱动</option>
                </select>
              </div>

              <div>
                <label className="text-gray-300 block mb-1">{t('avatar.voiceId')}</label>
                <Input
                  placeholder="如: zh-CN-XiaoxiaoNeural"
                  value={newVoice}
                  onChange={(e) => setNewVoice(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="text-gray-300 block mb-1">形象封面预览图 URL</label>
                <Input
                  value={newPreviewUrl}
                  onChange={(e) => setNewPreviewUrl(e.target.value)}
                />
              </div>

              <div className="p-2.5 rounded-xl bg-indigo-950/40 border border-indigo-500/30 text-[11px] text-indigo-300 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>新建形象将默认注入系统签约肖像授权，直接通过合规开播审查。</span>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button variant="secondary" type="button" onClick={() => setShowCreateModal(false)}>
                  {t('common.cancel')}
                </Button>
                <Button variant="primary" type="submit">
                  {t('common.save')}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* 新建场景弹窗 */}
      {showSceneModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="w-full max-w-md p-6 space-y-4">
            <h3 className="text-base font-bold text-gray-100">{t('avatar.addScene')}</h3>
            <form onSubmit={handleCreateScene} className="space-y-3 text-xs">
              <div>
                <label className="text-gray-300 block mb-1">场景名称</label>
                <Input
                  placeholder="如: 赛博朋克带货直播间"
                  value={newSceneTitle}
                  onChange={(e) => setNewSceneTitle(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="text-gray-300 block mb-1">背景视频 URL / 路径</label>
                <Input
                  placeholder="https://... 或 /workspace/data/scenes/cyber.mp4"
                  value={newSceneUrl}
                  onChange={(e) => setNewSceneUrl(e.target.value)}
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button variant="secondary" type="button" onClick={() => setShowSceneModal(false)}>
                  {t('common.cancel')}
                </Button>
                <Button variant="primary" type="submit">
                  {t('common.save')}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* 数字人直播间模板实时预览弹窗 */}
      {previewAvatar && (
        <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
          <div className="w-full max-w-4xl bg-gray-950 border border-white/15 rounded-3xl overflow-hidden shadow-2xl flex flex-col md:flex-row max-h-[90vh]">
            {/* 左侧：9:16 模拟手机直播间画面 */}
            <div className="relative w-full md:w-[360px] h-[520px] bg-slate-900 overflow-hidden flex flex-col justify-between p-4 shrink-0">
              {/* 背景图/视频 */}
              <div className="absolute inset-0 z-0">
                <img
                  src={
                    previewTemplate === 'luxury'
                      ? 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800&auto=format&fit=crop&q=80'
                      : previewTemplate === 'tech'
                      ? 'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=800&auto=format&fit=crop&q=80'
                      : 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&auto=format&fit=crop&q=80'
                  }
                  alt="Live Background Template"
                  className="w-full h-full object-cover opacity-40 filter blur-[1px]"
                />
                <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-transparent to-black/80" />
              </div>

              {/* 数字人半身立绘与动态声波 */}
              <div className="absolute inset-x-0 bottom-16 top-16 z-10 flex flex-col items-center justify-center">
                <DynamicAvatarView
                  name=""
                  imageUrl={previewAvatar.preview_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&auto=format&fit=crop&q=80'}
                  voiceId={previewAvatar.voice_id}
                  isSpeaking={isPlayingVoice}
                  isLive={previewAvatar.status === 'active'}
                  size="full"
                  showAudioIndicator={true}
                  showLiveBadge={false}
                  speakingStatusText={isPlayingVoice ? "AI 口型与声音实时驱动中" : (previewAvatar.status === 'active' ? "直播推流中 · 等待口播" : "形象已就绪 · 等待开播")}
                />
              </div>

              {/* 顶部直播间 HUD：主播信息与合规水印 */}
              <div className="relative z-20 flex items-start justify-between gap-2">
                <div className="flex items-center gap-2 bg-black/60 backdrop-blur-md px-2.5 py-1 rounded-full border border-white/10">
                  <div className="w-7 h-7 rounded-full overflow-hidden border border-indigo-400">
                    <img 
                      src={previewAvatar.preview_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500&auto=format&fit=crop&q=60'} 
                      alt="" 
                      className="w-full h-full object-cover" 
                    />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-white leading-tight">{previewAvatar.name}</div>
                    <div className="text-[10px] text-indigo-300 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      <span>{previewAvatar.avatar_type}</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col items-end gap-1">
                  <span className="px-2 py-0.5 rounded-md bg-rose-600 text-[10px] font-bold text-white">LIVE</span>
                  <span className="px-1.5 py-0.5 rounded bg-black/70 text-[9px] text-amber-300 border border-amber-400/30">
                    AI虚拟数字人
                  </span>
                </div>
              </div>

              {/* 底部互动与小黄车 HUD */}
              <div className="relative z-20 space-y-2">
                {/* 模拟弹幕 */}
                <div className="p-2 rounded-xl bg-black/50 backdrop-blur-md border border-white/10 text-[11px] text-gray-200">
                  <span className="text-indigo-400 font-bold">主播口播：</span>
                  <span>{isPlayingVoice ? '哈喽各位宝贝！今天这款爆款好物立减50元，保真包邮！' : '欢迎来到专属直播间，点击右侧音色即可试听试播。'}</span>
                </div>

                {/* 悬浮小黄车 */}
                <div className="flex items-center justify-between p-2 rounded-xl bg-gradient-to-r from-indigo-950/80 to-purple-950/80 border border-indigo-500/40 backdrop-blur-md">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-indigo-600/30 flex items-center justify-center text-indigo-300">
                      <ShoppingBag className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-[11px] font-bold text-white">精选爆款主推商品</div>
                      <div className="text-[10px] text-amber-400 font-bold">¥199.00</div>
                    </div>
                  </div>
                  <button className="px-2.5 py-1 rounded-lg bg-red-600 text-[10px] font-bold text-white shadow-md">
                    立即抢购
                  </button>
                </div>
              </div>
            </div>

            {/* 右侧：直播模板配置与控制面板 */}
            <div className="flex-1 p-6 flex flex-col justify-between overflow-y-auto space-y-5">
              <div>
                <div className="flex items-start justify-between gap-3 border-b border-white/10 pb-4">
                  <div>
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                      <Sparkles className="w-5 h-5 text-indigo-400" />
                      <span>{previewAvatar.name} · 直播间模板预览</span>
                    </h3>
                    <p className="text-xs text-gray-400 mt-1">
                      可视化预览该数字人形象在真实推流场景下的画风、背景切片及口型音色契合度。
                    </p>
                  </div>
                  <Badge variant={previewAvatar.status === 'active' ? 'success' : 'danger'}>
                    {previewAvatar.status === 'active' ? '已签约授权 (可直接开播)' : '已停用/未授权 (禁止开播)'}
                  </Badge>
                </div>

                {/* 详细参数配置矩阵 */}
                <div className="grid grid-cols-2 gap-3 mt-4 text-xs">
                  <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                    <span className="text-gray-400 block text-[11px]">驱动渲染引擎</span>
                    <span className="font-mono text-indigo-300 font-bold mt-0.5 block">{previewAvatar.avatar_type}</span>
                  </div>
                  <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                    <span className="text-gray-400 block text-[11px]">声音音色标识 (Voice ID)</span>
                    <span className="font-mono text-emerald-300 font-bold mt-0.5 block">{previewAvatar.voice_id}</span>
                  </div>
                </div>

                {/* 场景模板选择 */}
                <div className="mt-5 space-y-2">
                  <label className="text-xs font-bold text-gray-200 block">选择虚拟演播厅场景模板</label>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { id: 'luxury', label: '轻奢服装展厅' },
                      { id: 'tech', label: '未来数码科技' },
                      { id: 'green', label: '全景透明绿幕' },
                    ].map((tpl) => (
                      <button
                        key={tpl.id}
                        type="button"
                        onClick={() => setPreviewTemplate(tpl.id as any)}
                        className={`p-2.5 rounded-xl border text-xs font-medium transition-all text-center ${
                          previewTemplate === tpl.id
                            ? 'bg-indigo-600/30 border-indigo-500 text-indigo-200 shadow-md'
                            : 'bg-white/5 border-white/10 text-gray-400 hover:text-white'
                        }`}
                      >
                        {tpl.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* 音色试听交互 */}
                <div className="mt-5 p-3.5 rounded-2xl bg-indigo-950/30 border border-indigo-500/20 flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center">
                      <Volume2 className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-gray-200">试听带货口播与音色拟真度</div>
                      <div className="text-[11px] text-gray-400">实时驱动数字人声波光晕与口播台词</div>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant={isPlayingVoice ? 'danger' : 'primary'}
                    onClick={handleToggleVoicePreview}
                    leftIcon={isPlayingVoice ? <Volume2 className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                  >
                    {isPlayingVoice ? '停止试听' : '试听带货口播'}
                  </Button>
                </div>
              </div>

              {/* 底部动作区域 */}
              <div className="pt-4 border-t border-white/10 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Button
                    variant="danger"
                    size="sm"
                    leftIcon={<Trash2 className="w-3.5 h-3.5" />}
                    onClick={() => handleDeleteAvatar(previewAvatar)}
                  >
                    彻底删除
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleToggleAvatarStatus(previewAvatar)}
                  >
                    {previewAvatar.status === 'active' ? '停用此形象' : '启用并激活肖像授权'}
                  </Button>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="secondary"
                    onClick={() => {
                      if (typeof window !== 'undefined' && window.speechSynthesis) {
                        window.speechSynthesis.cancel();
                      }
                      setPreviewAvatar(null);
                      setIsPlayingVoice(false);
                    }}
                  >
                    关闭预览
                  </Button>
                  <Button
                    variant="primary"
                    leftIcon={<ExternalLink className="w-4 h-4" />}
                    onClick={() => handleApplyToLive(previewAvatar)}
                  >
                    使用此形象前往直播编排
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default AvatarManager;
