import React, { useState, useEffect, useRef } from 'react';
import { Sparkles } from 'lucide-react';

export interface DynamicAvatarViewProps {
  name?: string;
  imageUrl?: string;
  videoUrl?: string;
  voiceId?: string;
  isSpeaking?: boolean;
  isLive?: boolean;
  volume?: number; // 0 to 1
  size?: 'sm' | 'md' | 'lg' | 'full';
  showAudioIndicator?: boolean;
  showLiveBadge?: boolean;
  speakingStatusText?: string;
  className?: string;
}

export const DynamicAvatarView: React.FC<DynamicAvatarViewProps> = ({
  name = '官方签约主播',
  imageUrl = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&auto=format&fit=crop&q=80',
  videoUrl,
  voiceId: _voiceId = 'zh-CN-XiaoxiaoNeural',
  isSpeaking = false,
  isLive = false,
  volume = 0,
  size = 'md',
  showAudioIndicator = true,
  showLiveBadge = true,
  speakingStatusText,
  className = '',
}) => {
  // 眨眼状态机：每 3~5 秒触发一次自然眨眼 (持续约 140ms)
  const [isBlinking, setIsBlinking] = useState(false);
  
  // 嘴形开合程度 (0: 闭合, 1: 最大张开)
  const [mouthOpen, setMouthOpen] = useState(0);
  
  // 头部轻微摆动状态
  const [headTilt, setHeadTilt] = useState(0);

  // 1. 自然生理眨眼定时器
  useEffect(() => {
    let blinkTimer: any;
    const scheduleNextBlink = () => {
      const delay = 2600 + Math.random() * 2400; // 2.6s - 5s 随机间隔
      blinkTimer = setTimeout(() => {
        setIsBlinking(true);
        setTimeout(() => {
          setIsBlinking(false);
          scheduleNextBlink();
        }, 140);
      }, delay);
    };

    scheduleNextBlink();
    return () => clearTimeout(blinkTimer);
  }, []);

  // 2. 拟真音节与声波唇形驱动
  const animationFrameRef = useRef<number | null>(null);
  useEffect(() => {
    let startTime = Date.now();

    const updateLipAndMotion = () => {
      const now = Date.now();
      const elapsed = (now - startTime) / 1000;

      if (isSpeaking) {
        // 多频段音节振荡算法：模拟普通话元音开合、爆破音与语调起伏
        const baseOsc = Math.sin(elapsed * 12.0) * 0.35 + 0.35; // 说话主频
        const harmonic = Math.sin(elapsed * 19.5) * 0.15;      // 辅音微颤
        const pauseMod = Math.sin(elapsed * 2.8) > 0.6 ? 0.2 : 1.0; // 语句顿挫
        
        // 结合外部输入音量 (如果有)
        const volBoost = volume > 0 ? volume * 0.5 : 0;
        const targetOpen = Math.min(1.0, Math.max(0, (baseOsc + harmonic + volBoost) * pauseMod));
        setMouthOpen(targetOpen);

        // 说话时轻微的头部点动 (Cadence Nodding)
        const tilt = Math.sin(elapsed * 4.5) * 1.8;
        setHeadTilt(tilt);
      } else {
        // 静音/未说话状态：嘴唇自然闭合，头部回归极缓呼吸浮动
        setMouthOpen(0);
        const slowBreathing = Math.sin(elapsed * 1.2) * 0.6;
        setHeadTilt(slowBreathing);
      }

      animationFrameRef.current = requestAnimationFrame(updateLipAndMotion);
    };

    animationFrameRef.current = requestAnimationFrame(updateLipAndMotion);
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isSpeaking, volume]);

  // 尺寸映射
  const sizeClasses = {
    sm: 'w-24 h-24',
    md: 'w-48 h-48 sm:w-56 sm:h-56',
    lg: 'w-60 h-60 sm:w-72 sm:h-72',
    full: 'w-56 h-56 sm:w-64 sm:h-64',
  }[size];

  const defaultImg = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&auto=format&fit=crop&q=80';
  const effectiveImageUrl = imageUrl && imageUrl.trim().length > 0 ? imageUrl : defaultImg;

  return (
    <div className={`relative flex flex-col items-center justify-center select-none ${className}`}>
      {/* 外层呼吸声光浪 */}
      <div 
        className={`absolute -inset-6 rounded-full filter blur-2xl opacity-60 transition-all duration-500 pointer-events-none ${
          isSpeaking 
            ? 'bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 scale-110 opacity-80 animate-pulse' 
            : isLive
            ? 'bg-indigo-600/40 scale-100'
            : 'bg-indigo-900/30 scale-95'
        }`} 
      />

      {/* 虚拟主播主体视口 */}
      <div 
        className={`relative ${sizeClasses} rounded-full p-1.5 transition-transform duration-300 shrink-0`}
        style={{
          transform: `translateY(${isSpeaking ? Math.sin(Date.now() / 150) * 1.2 : 0}px) rotate(${headTilt}deg)`,
        }}
      >
        {/* 环形流光边框 */}
        <div 
          className={`absolute inset-0 rounded-full border-2 transition-colors duration-500 ${
            isSpeaking 
              ? 'border-indigo-400 shadow-[0_0_25px_rgba(99,102,241,0.6)]' 
              : 'border-indigo-500/40 shadow-lg'
          }`}
        />

        {/* 形象容器 */}
        <div className="relative w-full h-full rounded-full overflow-hidden bg-gray-950 shadow-2xl">
          {videoUrl ? (
            <video
              src={videoUrl}
              autoPlay
              loop
              muted
              playsInline
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="relative w-full h-full overflow-hidden">
              {/* 底板高清数字人立绘 */}
              <img
                src={effectiveImageUrl}
                alt={name}
                className="w-full h-full object-cover object-center transform scale-105"
                style={{
                  filter: isSpeaking ? 'brightness(1.05)' : 'brightness(1.0)',
                }}
              />

              {/* 动态生理眨眼微遮罩 (位于面部上方眼睛区域) */}
              <div 
                className={`absolute inset-x-0 top-[32%] h-[12%] bg-black/40 backdrop-blur-[0.5px] transition-opacity duration-100 pointer-events-none rounded-full ${
                  isBlinking ? 'opacity-80 scale-y-100' : 'opacity-0 scale-y-0'
                }`}
              />

              {/* 拟真声波唇动驱动遮罩 (位于嘴部区域) */}
              <div 
                className="absolute inset-x-0 bottom-[24%] mx-auto w-[28%] flex items-center justify-center pointer-events-none transition-all duration-75"
                style={{
                  height: `${Math.max(4, mouthOpen * 20)}px`,
                  opacity: mouthOpen > 0.05 ? 0.92 : 0,
                }}
              >
                {/* 唇腔自然阴影与开合 */}
                <div 
                  className="w-full h-full rounded-full bg-gradient-to-b from-[#2a0e14] via-[#481822] to-[#1e070c] border border-rose-900/40 shadow-inner"
                  style={{
                    transform: `scaleX(${1.0 + mouthOpen * 0.15}) scaleY(${mouthOpen})`,
                    transformOrigin: 'center center',
                  }}
                />
              </div>

              {/* 高光与立体光影微动层 */}
              <div 
                className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-indigo-500/10 pointer-events-none"
              />
            </div>
          )}

          {/* LIVE 徽标 */}
          {showLiveBadge && (isLive || isSpeaking) && (
            <div className="absolute top-3 left-3 z-20 bg-rose-600/90 backdrop-blur-sm text-white font-bold text-[9px] px-2 py-0.5 rounded-full shadow-lg flex items-center gap-1 animate-pulse">
              <span className="w-1.5 h-1.5 rounded-full bg-white" />
              LIVE
            </div>
          )}
        </div>

        {/* 底部口型与发声动态徽章 */}
        {showAudioIndicator && (
          <div className="absolute -bottom-3 inset-x-0 mx-auto w-fit z-20">
            <div 
              className={`px-3 py-1 rounded-full text-[10px] flex items-center gap-1.5 shadow-xl backdrop-blur-md border transition-all duration-300 whitespace-nowrap ${
                isSpeaking
                  ? 'bg-indigo-600/95 text-white border-indigo-300 shadow-indigo-500/50 scale-105'
                  : isLive
                  ? 'bg-black/80 text-indigo-300 border-indigo-500/40'
                  : 'bg-black/80 text-gray-400 border-white/10'
              }`}
            >
              {isSpeaking ? (
                <>
                  <span className="flex gap-0.5 items-end h-3">
                    <span className="w-0.5 bg-white animate-pulse" style={{ height: `${Math.max(4, mouthOpen * 12)}px` }} />
                    <span className="w-0.5 bg-indigo-200 animate-bounce" style={{ height: `${Math.max(6, mouthOpen * 14)}px` }} />
                    <span className="w-0.5 bg-white animate-pulse" style={{ height: `${Math.max(4, mouthOpen * 10)}px` }} />
                  </span>
                  <span className="font-medium">{speakingStatusText || 'AI 口型与声音实时驱动中'}</span>
                </>
              ) : isLive ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span>直播推流中 · 等待口播台词</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3 h-3 text-indigo-400" />
                  <span>形象已就绪 · 待命开播</span>
                </>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 主播姓名与参数标注 */}
      {name && (
        <div className="mt-5 text-center pointer-events-none">
          <div className="text-sm font-bold text-gray-100 flex items-center justify-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>{name}</span>
          </div>
        </div>
      )}
    </div>
  );
};
export default DynamicAvatarView;
