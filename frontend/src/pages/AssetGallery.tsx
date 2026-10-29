import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Video, Image as ImageIcon, Loader2, Download } from 'lucide-react';
import { projectsApi, type ProjectAssetsResponse } from '../api/projects';
import { getMediaUrl } from '../api/client';

export default function AssetGallery() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const [assets, setAssets] = useState<ProjectAssetsResponse>({ videos: [], images: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!slug) return;
    
    setIsLoading(true);
    projectsApi.getProjectAssets(slug)
      .then(data => {
        setAssets(data);
      })
      .catch(err => {
        console.error(err);
        setError('Failed to load assets');
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [slug]);

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8 pb-6 border-b border-gray-800">
          <button 
            onClick={() => navigate('/')}
            className="p-2 bg-gray-900 border border-gray-800 hover:bg-gray-800 rounded-xl transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
              资产展厅 (Asset Gallery)
            </h1>
            <p className="text-gray-500 mt-1">Project: {slug}</p>
          </div>
        </div>

        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
          </div>
        ) : error ? (
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400">
            {error}
          </div>
        ) : (
          <div className="space-y-12">
            {/* Videos Section */}
            <section>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-blue-500/20 text-blue-400 rounded-lg">
                  <Video className="w-5 h-5" />
                </div>
                <h2 className="text-xl font-semibold">成片母带 (Rendered Masters)</h2>
              </div>
              
              {assets.videos.length === 0 ? (
                <div className="p-8 border border-dashed border-gray-800 rounded-2xl flex flex-col items-center justify-center text-gray-600">
                  <p>无可用视频资产，任务可能尚未完成生成。</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {assets.videos.map((src, idx) => (
                    <div key={idx} className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden shadow-xl flex flex-col">
                      <video 
                        src={getMediaUrl(src)} 
                        controls 
                        className="w-full aspect-[9/16] object-cover bg-black"
                      />
                      <div className="p-4 border-t border-gray-800 flex items-center justify-between">
                        <p className="text-sm text-gray-400 truncate">Video {idx + 1}</p>
                        <a 
                          href={getMediaUrl(src)} 
                          download 
                          className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                        >
                          <Download className="w-3.5 h-3.5" />
                          下载
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Images Section */}
            <section>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-purple-500/20 text-purple-400 rounded-lg">
                  <ImageIcon className="w-5 h-5" />
                </div>
                <h2 className="text-xl font-semibold">分镜剧本原画 (Storyboards)</h2>
              </div>
              
              {assets.images.length === 0 ? (
                <div className="p-8 border border-dashed border-gray-800 rounded-2xl flex flex-col items-center justify-center text-gray-600">
                  <p>暂无分镜剧本图片资产。</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                  {assets.images.map((src, idx) => (
                    <div key={idx} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden group shadow-md">
                      <div className="aspect-[9/16] overflow-hidden bg-black relative">
                        <img 
                          src={getMediaUrl(src)} 
                          alt={`Storyboard ${idx}`}
                          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110 opacity-85 group-hover:opacity-100"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
