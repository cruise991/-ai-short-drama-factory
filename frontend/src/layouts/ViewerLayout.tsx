import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { Radio, ArrowLeft } from 'lucide-react';
import { Badge } from '../components/ui/Badge';

export const ViewerLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-black text-gray-100 flex flex-col justify-between selection:bg-indigo-500 selection:text-white">
      {/* Immersive Top Bar */}
      <header className="h-14 bg-gradient-to-b from-black/80 to-transparent absolute top-0 left-0 right-0 z-40 flex items-center justify-between px-4 sm:px-6 pointer-events-auto">
        <div className="flex items-center gap-3">
          <Link
            to="/"
            className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white bg-white/10 hover:bg-white/20 px-2.5 py-1 rounded-full backdrop-blur-md transition-all"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>返回工作台</span>
          </Link>
          <div className="flex items-center gap-2">
            <Badge variant="danger" size="sm" className="animate-pulse">
              <Radio className="w-3 h-3 animate-spin" /> LIVE
            </Badge>
          </div>
        </div>

        {/* AI Disclaimer Watermark Badge */}
        <div className="text-[11px] text-gray-400/90 bg-black/60 backdrop-blur-md px-3 py-1 rounded-full border border-white/10">
          AI虚拟数字人直播中 · 请理性消费
        </div>
      </header>

      {/* Main Stream & Interactive Content */}
      <main className="flex-1 flex flex-col pt-14">
        <Outlet />
      </main>
    </div>
  );
};
