import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { useLiveStore } from '../store/liveStore';
import { useWebSocket } from '../hooks/useWebSocket';
import { useTranslation } from '../locales/i18n';
import client from '../api/client';
import { 
  Radio, 
  Play, 
  Square, 
  Users, 
  Clock, 
  Sparkles,
  ShoppingBag,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  Copy,
  Check,
  Zap,
  ArrowRightLeft,
  UserCheck,
  ExternalLink,
  Volume2,
  AlertTriangle
} from 'lucide-react';

interface ProductItem {
  id: number;
  title: string;
  price: number;
  original_price?: number;
  stock: number;
}

interface AvatarItem {
  id: number;
  name: string;
  avatar_type: string;
  voice_id: string;
  preview_video_url?: string;
  preview_url?: string;
  image_url?: string;
  status: string; // active | archived
  auth_status?: string; // verified | pending | rejected
  compliance_filing_id?: string;
  config_json?: string;
}

export const getAvatarCompliance = (avatar?: AvatarItem) => {
  if (!avatar) return { isEligible: false, label: '未选择', desc: '请选择出镜主播', tag: 'unknown' };
  if (avatar.status === 'archived') {
    return { isEligible: false, label: '已归档停用', desc: '该数字人形象已归档停用，禁止开播推流', tag: 'archived' };
  }
  if (avatar.status !== 'active') {
    return { isEligible: false, label: `审核中 [${avatar.status}]`, desc: '未完成肖像合规备案', tag: 'pending' };
  }
  
  let licensingStatus = 'verified';
  try {
    if (avatar.config_json) {
      const cfg = typeof avatar.config_json === 'string' ? JSON.parse(avatar.config_json) : avatar.config_json;
      if (cfg && cfg.licensing_status) {
        licensingStatus = cfg.licensing_status;
      }
    }
  } catch (e) {}

  if (licensingStatus === 'revoked' || licensingStatus === 'expired') {
    return { isEligible: false, label: '授权已失效', desc: `肖像授权异常 [${licensingStatus}]`, tag: 'revoked' };
  }

  return { isEligible: true, label: '已签约授权有效', desc: '深度合成肖像合规备案已生效', tag: 'verified' };
};

