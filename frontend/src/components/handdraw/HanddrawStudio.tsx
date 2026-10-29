import React, { useState } from 'react';
import { 
  PenTool, ShieldCheck, Cpu, CheckCircle2 
} from 'lucide-react';

interface HanddrawStudioProps {
  projectSlug: string;
  handPreset?: string;
  captionStyle?: string;
  paperColor?: string;
  storyboard?: string;
}

export const HanddrawStudio: React.FC<HanddrawStudioProps> = ({
  projectSlug,
  handPreset = 'teacher-pen',
  captionStyle = 'pill_dark',
  paperColor = '#FBF9F1',
  storyboard,
}) => {
  const [activeTab, setActiveTab] = useState<'acts' | 'visuals' | 'rules'>('acts');

  const storyActs = [
    {
      act: 'ACT 1: 痛点共鸣 (0-15s)',
      title: '暴走安保的夺权突袭',
      narration: '你有没有过这种经历：刚冲动发完一段质问，下一秒就恨不得抽自己耳光？这不是你智商不够，而是你的大脑刚刚经历了一场恶性夺权。',
      metaphor: '西装革履的“理智脑总裁” vs 突然掏出电棍暴走的“安保小哥”',
      emotion: '刺痛与共鸣 (High Tension)',
      handMotion: '快速勾勒会议室、暴走安保将总裁反锁进更衣室',
      color: 'border-rose-500/50 bg-rose-950/10 text-rose-300'
    },
    {
      act: 'ACT 2: 机制揭秘 (15-40s)',
      title: '杏仁核劫持与20秒信息差',
      narration: '情绪中枢杏仁核只要20毫秒就能引爆战斗或逃跑，但前额叶理智脑至少要慢半拍。等安保把门焊死，所有决定就全凭肌肉记忆了。',
      metaphor: '大脑横切面：闪电警报直通杏仁核，前额叶理智线掉线灰暗',
      emotion: '恍然大悟 (Cognitive Aha)',
      handMotion: '双色中性笔描线：红色警报闪烁，更衣室门被挂上铁锁链',
      color: 'border-amber-500/50 bg-amber-950/10 text-amber-300'
    },
    {
      act: 'ACT 3: 破局行动 (40-60s)',
      title: '救回总裁的20秒呼吸钥匙',
      narration: '下次血涌上头时，记住：什么都别说，把双手插兜，做三次深长的腹式呼吸。给更衣室里的总裁20秒撬开锁，你的理性就能夺回方向盘。',
      metaphor: '20秒沙漏倒计时，双手插兜，钥匙插入更衣室，总裁重回指挥台',
      emotion: '掌控与释然 (Empowerment)',
      handMotion: '计时器圆环倒数、深呼吸气流波纹、钥匙旋转咔哒解锁',
      color: 'border-emerald-500/50 bg-emerald-950/10 text-emerald-300'
    }
  ];

  return (
    <div className="bg-gray-900/70 border border-gray-800 rounded-2xl p-6 mb-8">
      {/* Studio Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-5 border-b border-gray-800 gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400">
            <PenTool className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white tracking-wide">
                手绘思维推演专属工作台 (Sweety-Handdraw Studio)
              </h2>
              <span className="px-2 py-0.5 text-xs rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 font-mono">
                WCAG 18:1 胶囊字幕
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-1">
              逐笔手绘线稿 · 戈尔曼隐喻双脑模型 · 动态卡点口播 · 纯净无水印
            </p>
          </div>
        </div>

        {/* Configuration Badges */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="px-3 py-1.5 rounded-lg bg-gray-800/80 border border-gray-700 text-xs text-gray-300 flex items-center gap-1.5 font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            手型: {handPreset}
          </span>
          <span className="px-3 py-1.5 rounded-lg bg-gray-800/80 border border-gray-700 text-xs text-gray-300 flex items-center gap-1.5 font-mono">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: paperColor }}></span>
            底纸: {paperColor}
          </span>
          <span className="px-3 py-1.5 rounded-lg bg-gray-800/80 border border-gray-700 text-xs text-gray-300 flex items-center gap-1.5 font-mono">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            字幕: {captionStyle}
          </span>
          <span className="px-3 py-1.5 rounded-lg bg-gray-800/80 border border-gray-700 text-xs text-gray-400 font-mono">
            工程: {projectSlug}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 mt-5 mb-4 border-b border-gray-800/60 pb-2">
        <button
          onClick={() => setActiveTab('acts')}
          className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
            activeTab === 'acts'
              ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
              : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
          }`}
        >
          三幕式心智情绪曲线 (60s)
        </button>
        <button
          onClick={() => setActiveTab('visuals')}
          className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
            activeTab === 'visuals'
              ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
              : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
          }`}
        >
          手绘隐喻配图对齐 (Metaphor Align)
        </button>
        <button
          onClick={() => setActiveTab('rules')}
          className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
            activeTab === 'rules'
              ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
              : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
          }`}
        >
          认知科学声学与排版规范
        </button>
      </div>

      {/* Tab 1: 3 Acts Structure */}
      {activeTab === 'acts' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {storyActs.map((item, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-xl border flex flex-col justify-between transition-all ${item.color}`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono font-bold tracking-wider">{item.act}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-black/40 font-mono">
                      {item.emotion}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-white mb-2">{item.title}</h3>
                  <p className="text-xs text-gray-300 leading-relaxed mb-3">
                    “{item.narration}”
                  </p>
                </div>

                <div className="pt-3 border-t border-white/10 text-xs">
                  <div className="text-gray-400 mb-1 flex items-center gap-1">
                    <Cpu className="w-3 h-3" />
                    <span>视觉隐喻：</span>
                  </div>
                  <div className="text-gray-200 font-medium">{item.metaphor}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 2: Visual Metaphors */}
      {activeTab === 'visuals' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-gray-950 rounded-xl border border-gray-800 flex flex-col gap-2">
            <div className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" />
              <span>镜01：夺权突袭 (前额叶vs杏仁核)</span>
            </div>
            <div className="text-xs text-gray-400">
              黑白双极简手绘线条，理智脑总裁端坐工位，狂躁安保拉响火警、电棍闪烁。
            </div>
          </div>
          <div className="p-4 bg-gray-950 rounded-xl border border-gray-800 flex flex-col gap-2">
            <div className="text-xs font-bold text-amber-400 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" />
              <span>镜02：更衣室铁锁 (理性断联)</span>
            </div>
            <div className="text-xs text-gray-400">
              大号锁链重重卡死衣柜，旁边浮现脉冲波形与大脑反射延迟图谱。
            </div>
          </div>
          <div className="p-4 bg-gray-950 rounded-xl border border-gray-800 flex flex-col gap-2">
            <div className="text-xs font-bold text-blue-400 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" />
              <span>镜03：20秒沙漏与钥匙 (破局掌控)</span>
            </div>
            <div className="text-xs text-gray-400">
              优雅中性笔快速画出沙漏倒计时流沙，气流波浪抚平躁动，衣柜门锁咔哒开启。
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Rules & Guidelines */}
      {activeTab === 'rules' && (
        <div className="p-4 bg-gray-950 rounded-xl border border-gray-800 text-xs text-gray-300 space-y-2">
          <div className="flex items-center gap-2 text-blue-400 font-semibold mb-2">
            <ShieldCheck className="w-4 h-4" />
            <span>手绘短视频制作与合规审计基准：</span>
          </div>
          <p>• <b>拒绝生硬说教</b>：严禁“根据神经生物学研究...”式教科书开场，必须用成年人熟悉的职场、家庭或伴侣吵架具体生活痛点开场。</p>
          <p>• <b>动态语速设计</b>：开场压低声线营造紧迫感（160字/分），中段揭秘提速（180字/分），尾段动作指导放缓平复（140字/分）。</p>
          <p>• <b>严苛字幕标准</b>：采用 85% 半透明深黑胶囊底衬（#1C1F23）+ 48px 粗体纯白无衬线字体，杜绝白纸白字或低对比度导致看不清。</p>
          <p>• <b>纯净商业交付</b>：全流程零水印、零外链广告、零破坏性遮挡，确保 100% 独立商业发布标准。</p>
          {storyboard && (
            <div className="mt-3 pt-2 border-t border-gray-800 text-[11px] text-gray-500 font-mono">
              当前手绘口播台本就绪：已编译 {storyboard.length} 字符分镜指令
            </div>
          )}
        </div>
      )}
    </div>
  );
};
