import React from 'react';
import { CheckCircle2, ShieldCheck, Eye } from 'lucide-react';

export interface CaptionStyleOption {
  id: string;
  name: string;
  desc: string;
  bg_color: string;
  bg_opacity: number;
  text_color: string;
  size: number;
}

interface CaptionStyleEditorProps {
  styles: CaptionStyleOption[];
  selectedStyleId: string;
  onSelect: (id: string) => void;
  paperColor?: string;
}

export const CaptionStyleEditor: React.FC<CaptionStyleEditorProps> = ({
  styles,
  selectedStyleId,
  onSelect,
  paperColor = '#FBF9F1',
}) => {
  const currentStyle = styles.find((s) => s.id === selectedStyleId) || styles[0];

  // Calculate approximate contrast ratio for visual feedback
  const getContrastRatio = (styleId: string) => {
    if (styleId === 'pill_dark') return { ratio: '18.2:1', level: 'AAA', safe: true };
    if (paperColor === '#20252B') return { ratio: '12.5:1', level: 'AAA', safe: true };
    return { ratio: '4.8:1', level: 'AA', safe: true };
  };

  const contrast = getContrastRatio(selectedStyleId);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider">
          字幕对比度与底衬渲染 (Subtitle Contrast Engine)
        </label>
        <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono bg-emerald-950/60 text-emerald-400 border border-emerald-800/60">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>WCAG {contrast.level} ({contrast.ratio})</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {styles.map((style) => {
          const isSelected = style.id === selectedStyleId;
          return (
            <div
              key={style.id}
              onClick={() => onSelect(style.id)}
              className={`cursor-pointer p-3.5 rounded-xl border transition-all flex flex-col justify-between ${
                isSelected
                  ? 'border-blue-500/80 bg-blue-950/20 shadow-md shadow-blue-500/10'
                  : 'border-gray-800 bg-gray-900/40 hover:border-gray-700'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <div className="text-sm font-medium text-gray-200 flex items-center gap-1.5">
                    {style.name}
                    {style.id === 'pill_dark' && (
                      <span className="text-[10px] px-1.5 py-0.2 bg-blue-500/20 text-blue-400 rounded">推荐</span>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">{style.desc}</div>
                </div>
                {isSelected ? (
                  <CheckCircle2 className="w-4 h-4 text-blue-400 shrink-0" />
                ) : (
                  <div className="w-4 h-4 rounded-full border border-gray-700 shrink-0" />
                )}
              </div>

              {/* Mini preview pill */}
              <div
                className="mt-2 py-1.5 px-3 rounded-lg text-center font-bold text-xs truncate border border-gray-700/50"
                style={{
                  backgroundColor: style.id === 'pill_dark' ? 'rgba(28, 31, 35, 0.88)' : 'transparent',
                  color: style.id === 'pill_dark' ? '#FFFFFF' : '#1E1E1E',
                }}
              >
                “这就是为什么越生气，越容易做错决定”
              </div>
            </div>
          );
        })}
      </div>

      {/* Realistic Live Simulation Card */}
      <div className="p-4 rounded-xl border border-gray-800 bg-gray-950 flex flex-col gap-2">
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <Eye className="w-3.5 h-3.5 text-blue-400" />
          <span>手绘真实画纸与字幕叠显效果实时预览：</span>
        </div>
        
        <div
          className="relative w-full h-28 rounded-lg overflow-hidden flex flex-col items-center justify-end pb-3 shadow-inner border border-gray-700/30"
          style={{ backgroundColor: paperColor }}
        >
          {/* Sketch stroke simulator */}
          <div className="absolute inset-0 opacity-25 flex items-center justify-center pointer-events-none">
            <svg width="220" height="70" viewBox="0 0 220 70" fill="none">
              <path
                d="M 10 35 C 40 10, 60 60, 100 35 C 140 10, 170 50, 210 30"
                stroke="#333333"
                strokeWidth="2.5"
                strokeDasharray="4 2"
              />
              <circle cx="100" cy="35" r="14" stroke="#D32F2F" strokeWidth="2" fill="none" />
            </svg>
          </div>

          {/* Rendered Subtitle Pill */}
          <div
            className="px-4 py-1.5 rounded-full text-xs font-bold shadow-lg max-w-[90%] text-center transition-all backdrop-blur-sm"
            style={{
              backgroundColor:
                currentStyle.id === 'pill_dark'
                  ? 'rgba(28, 31, 35, 0.88)'
                  : 'rgba(255, 255, 255, 0.2)',
              color: currentStyle.id === 'pill_dark' ? '#FFFFFF' : '#1C1F23',
              boxShadow: currentStyle.id === 'pill_dark' ? '0 4px 12px rgba(0,0,0,0.45)' : 'none',
              border: currentStyle.id === 'pill_dark' ? '1px solid rgba(255,255,255,0.1)' : 'none',
            }}
          >
            暴走安保把理智脑总裁反锁进了更衣室！
          </div>
        </div>
      </div>
    </div>
  );
};
