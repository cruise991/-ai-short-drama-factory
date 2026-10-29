import { useState, useEffect } from 'react';
import { Play, Activity, Clock, AlertCircle, Plus, Image as ImageIcon, ChevronRight, Trash2, RotateCw, AlertTriangle } from 'lucide-react';
import CreateProjectModal from './CreateProjectModal';
import { useNavigate } from 'react-router-dom';
import { projectsApi, type Project } from '../api/projects';
import { useTranslation } from '../locales/i18n';

const ProjectList = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<number | null>(null);
  const navigate = useNavigate();
  const { t } = useTranslation();

  const fetchProjects = async () => {
    try {
      const data = await projectsApi.getProjects();
      setProjects(data);
    } catch (error) {
      console.error("Error fetching projects", error);
    }
  };

  const handleDeleteProject = async (projectId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm("确定要删除该短剧工单吗？此操作不可逆。")) return;
    try {
      setActionLoadingId(projectId);
      await projectsApi.deleteProject(projectId);
      await fetchProjects();
    } catch (err) {
      console.error("Failed to delete project", err);
      alert("删除失败，请稍后重试");
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleRetryProject = async (projectId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      setActionLoadingId(projectId);
      await projectsApi.retryProject(projectId);
      await fetchProjects();
    } catch (err) {
      console.error("Failed to retry project", err);
      alert("重试触发失败，请稍后重试");
    } finally {
      setActionLoadingId(null);
    }
  };

  useEffect(() => {
    fetchProjects();
    const interval = setInterval(fetchProjects, 4000);
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Pending':
        return <span className="flex items-center text-yellow-400 bg-yellow-400/10 px-2 py-1 rounded text-xs"><Clock className="w-3 h-3 mr-1" /> {t('drama.status.pending')}</span>;
      case 'Draft_Completed':
        return <span className="flex items-center text-indigo-300 bg-indigo-500/20 border border-indigo-500/40 px-2 py-1 rounded text-xs font-semibold animate-pulse"><Clock className="w-3 h-3 mr-1" /> {t('drama.status.draftCompleted')}</span>;
      case 'Running':
      case 'Drafting':
      case 'Assets_Generated':
        return <span className="flex items-center text-blue-400 bg-blue-400/10 px-2 py-1 rounded text-xs"><Activity className="w-3 h-3 mr-1" /> {status.replace('_', ' ')}</span>;
      case 'Paused_By_Error':
        return <span className="flex items-center text-red-400 bg-red-400/10 px-2 py-1 rounded text-xs"><AlertCircle className="w-3 h-3 mr-1" /> {t('drama.status.pausedByError')}</span>;
      case 'Completed':
        return <span className="flex items-center text-green-400 bg-green-400/10 px-2 py-1 rounded text-xs"><Play className="w-3 h-3 mr-1" /> {t('drama.status.completed')}</span>;
      default:
        return <span className="flex items-center text-gray-400 bg-gray-400/10 px-2 py-1 rounded text-xs">{status}</span>;
    }
  };

  return (
    <div className="flex-1 p-8 overflow-y-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-white mb-1">{t('drama.title')}</h2>
          <p className="text-gray-400 text-sm">{t('drama.subtitle')}</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="flex items-center bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 rounded-xl shadow-lg shadow-blue-500/20 font-medium transition-all"
        >
          <Plus className="w-4 h-4 mr-2" />
          {t('drama.newProject')}
        </button>
      </div>

      {projects.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 border border-dashed border-gray-800 rounded-2xl bg-gray-950/40">
          <p className="text-gray-400 mb-4">{t('drama.empty')}</p>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-xl transition-colors text-sm"
          >
            {t('drama.createFirst')}
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map(project => (
            <div 
              key={project.id} 
              className="group bg-gray-950 border border-gray-800 rounded-2xl p-5 hover:border-blue-500/50 transition-all shadow-xl flex flex-col justify-between cursor-pointer"
              onClick={() => navigate(`/projects/${project.project_slug}`)}
            >
              <div>
                <div className="flex justify-between items-start mb-3">
                  <h3 className="text-base font-semibold text-white group-hover:text-blue-400 transition-colors line-clamp-2" title={project.goal}>
                    {project.goal}
                  </h3>
                  {getStatusBadge(project.status)}
                </div>
                <div className="text-xs text-gray-500 mb-3 space-y-1 font-mono">
                  <p><span className="text-gray-600">SLUG:</span> {project.project_slug}</p>
                  <p><span className="text-gray-600">FORMAT:</span> {project.format_type}</p>
                </div>

                {project.error_message && (
                  <div className="bg-red-950/40 border border-red-800/60 rounded-xl p-3 mb-3 text-xs text-red-300">
                    <div className="flex items-center gap-1.5 font-semibold text-red-400 mb-1">
                      <AlertTriangle className="w-3.5 h-3.5 text-red-400 shrink-0" />
                      <span>异常诊断与修复建议</span>
                    </div>
                    <p className="line-clamp-3 text-gray-300 font-mono text-[11px] leading-relaxed">
                      {project.error_message}
                    </p>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-gray-800/80" onClick={e => e.stopPropagation()}>
                <span className="text-xs text-gray-500">
                  {new Date(project.created_at).toLocaleDateString()}
                </span>
                <div className="flex items-center gap-1.5">
                  {project.status === 'Paused_By_Error' && (
                    <button 
                      onClick={(e) => handleRetryProject(project.id, e)}
                      disabled={actionLoadingId === project.id}
                      className="flex items-center gap-1 px-2.5 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 rounded-lg transition-colors text-xs font-medium border border-amber-500/30 disabled:opacity-50"
                      title="重置状态并重试执行"
                    >
                      <RotateCw className={`w-3.5 h-3.5 ${actionLoadingId === project.id ? 'animate-spin' : ''}`} />
                      重试
                    </button>
                  )}
                  <button 
                    onClick={() => navigate(`/projects/${project.project_slug}/assets`)}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-900 hover:bg-gray-800 text-gray-300 rounded-lg transition-colors text-xs font-medium border border-gray-800"
                    title={t('drama.actions.viewAssets')}
                  >
                    <ImageIcon className="w-3.5 h-3.5 text-purple-400" />
                    Assets
                  </button>
                  <button 
                    onClick={() => navigate(`/projects/${project.project_slug}`)}
                    className="flex items-center gap-1 px-3 py-1.5 bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 rounded-lg transition-colors text-xs font-medium border border-blue-500/20"
                  >
                    Timeline
                    <ChevronRight className="w-3 h-3" />
                  </button>
                  <button 
                    onClick={(e) => handleDeleteProject(project.id, e)}
                    disabled={actionLoadingId === project.id}
                    className="flex items-center justify-center p-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 hover:text-rose-300 rounded-lg transition-colors border border-rose-500/20 disabled:opacity-50"
                    title="删除此工单"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {isModalOpen && (
        <CreateProjectModal 
          onClose={() => setIsModalOpen(false)} 
          onSuccess={() => {
            setIsModalOpen(false);
            fetchProjects();
          }} 
        />
      )}
    </div>
  );
};

export default ProjectList;
