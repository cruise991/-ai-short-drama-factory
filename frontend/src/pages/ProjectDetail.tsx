import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, CheckCircle2, Clock, 
  FileText, Film, RefreshCw, Send, Check, Sparkles, Download
} from 'lucide-react';
import { projectsApi, type ProjectDetailResponse, type ProjectAssetsResponse } from '../api/projects';
import { getMediaUrl } from '../api/client';
import { useTranslation } from '../locales/i18n';
import { HanddrawStudio } from '../components/handdraw/HanddrawStudio';

export default function ProjectDetail() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const [detail, setDetail] = useState<ProjectDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [rejectFeedback, setRejectFeedback] = useState('');
  const [submittingAction, setSubmittingAction] = useState(false);
  const [actionSuccessMsg, setActionSuccessMsg] = useState('');
  const [assets, setAssets] = useState<ProjectAssetsResponse | null>(null);

  const fetchDetail = async () => {
    if (!slug) return;
    try {
      const data = await projectsApi.getProjectDetail(slug);
      setDetail(data);
      
      const assetData = await projectsApi.getProjectAssets(slug);
      setAssets(assetData);
    } catch (err) {
      console.error('Failed to load project detail/assets', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
    const interval = setInterval(fetchDetail, 4000);
    return () => clearInterval(interval);
  }, [slug]);

  const handleApprove = async () => {
    if (!detail?.project?.id) return;
    setSubmittingAction(true);
    setActionSuccessMsg('');
    try {
      await projectsApi.approveProject(detail.project.id);
      setActionSuccessMsg(t('detail.messages.approveSuccess'));
      setTimeout(() => fetchDetail(), 1000);
    } catch (err) {
      alert(t('detail.messages.actionFailed'));
    } finally {
      setSubmittingAction(false);
    }
  };

  const handleReject = async () => {
    if (!detail?.project?.id || !rejectFeedback.trim()) return;
    setSubmittingAction(true);
    setActionSuccessMsg('');
    try {
      await projectsApi.rejectProject(detail.project.id, rejectFeedback);
      setRejectFeedback('');
      setActionSuccessMsg(t('detail.messages.rejectSuccess'));
      setTimeout(() => fetchDetail(), 1000);
    } catch (err) {
      alert(t('detail.messages.actionFailed'));
    } finally {
      setSubmittingAction(false);
    }
  };

  const workflowSteps = [
    { id: 'planning', label: t('detail.steps.planning'), status: 'done' },
    { id: 'script', label: t('detail.steps.script'), status: detail?.storyboard ? 'done' : 'current' },
    { id: 'production', label: t('detail.steps.production'), status: ['Assets_Generated', 'Completed'].includes(detail?.current_status || '') ? 'done' : 'pending' },
    { id: 'qa', label: t('detail.steps.qa'), status: detail?.is_waiting_approval ? 'current' : 'pending' },
    { id: 'post', label: t('detail.steps.post'), status: detail?.current_status === 'Completed' ? 'done' : 'pending' },
  ];

  if (loading && !detail) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
        <RefreshCw className="w-8 h-8 text-blue-400 animate-spin mr-3" />
        <span>{t('common.loading')}</span>
      </div>
    );
  }

  const project = detail?.project;
  const isWaiting = detail?.is_waiting_approval;

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Top Navigation */}
        <div className="flex items-center justify-between pb-6 border-b border-gray-800 mb-8">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => navigate('/')}
              className="p-2 bg-gray-900 border border-gray-800 hover:bg-gray-800 rounded-xl transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-gray-400" />
            </button>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-indigo-300 bg-clip-text text-transparent">
                {project?.goal || slug}
              </h1>
              <p className="text-xs text-gray-500 mt-1 font-mono">Slug: {slug} // ID: {project?.id}</p>
            </div>
          </div>

          <button
            onClick={() => navigate(`/projects/${slug}/assets`)}
            className="flex items-center px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-medium rounded-xl shadow-lg shadow-indigo-500/20 transition-all text-sm"
          >
            <Film className="w-4 h-4 mr-2" />
            {t('drama.actions.viewAssets')}
          </button>
        </div>

        {/* Workflow Timeline */}
        <div className="bg-gray-900/60 border border-gray-800 rounded-2xl p-6 mb-8">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Clock className="w-4 h-4 text-blue-400" />
            {t('detail.workflow')}
          </h2>
          <div className="grid grid-cols-5 gap-3">
            {workflowSteps.map((step, idx) => (
              <div 
                key={step.id} 
                className={`p-4 rounded-xl border flex flex-col justify-between transition-all ${
                  step.status === 'done' 
                    ? 'bg-green-950/20 border-green-800/40 text-green-300'
                    : step.status === 'current'
                    ? 'bg-blue-950/30 border-blue-600/50 text-blue-300 shadow-md shadow-blue-500/10 animate-pulse'
                    : 'bg-gray-900/40 border-gray-800 text-gray-500'
                }`}
              >
                <div className="text-xs font-mono mb-1">STAGE 0{idx + 1}</div>
                <div className="font-medium text-sm">{step.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Dedicated Handdraw Studio for Handdraw Video Branch */}
        {project?.branch_type === 'handdraw_video' && (
          <HanddrawStudio 
            projectSlug={slug || ''}
            handPreset={project?.hand_preset}
            captionStyle={project?.caption_style}
            storyboard={detail?.storyboard}
          />
        )}

        {/* Final Output & Dual-Delivery Showcase */}
        {assets && (assets.videos.length > 0 || (assets.drafts && assets.drafts.length > 0)) && (
          <div className="bg-gradient-to-br from-gray-900 via-indigo-950/30 to-purple-950/30 border border-purple-500/30 rounded-2xl p-6 mb-8 shadow-2xl animate-fade-in">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-gray-800">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 bg-emerald-500/20 text-emerald-400 rounded-xl border border-emerald-500/30">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <span>{t('detail.dualDelivery.title')}</span>
                    <span className="text-xs font-normal px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
                      {t('detail.dualDelivery.badge')}
                    </span>
                  </h3>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {t('detail.dualDelivery.desc')}
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-2">
                {assets.drafts && assets.drafts.length > 0 && (
                  <a
                    href={getMediaUrl(assets.drafts[0])}
                    download
                    className="inline-flex items-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-purple-600 via-pink-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-purple-500/25 transition-all active:scale-[0.98]"
                  >
                    <Film className="w-4 h-4 text-purple-200" />
                    <span>{t('detail.dualDelivery.downloadDraft')}</span>
                  </a>
                )}
                {assets.videos.length > 0 && (
                  <a
                    href={getMediaUrl(assets.videos[0])}
                    download
                    className="inline-flex items-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-500/25 transition-all active:scale-[0.98]"
                  >
                    <Download className="w-4 h-4" />
                    <span>{t('detail.dualDelivery.downloadMp4')}</span>
                  </a>
                )}
                {assets.subtitles && assets.subtitles.length > 0 && (
                  <a
                    href={getMediaUrl(assets.subtitles[0])}
                    download
                    className="inline-flex items-center space-x-1.5 px-3 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-xl text-xs font-semibold transition-all border border-gray-700"
                  >
                    <span>{t('detail.dualDelivery.downloadSrt')}</span>
                  </a>
                )}
              </div>
            </div>

            {/* Video Player */}
            {assets.videos.length > 0 && (
              <div className="mt-6 flex justify-center">
                <div className="w-full max-w-sm aspect-[9/16] bg-black rounded-2xl overflow-hidden shadow-2xl border border-gray-800">
                  <video
                    src={getMediaUrl(assets.videos[0])}
                    controls
                    className="w-full h-full object-contain bg-black"
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Approval Card (if waiting) */}
        {isWaiting && (
          <div className="bg-gradient-to-b from-amber-950/30 to-gray-900 border-2 border-amber-500/40 rounded-2xl p-6 mb-8 shadow-xl shadow-amber-500/5">
            <div className="flex items-center gap-3 text-amber-400 mb-3">
              <Sparkles className="w-5 h-5 animate-bounce" />
              <h3 className="text-lg font-bold">{t('detail.waitingApproval')}</h3>
            </div>
            <p className="text-sm text-gray-300 mb-6">{t('detail.approvalTip')}</p>

            {actionSuccessMsg && (
              <div className="mb-4 p-3 bg-green-900/30 border border-green-600/40 text-green-300 text-sm rounded-xl flex items-center gap-2">
                <Check className="w-4 h-4" />
                {actionSuccessMsg}
              </div>
            )}

            <div className="flex flex-col md:flex-row gap-4">
              <button
                onClick={handleApprove}
                disabled={submittingAction}
                className="flex-1 py-3 px-6 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold rounded-xl shadow-lg shadow-emerald-600/20 flex items-center justify-center gap-2 transition-all"
              >
                <CheckCircle2 className="w-5 h-5" />
                {t('detail.approveBtn')}
              </button>

              <div className="flex-[2] flex gap-2">
                <input
                  type="text"
                  value={rejectFeedback}
                  onChange={(e) => setRejectFeedback(e.target.value)}
                  placeholder={t('detail.rejectPlaceholder')}
                  className="flex-1 bg-gray-950 border border-gray-700 focus:border-amber-500 rounded-xl px-4 text-sm text-white outline-none"
                />
                <button
                  onClick={handleReject}
                  disabled={submittingAction || !rejectFeedback.trim()}
                  className="px-5 py-3 bg-rose-700 hover:bg-rose-600 disabled:opacity-40 text-white font-semibold rounded-xl text-sm transition-all flex items-center gap-2"
                >
                  <Send className="w-4 h-4" />
                  {t('detail.rejectBtn')}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Storyboard Script Draft Section */}
        <div className="bg-gray-900/80 border border-gray-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-800">
            <div className="flex items-center gap-2 text-indigo-400">
              <FileText className="w-5 h-5" />
              <h3 className="font-bold text-lg text-white">{t('detail.scriptDraft')}</h3>
            </div>
            <span className="text-xs font-mono bg-gray-800 text-gray-400 px-2.5 py-1 rounded-md">
              STATUS: {detail?.current_status}
            </span>
          </div>

          {detail?.storyboard ? (
            <div className="bg-gray-950 rounded-xl p-6 border border-gray-800/80 font-mono text-sm leading-relaxed text-gray-200 whitespace-pre-wrap max-h-[500px] overflow-y-auto">
              {detail.storyboard}
            </div>
          ) : (
            <div className="text-center py-16 text-gray-500">
              <RefreshCw className="w-8 h-8 mx-auto mb-3 animate-spin text-gray-600" />
              <p>{t('detail.noScriptYet')}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
