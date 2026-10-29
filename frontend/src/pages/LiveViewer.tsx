import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useLiveStore } from '../store/liveStore';
import { useWebSocket } from '../hooks/useWebSocket';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { LivePlayer } from '../components/LivePlayer';
import { Send, Heart, ShoppingBag, Users, CheckCircle2, Radio, ExternalLink } from 'lucide-react';
import { useTranslation } from '../locales/i18n';
import client from '../api/client';

export const LiveViewer: React.FC = () => {
  const { roomId } = useParams<{ roomId?: string }>();
  const activeRoomId = roomId || 'default';
  const navigate = useNavigate();
  const { t } = useTranslation();
  
  const {
    sessionId,
    httpFlvUrl,
    hlsUrl,
    status,
    danmakuList,
    addDanmaku,
    viewerCount,
    currentProduct,
    isAudioMuted,
    toggleMute,
    setRoomInfo
  } = useLiveStore();

  const [inputText, setInputText] = useState('');
  const [likes, setLikes] = useState(1280);
  const [showHeartAnim, setShowHeartAnim] = useState(false);
  const [purchasedTip, setPurchasedTip] = useState(false);
  
  // 出镜数字人主播与实时话术台本
  const [avatarInfo, setAvatarInfo] = useState<any>(null);
  const [currentScript, setCurrentScript] = useState<string>('');
  const [activeStreamingRoom, setActiveStreamingRoom] = useState<string | null>(null);

  // 初始化拉取房间最新状态
  useEffect(() => {
    client.get(`/api/v1/live/status?room_id=${activeRoomId}`)
      .then((res) => {
        if (res.data) {
          if (res.data.session_id) {
            setRoomInfo({
              roomId: activeRoomId,
              sessionId: res.data.session_id,
              status: res.data.status || 'streaming',
              rtmpUrl: res.data.rtmp_url,
              httpFlvUrl: res.data.http_flv_url,
            });
          }
          if (res.data.avatar) {
            setAvatarInfo(res.data.avatar);
          }
          if (res.data.current_script) {
            setCurrentScript(res.data.current_script);
          }
          if (res.data.active_streaming_room) {
            setActiveStreamingRoom(res.data.active_streaming_room);
          }
        }
      })
      .catch((err) => {
        console.warn('Could not fetch live session info', err);
      });

    // 如果未获取到主播信息，从形象库拉取默认活跃形象
    client.get('/api/v1/avatars')
      .then((res) => {
        if (Array.isArray(res.data) && res.data.length > 0) {
          const eligible = res.data.find((a: any) => a.status === 'active') || res.data[0];
          setAvatarInfo((prev: any) => prev || eligible);
        }
      })
      .catch(() => {});
  }, [activeRoomId, setRoomInfo]);

  // WebSocket 实时弹幕接收
  const wsUrl = sessionId 
    ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/live/ws/${sessionId}`
    : null;

  useWebSocket(wsUrl, {
    onMessage: (data) => {
      if (data && data.type === 'danmaku') {
        addDanmaku({
          id: `msg_${Date.now()}_${Math.random()}`,
          sender: data.sender || '观众',
          content: data.content,
          timestamp: data.timestamp || new Date().toLocaleTimeString(),
          type: 'danmaku',
        });
      }
    },
  });

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const content = inputText.trim();
    setInputText('');

    if (sessionId) {
      try {
        const resp = await client.post('/api/v1/live/danmaku', {
          session_id: sessionId,
          user_name: '我',
          content: content,
        });

        // 本地立即展示已脱敏或清洗后的内容
        const displayContent = resp.data?.violations?.length ? '**** (内容已脱敏)' : content;
        addDanmaku({
          id: `viewer_${Date.now()}`,
          sender: '我',
          content: displayContent,
          timestamp: new Date().toLocaleTimeString(),
          type: 'danmaku',
        });
      } catch (err) {
        console.warn('Send danmaku error', err);
      }
    } else {
      // 离线/模拟测试模式：执行客户端轻量级敏感词过滤兜底
      const prohibitedWords = ['第一', '国家级', '顶级', '最高级', '最佳', '独家首创', '全网首发', '绝无仅有', '史无前例', '赌博', '洗钱', '诈骗'];
      let safeContent = content;
      let isViolation = false;
      for (const pw of prohibitedWords) {
        if (safeContent.includes(pw)) {
          safeContent = safeContent.split(pw).join('*'.repeat(pw.length));
          isViolation = true;
        }
      }

      addDanmaku({
        id: `viewer_${Date.now()}`,
        sender: '我',
        content: isViolation ? `${safeContent} (已按广告法脱敏)` : content,
        timestamp: new Date().toLocaleTimeString(),
        type: 'danmaku',
      });

      setTimeout(() => {
        addDanmaku({
          id: `ai_${Date.now()}`,
          sender: t('viewer.anchor'),
          content: isViolation 
            ? '直播间倡导文明互动与合规交流，请遵守平台公约哦~'
            : '欢迎新进来的朋友！点击右下角小黄车即可领券立减，现货包邮哦！',
          timestamp: new Date().toLocaleTimeString(),
          type: 'agent_reply',
        });
      }, 1500);
    }
  };

  const handleLike = () => {
    setLikes((l) => l + 1);
    setShowHeartAnim(true);
    setTimeout(() => setShowHeartAnim(false), 800);
  };

  const handleBuy = () => {
    setPurchasedTip(true);
    setTimeout(() => setPurchasedTip(false), 2500);
  };

  return (
    <div className="flex-1 flex flex-col md:flex-row relative bg-black overflow-hidden select-none">
      {/* 1. 核心视频播放器视口 */}
      <div className="flex-1 flex items-center justify-center relative bg-gradient-to-tr from-black via-gray-950 to-indigo-950 aspect-[9/16] md:aspect-auto max-h-[92vh]">
        {/* 当前房间若闲置但有热播房间，提供智能感知横幅 */}
        {activeStreamingRoom && activeStreamingRoom !== activeRoomId && (
          <div className="absolute top-16 left-4 right-4 z-40 bg-indigo-950/90 border border-indigo-500/50 backdrop-blur-md px-4 py-2.5 rounded-2xl shadow-2xl flex items-center justify-between text-xs text-indigo-200">
            <div className="flex items-center gap-2">
              <Radio className="w-4 h-4 text-emerald-400 animate-pulse" />
              <span>主播正在 <strong>【{activeStreamingRoom}】</strong> 直播间热播中！当前房间未开播。</span>
            </div>
            <Button
              size="sm"
              variant="primary"
              onClick={() => navigate(`/viewer/${activeStreamingRoom}`)}
              leftIcon={<ExternalLink className="w-3.5 h-3.5" />}
            >
              一键进入热播间
            </Button>
          </div>
        )}

        <LivePlayer
          httpFlvUrl={httpFlvUrl}
          hlsUrl={hlsUrl}
          roomId={activeRoomId}
          isStreaming={status === 'streaming'}
          isAudioMuted={isAudioMuted}
          onToggleMute={toggleMute}
          avatar={avatarInfo}
          currentScript={currentScript}
          className="w-full h-full"
        />

        {/* Top Overlay Stats */}
        <div className="absolute top-4 left-4 z-20 flex items-center gap-2.5">
          <div className="flex items-center gap-1.5 bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10 text-xs text-gray-200">
            <Users className="w-3.5 h-3.5 text-indigo-400" />
            <span>{viewerCount || 382} {t('viewer.viewers')}</span>
          </div>
          <div className="flex items-center gap-1.5 bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10 text-xs text-gray-300">
            <span className={`w-2 h-2 rounded-full ${status === 'streaming' ? 'bg-emerald-400 animate-ping' : 'bg-amber-400'}`} />
            <span>{status === 'streaming' ? '● 直播中' : '闲置未开播'} · 房间: {activeRoomId}</span>
          </div>
        </div>

        {/* 悬浮主推商品卡片 */}
        <div className="absolute bottom-6 left-4 z-20 w-72 bg-black/85 backdrop-blur-md p-3 rounded-2xl border border-white/15 shadow-2xl flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-indigo-600/30 flex items-center justify-center shrink-0 border border-indigo-500/30">
            <ShoppingBag className="w-6 h-6 text-indigo-300" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-xs font-semibold text-gray-100 truncate">
              {currentProduct?.title || '超感重低音智能降噪耳机'}
            </h4>
            <div className="flex items-baseline gap-1.5 mt-0.5">
              <span className="text-sm font-bold text-rose-400">
                ¥{currentProduct?.price || 269.00}
              </span>
              <span className="text-[10px] text-gray-500 line-through">
                ¥{currentProduct?.originalPrice || 599.00}
              </span>
            </div>
          </div>
          <Button
            size="sm"
            variant="danger"
            onClick={handleBuy}
            className="shrink-0 text-xs px-3"
          >
            {t('viewer.buyNow')}
          </Button>
        </div>

        {/* 购买成功浮动提示 */}
        {purchasedTip && (
          <div className="absolute top-20 z-40 flex items-center gap-2 bg-emerald-600 text-white px-4 py-2 rounded-xl shadow-2xl animate-bounce">
            <CheckCircle2 className="w-4 h-4" />
            <span className="text-xs font-semibold">专属优惠券已核销，订单已进入发货流水线！</span>
          </div>
        )}
      </div>

      {/* 2. 右侧互动面板与弹幕流 */}
      <div className="w-full md:w-80 border-t md:border-t-0 md:border-l border-white/10 bg-[#0e1422]/95 backdrop-blur-md flex flex-col justify-between p-4 h-80 md:h-auto">
        <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-2">
          <span className="text-xs font-semibold text-gray-300">{t('viewer.danmakuZone')}</span>
          <div className="relative">
            <button
              onClick={handleLike}
              className="flex items-center gap-1 text-xs text-rose-400 hover:text-rose-300 transition-colors"
            >
              <Heart className="w-4 h-4 fill-rose-500 text-rose-500" />
              <span>{likes}</span>
            </button>
            {showHeartAnim && (
              <Heart className="w-6 h-6 fill-rose-500 text-rose-500 absolute -top-8 left-1 animate-ping pointer-events-none" />
            )}
          </div>
        </div>

        {/* 弹幕滚动列表 */}
        <div className="flex-1 overflow-y-auto space-y-2 text-xs pr-1">
          {danmakuList.map((msg) => (
            <div
              key={msg.id}
              className={`p-2 rounded-xl leading-relaxed ${
                msg.type === 'agent_reply'
                  ? 'bg-indigo-950/70 border border-indigo-500/40 text-indigo-200'
                  : 'bg-white/5 text-gray-200'
              }`}
            >
              <span className="font-semibold text-indigo-400 mr-1.5">{msg.sender}:</span>
              <span>{msg.content}</span>
            </div>
          ))}
        </div>

        {/* 发送弹幕表单 */}
        <form onSubmit={handleSend} className="mt-3 pt-3 border-t border-white/10 flex gap-2">
          <Input
            placeholder={t('viewer.sendPlaceholder')}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            className="text-xs py-1.5"
          />
          <Button type="submit" size="sm" leftIcon={<Send className="w-3.5 h-3.5" />}>
            {t('viewer.sendBtn')}
          </Button>
        </form>
      </div>
    </div>
  );
};
export default LiveViewer;