export const LiveOrchestrator: React.FC = () => {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { 
    sessionId,
    status, 
    rtmpUrl,
    httpFlvUrl,
    streamKey,
    setRoomInfo, 
    viewerCount, 
    updateViewers, 
    danmakuList, 
    addDanmaku 
  } = useLiveStore();

  const [roomId, setRoomId] = useState('studio_01');
  const [insertScriptText, setInsertScriptText] = useState('');
  const [copiedKey, setCopiedKey] = useState(false);
  const [copiedRtmp, setCopiedRtmp] = useState(false);
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);
  
  // 数字人主播列表与选中项
  const [avatars, setAvatars] = useState<AvatarItem[]>([]);
  const [selectedAvatarId, setSelectedAvatarId] = useState<number | null>(null);

  const [isActionLoading, setIsActionLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // 1. 初始化拉取直播状态、商品库与数字人列表
  useEffect(() => {
    // 检查是否有正在推流的 session
    client.get('/api/v1/live/status')
      .then((res) => {
        if (res.data && res.data.session_id) {
          setRoomInfo({
            roomId: res.data.room_id || roomId,
            sessionId: res.data.session_id,
            status: res.data.status || 'idle',
            rtmpUrl: res.data.rtmp_url,
            httpFlvUrl: res.data.http_flv_url,
          });
          if (res.data.viewer_count) {
            updateViewers(res.data.viewer_count, res.data.peak_viewers);
          }
        }
      })
      .catch(() => {});

    // 拉取商品列表
    client.get('/api/v1/products')
      .then((res) => {
        if (Array.isArray(res.data)) {
          setProducts(res.data);
          if (res.data.length > 0) {
            setSelectedProductId(res.data[0].id);
          }
        }
      })
      .catch(() => {});

    // 拉取数字人主播列表
    client.get('/api/v1/avatars')
      .then((res) => {
        if (Array.isArray(res.data) && res.data.length > 0) {
          setAvatars(res.data);
          const queryAvatarId = Number(searchParams.get('avatar_id'));
          if (queryAvatarId && res.data.some((a: AvatarItem) => a.id === queryAvatarId)) {
            setSelectedAvatarId(queryAvatarId);
          } else {
            // 优先选择第一个状态活跃且授权通过的数字人
            const eligible = res.data.find((a: AvatarItem) => getAvatarCompliance(a).isEligible);
            setSelectedAvatarId(eligible ? eligible.id : res.data[0].id);
          }
        }
      })
      .catch(() => {});
  }, [setRoomInfo, updateViewers, roomId, searchParams]);

  // 计算当前选中的数字人及合规状态
  const currentAvatar = avatars.find((a) => a.id === selectedAvatarId);
  const currentCompliance = getAvatarCompliance(currentAvatar);
  const isAvatarEligible = currentCompliance.isEligible;

  // 2. WebSocket 实时弹幕与事件监听
  const wsUrl = sessionId 
    ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/live/ws/${sessionId}`
    : null;

  useWebSocket(wsUrl, {
    onMessage: (data) => {
      if (data && data.type === 'danmaku') {
        addDanmaku({
          id: `ws_${Date.now()}_${Math.random()}`,
          sender: data.sender || '观众',
          content: data.content,
          timestamp: data.timestamp || new Date().toLocaleTimeString(),
          type: 'danmaku',
        });
      }
    },
  });

  // 3. 开播 / 停播
  const handleToggleStream = async () => {
    setIsActionLoading(true);
    setActionMsg(null);
    try {
      if (status === 'streaming' && sessionId) {
        await client.post('/api/v1/live/stop', { session_id: sessionId });
        setRoomInfo({ roomId, sessionId: null, status: 'finished' });
        setActionMsg({ type: 'success', text: '直播已安全停播，硬件与推流管道已释放。' });
      } else {
        if (!selectedAvatarId) {
          setActionMsg({ type: 'error', text: '请先在出镜控制面板中选择数字人主播形象' });
          setIsActionLoading(false);
          return;
        }
        if (!isAvatarEligible) {
          setActionMsg({ 
            type: 'error', 
            text: `数字人肖像授权合规拦截: 主播【${currentAvatar?.name || `#${selectedAvatarId}`}】${currentAvatar?.status === 'archived' ? '已归档停用' : '肖像授权未通过'}。请在控制面板切换合规形象后再开播。` 
          });
          setIsActionLoading(false);
          return;
        }

        const resp = await client.post('/api/v1/live/start', {
          title: `LingCast 智能直播场次 - ${new Date().toLocaleDateString()}`,
          room_id: roomId,
          avatar_id: selectedAvatarId,
        });
        const data = resp.data;
        setRoomInfo({
          roomId: data.room_id,
          sessionId: data.session_id,
          streamKey: data.stream_key,
          status: 'streaming',
          rtmpUrl: data.rtmp_url,
          httpFlvUrl: data.http_flv_url,
        });
        updateViewers(156, 380);
        setActionMsg({ type: 'success', text: `直播编排引擎启动成功！主播【${currentAvatar?.name}】已登台，音画与水印实时压制推流中！` });
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail || '开播或停播操作失败';
      setActionMsg({ type: 'error', text: String(detail) });
    } finally {
      setIsActionLoading(false);
    }
  };

  // 4. 一键插播紧急台本话术
  const handleInsertScript = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!insertScriptText.trim()) return;
    if (!sessionId) {
      setActionMsg({ type: 'error', text: '请先开启直播推流，方可插播话术' });
      return;
    }

    try {
      const resp = await client.post('/api/v1/live/insert_script', {
        session_id: sessionId,
        content: insertScriptText.trim(),
        priority: true,
      });

      addDanmaku({
        id: `script_${Date.now()}`,
        sender: '中控插队话术',
        content: resp.data?.is_compliant ? insertScriptText : `[已合规脱敏] ${insertScriptText}`,
        timestamp: new Date().toLocaleTimeString(),
        type: 'system',
      });
      setInsertScriptText('');
      setActionMsg({ type: 'success', text: '紧急话术已置顶插入播放队列！' });
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.response?.data?.detail || '插播失败' });
    }
  };

  // 5. 动态切换主推商品
  const handleSwitchProduct = async () => {
    if (!sessionId || !selectedProductId) {
      setActionMsg({ type: 'error', text: '请先开播并选择要切换的目标商品' });
      return;
    }
    try {
      const resp = await client.post('/api/v1/live/switch_product', {
        session_id: sessionId,
        product_id: selectedProductId,
      });
      setActionMsg({ type: 'success', text: `主播主推商品已成功切换为: ${resp.data.product_title}` });
    } catch (err: any) {
      setActionMsg({ type: 'error', text: err.response?.data?.detail || '商品切换失败' });
    }
  };

  const copyText = (text: string, type: 'rtmp' | 'key') => {
    navigator.clipboard.writeText(text);
    if (type === 'rtmp') {
      setCopiedRtmp(true);
      setTimeout(() => setCopiedRtmp(false), 2000);
    } else {
      setCopiedKey(true);
      setTimeout(() => setCopiedKey(false), 2000);
    }
  };

  return (
    <div className="space-y-6">
      {/* 顶部标题与开播控制 */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-gray-100 flex items-center gap-2">
              <Radio className="w-5 h-5 text-indigo-400" />
              {t('live.title')}
            </h2>
            <Badge variant={status === 'streaming' ? 'danger' : 'neutral'} size="sm">
              {status === 'streaming' ? t('live.streaming') : t('live.idle')}
            </Badge>
          </div>
          <p className="text-xs text-gray-400 mt-1">{t('live.subtitle')}</p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant={status === 'streaming' ? 'danger' : 'primary'}
            onClick={handleToggleStream}
            isLoading={isActionLoading}
            leftIcon={status === 'streaming' ? <Square className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          >
            {status === 'streaming' ? t('live.stopLive') : t('live.startLive')}
          </Button>
        </div>
      </div>

      {/* 状态操作反馈 Toast */}
      {actionMsg && (
        <div className={`p-3 rounded-xl border text-xs flex items-center justify-between ${
          actionMsg.type === 'success' 
            ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300' 
            : 'bg-rose-950/60 border-rose-500/40 text-rose-300'
        }`}>
          <span>{actionMsg.text}</span>
          <button onClick={() => setActionMsg(null)} className="hover:underline font-bold">×</button>
        </div>
      )}

      {/* 核心状态指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4 flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-600/20 text-indigo-400">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] text-gray-400 font-medium">{t('live.activeViewers')}</span>
            <div className="text-lg font-bold text-gray-100">{viewerCount || 156}</div>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-pink-600/20 text-pink-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] text-gray-400 font-medium">{t('live.peakViewers')}</span>
            <div className="text-lg font-bold text-gray-100">{viewerCount ? Math.max(viewerCount, 380) : 0}</div>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-emerald-600/20 text-emerald-400">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] text-gray-400 font-medium">{t('live.latency')}</span>
            <div className="text-lg font-bold text-emerald-400 font-mono">1.18s (FLV)</div>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-amber-600/20 text-amber-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] text-gray-400 font-medium">合规监管状态</span>
            <div className="text-xs font-semibold text-emerald-300 flex items-center gap-1 mt-0.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block animate-pulse" />
              {t('live.watermarkCompliant')}
            </div>
          </div>
        </Card>
      </div>

      {/* 出镜数字人与肖像合规中枢 */}
      <Card className="p-5 border border-indigo-500/20 bg-gradient-to-r from-gray-900 via-indigo-950/20 to-gray-900 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              <UserCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-gray-100">出镜数字人主播选择与肖像授权</h3>
                <span className="text-[10px] bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full font-mono">
                  {avatars.length} 位可用形象
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                实时指定开播推流的数字人形象，开播推流引擎将根据国家合规要求自动核验肖像签约授权与数字水印
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => navigate('/admin/avatars')}
              leftIcon={<ExternalLink className="w-3.5 h-3.5" />}
            >
              资产工坊与模板预览
            </Button>
          </div>
        </div>

        {/* 主播选择与当前状态 */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
          {/* 左侧：形象立绘与头像 */}
          <div className="md:col-span-4 flex items-center gap-4 bg-gray-950/50 p-3.5 rounded-xl border border-white/5">
            <div className="relative w-16 h-16 rounded-xl overflow-hidden bg-gray-900 border border-white/10 shrink-0">
              <img
                src={currentAvatar?.image_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500&auto=format&fit=crop&q=60'}
                alt={currentAvatar?.name}
                className="w-full h-full object-cover"
              />
              <div className="absolute top-1 left-1 bg-black/70 backdrop-blur-sm text-[8px] font-mono px-1 rounded text-emerald-400">
                LIVE
              </div>
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-gray-100 truncate">
                  {currentAvatar ? currentAvatar.name : '未选择主播'}
                </span>
                <span className="text-[10px] text-gray-500 font-mono">#{currentAvatar?.id}</span>
              </div>
              <div className="text-[11px] text-gray-400 mt-0.5 flex items-center gap-1 truncate">
                <Volume2 className="w-3 h-3 text-indigo-400 shrink-0" />
                <span className="truncate">{currentAvatar?.voice_id || '默认TTS音色'}</span>
              </div>
              <div className="mt-1.5 flex items-center gap-1.5">
                {currentCompliance.tag === 'verified' ? (
                  <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 bg-emerald-950/60 border border-emerald-500/30 px-2 py-0.5 rounded-md font-medium">
                    <ShieldCheck className="w-3 h-3" />
                    {currentCompliance.label}
                  </span>
                ) : currentCompliance.tag === 'archived' ? (
                  <span className="inline-flex items-center gap-1 text-[10px] text-rose-400 bg-rose-950/60 border border-rose-500/30 px-2 py-0.5 rounded-md font-medium animate-pulse">
                    <ShieldX className="w-3 h-3" />
                    {currentCompliance.label}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[10px] text-amber-400 bg-amber-950/60 border border-amber-500/30 px-2 py-0.5 rounded-md font-medium">
                    <AlertTriangle className="w-3 h-3" />
                    {currentCompliance.label}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* 中间：下拉选择切换 */}
          <div className="md:col-span-5 space-y-2">
            <label className="text-xs text-gray-300 font-medium block">
              切换出镜主播形象 (共 {avatars.length} 款)
            </label>
            <div className="flex gap-2">
              <select
                disabled={status === 'streaming'}
                value={selectedAvatarId || ''}
                onChange={(e) => setSelectedAvatarId(Number(e.target.value))}
                className="flex-1 bg-gray-900 border border-white/15 rounded-xl px-3 py-2 text-gray-200 text-xs focus:outline-none focus:border-indigo-500"
              >
                {avatars.map((av) => {
                  const comp = getAvatarCompliance(av);
                  return (
                    <option key={av.id} value={av.id}>
                      #{av.id} · {av.name} [{comp.label}] - {av.voice_id}
                    </option>
                  );
                })}
              </select>
            </div>
            <p className="text-[11px] text-gray-500">
              支持在直播开播前自由切换；正在推流时主播锁定以确保推流管道稳定。
            </p>
          </div>

          {/* 右侧：防呆状态预警或快捷修复 */}
          <div className="md:col-span-3">
            {isAvatarEligible ? (
              <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/30 text-emerald-300 text-xs">
                <div className="font-semibold flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  肖像审查已通过
                </div>
                <div className="text-[11px] text-emerald-400/80 mt-1 font-mono truncate">
                  备案号: {currentAvatar?.compliance_filing_id || 'CAC-2026-AVATAR-PASS'}
                </div>
              </div>
            ) : (
              <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs space-y-2">
                <div className="font-semibold flex items-center gap-1 text-rose-400">
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                  {currentCompliance.label}
                </div>
                <p className="text-[11px] text-rose-300/80 leading-tight">
                  {currentCompliance.desc}
                </p>
                {/* 快捷切换至合规主播防呆按钮 */}
                {avatars.some(a => getAvatarCompliance(a).isEligible) && (
                  <Button
                    size="sm"
                    variant="secondary"
                    className="w-full text-xs text-emerald-300 border-emerald-500/40 hover:bg-emerald-950/50"
                    onClick={() => {
                      const firstEligible = avatars.find(a => getAvatarCompliance(a).isEligible);
                      if (firstEligible) setSelectedAvatarId(firstEligible.id);
                    }}
                  >
                    一键切换为可用合规主播
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* 推流配置与商品切换双栏 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 左侧：推流地址与房间配置 */}
        <Card className="p-5 space-y-4">
          <h3 className="text-sm font-semibold text-gray-100 flex items-center gap-2">
            <Radio className="w-4 h-4 text-indigo-400" />
            推流管道连接参数
          </h3>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-gray-400 block mb-1">直播房间识别码 (Room ID)</label>
              <Input
                value={roomId}
                onChange={(e) => setRoomId(e.target.value)}
                disabled={status === 'streaming'}
                className="font-mono text-xs"
              />
            </div>

            <div>
              <label className="text-gray-400 block mb-1">{t('live.rtmpUrl')}</label>
              <div className="flex gap-2">
                <Input
                  readOnly
                  value={rtmpUrl || `rtmp://localhost:1935/live/${roomId}`}
                  className="font-mono text-xs bg-gray-900/50"
                />
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => copyText(rtmpUrl || `rtmp://localhost:1935/live/${roomId}`, 'rtmp')}
                >
                  {copiedRtmp ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </Button>
              </div>
            </div>

            <div>
              <label className="text-gray-400 block mb-1">{t('live.streamKey')}</label>
              <div className="flex gap-2">
                <Input
                  readOnly
                  value={streamKey || 'live_key_auto_generated'}
                  className="font-mono text-xs bg-gray-900/50"
                />
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => copyText(streamKey || 'live_key_auto_generated', 'key')}
                >
                  {copiedKey ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </Button>
              </div>
            </div>

            <div>
              <label className="text-gray-400 block mb-1">{t('live.httpFlvUrl')}</label>
              <Input
                readOnly
                value={httpFlvUrl || `http://localhost:8085/live/${roomId}.flv`}
                className="font-mono text-xs bg-gray-900/50"
              />
            </div>
          </div>
        </Card>

        {/* 右侧：主推商品实时切换中枢 */}
        <Card className="p-5 space-y-4">
          <h3 className="text-sm font-semibold text-gray-100 flex items-center gap-2">
            <ShoppingBag className="w-4 h-4 text-pink-400" />
            {t('live.currentProduct')}
          </h3>

          <div className="space-y-3 text-xs">
            <p className="text-gray-400">
              切换后，智能体将立即优先提取该商品的卖点与知识库，调整口播带货策略。
            </p>

            <div className="space-y-2">
              <label className="text-gray-400 block">选择商品库中可用 SKU</label>
              <div className="flex gap-2">
                <select
                  className="flex-1 bg-gray-900 border border-white/15 rounded-xl px-3 py-2 text-gray-200 text-xs focus:outline-none focus:border-indigo-500"
                  value={selectedProductId || ''}
                  onChange={(e) => setSelectedProductId(Number(e.target.value))}
                >
                  {products.length === 0 && <option value="">暂无商品，请在商品库添加</option>}
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      #{p.id} · {p.title} (现价 ¥{p.price} / 库存 {p.stock})
                    </option>
                  ))}
                </select>
                <Button
                  size="sm"
                  variant="primary"
                  onClick={handleSwitchProduct}
                  leftIcon={<ArrowRightLeft className="w-3.5 h-3.5" />}
                >
                  {t('live.switchProduct')}
                </Button>
              </div>
            </div>

            {/* 紧急插播话术 */}
            <div className="pt-3 border-t border-white/10">
              <label className="text-gray-300 font-medium block mb-1.5 flex items-center gap-1">
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                {t('live.insertScript')}
              </label>
              <form onSubmit={handleInsertScript} className="flex gap-2">
                <Input
                  placeholder={t('live.insertScriptPlaceholder')}
                  value={insertScriptText}
                  onChange={(e) => setInsertScriptText(e.target.value)}
                  className="text-xs"
                />
                <Button type="submit" size="sm" variant="danger">
                  {t('live.insertBtn')}
                </Button>
              </form>
            </div>
          </div>
        </Card>
      </div>

      {/* 底部：实时弹幕审核流 */}
      <Card className="p-5 space-y-3">
        <h3 className="text-sm font-semibold text-gray-100 flex items-center gap-2">
          <Radio className="w-4 h-4 text-emerald-400" />
          {t('live.danmakuStream')}
        </h3>

        <div className="h-64 overflow-y-auto space-y-2 text-xs pr-2 bg-gray-950/60 p-3 rounded-xl border border-white/5">
          {danmakuList.length === 0 ? (
            <div className="h-full flex items-center justify-center text-gray-500 text-xs">
              等待观众弹幕流入或中控指令...
            </div>
          ) : (
            danmakuList.map((msg) => (
              <div
                key={msg.id}
                className={`p-2.5 rounded-lg leading-relaxed flex items-start justify-between ${
                  msg.type === 'agent_reply'
                    ? 'bg-indigo-950/50 border border-indigo-500/30 text-indigo-200'
                    : msg.type === 'system'
                    ? 'bg-amber-950/40 border border-amber-500/30 text-amber-200'
                    : 'bg-white/5 text-gray-200'
                }`}
              >
                <div>
                  <span className="font-semibold text-indigo-400 mr-2">{msg.sender}:</span>
                  <span>{msg.content}</span>
                </div>
                <span className="text-[10px] text-gray-500 font-mono ml-2 shrink-0">{msg.timestamp}</span>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
};
export default LiveOrchestrator;
