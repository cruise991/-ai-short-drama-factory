import React, { useState, useEffect, useRef, useMemo } from 'react'
import { useTranslation } from '../locales/i18n'
import { 
  UploadCloud, Sparkles, Flame, CheckCircle2, 
  AlertCircle, Download, RotateCcw, Clock, Layers, Sliders,
  Film, ShieldCheck, Zap, RefreshCw, Play
} from 'lucide-react'
import { danceApi, type DanceTemplate, type DanceTaskStatus, type MultiViewResult, type PoseSlot } from '../api/dance'
import { getMediaUrl } from '../api/client'
import { useAuthStore } from '../store/authStore'
import { ChoreographyWorkbench } from '../components/dance/ChoreographyWorkbench'

type TemplateCategory = 'all' | 'kpop' | 'fitness' | 'street' | 'luxury'
type StudioMode = 'template' | 'choreography'

export default function DanceStudio() {
  const { t } = useTranslation()
  const { user } = useAuthStore()
  const [studioMode, setStudioMode] = useState<StudioMode>('choreography')
  const [templates, setTemplates] = useState<DanceTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<DanceTemplate | null>(null)
  const [activeCategory, setActiveCategory] = useState<TemplateCategory>('all')
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [multiViewData, setMultiViewData] = useState<MultiViewResult | null>(null)
  const [selectedViewIndex, setSelectedViewIndex] = useState<number | null>(null)
  const [isAnalyzingViews, setIsAnalyzingViews] = useState<boolean>(false)
  const [aspectRatio, setAspectRatio] = useState<string>('9:16')
  const [duration, setDuration] = useState<number>(20)
  const [style, setStyle] = useState<string>('fitness')
  const [promptDesc, setPromptDesc] = useState<string>('')
  const [customBpm, setCustomBpm] = useState<number>(120)
  const [loading, setLoading] = useState<boolean>(false)
  const [currentTask, setCurrentTask] = useState<DanceTaskStatus | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    fetchTemplates()
    const params = new URLSearchParams(window.location.search)
    const tid = params.get('task_id')
    if (tid) {
      danceApi.getTaskStatus(tid).then(taskData => {
        if (taskData) {
          setCurrentTask(taskData)
          if (taskData.duration) setDuration(taskData.duration)
          if (taskData.style) setStyle(taskData.style)
          if (taskData.status === 'processing' || taskData.status === 'queued') {
            setLoading(true)
            pollTaskStatus(tid)
          }
        }
      }).catch(console.error)
    }
  }, [])

  const fetchTemplates = async () => {
    try {
      const data = await danceApi.getTemplates()
      setTemplates(data)
      if (data.length > 0) {
        setSelectedTemplate(data[0])
        const firstBpm = parseInt(data[0].bpm?.split('-')[0]) || 120
        setCustomBpm(firstBpm)
      }
    } catch (err) {
      console.error('Failed to fetch dance templates', err)
    }
  }

  // Filter templates by category
  const filteredTemplates = useMemo(() => {
    if (activeCategory === 'all') return templates
    return templates.filter(tpl => {
      const tagsStr = (tpl.tags || []).join(' ').toLowerCase()
      const nameStr = (tpl.name || '').toLowerCase()
      const combined = `${tagsStr} ${nameStr}`
      if (activeCategory === 'kpop') {
        return combined.includes('kpop') || combined.includes('女团') || combined.includes('aespa') || combined.includes('blackpink') || combined.includes('angel')
      }
      if (activeCategory === 'fitness') {
        return combined.includes('健身') || combined.includes('活力') || combined.includes('扭胯') || combined.includes('上车') || combined.includes('库里') || combined.includes('动力学') || combined.includes('kinetic')
      }
      if (activeCategory === 'street') {
        return combined.includes('街头') || combined.includes('律动') || combined.includes('搞笑') || combined.includes('科目三') || combined.includes('二摆')
      }
      if (activeCategory === 'luxury') {
        return combined.includes('慢摇') || combined.includes('纯欲') || combined.includes('曲线') || combined.includes('甜美') || combined.includes('高精度') || combined.includes('precision')
      }
      return true
    })
  }, [templates, activeCategory])

  const clearUrlTaskId = () => {
    if (window.location.search.includes('task_id')) {
      window.history.replaceState(null, '', '/dance')
    }
  }

  const handleProcessFile = async (file: File) => {
    setImageFile(file)
    setImagePreview(URL.createObjectURL(file))
    setErrorMsg(null)
    setMultiViewData(null)
    setSelectedViewIndex(null)
    if (currentTask) {
      setCurrentTask(null)
    }
    clearUrlTaskId()

    try {
      setIsAnalyzingViews(true)
      const fd = new FormData()
      fd.append('image', file)
      fd.append('tenant_id', user?.tenant_id || 'default')
      const res = await danceApi.analyzeViews(fd)
      setMultiViewData(res)
      if (res && res.views && res.views.length > 0) {
        const prim = res.views.find(v => v.is_primary_start)
        setSelectedViewIndex(prim ? prim.index : 0)
      }
    } catch (e) {
      console.warn('Auto view analysis skipped or failed:', e)
    } finally {
      setIsAnalyzingViews(false)
    }
  }

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleProcessFile(e.target.files[0])
    }
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleProcessFile(e.dataTransfer.files[0])
    }
  }

  const handleSelectTemplate = (tpl: DanceTemplate) => {
    setSelectedTemplate(tpl)
    if (tpl.bpm) {
      const b = parseInt(tpl.bpm.split('-')[0]) || 120
      setCustomBpm(b)
    }
    // Auto sync style recommendation if matching
    const tags = (tpl.tags || []).join(' ')
    if (tags.includes('kpop') || tags.includes('女团')) setStyle('kpop')
    else if (tags.includes('健身') || tags.includes('活力') || tags.includes('动力学')) setStyle('fitness')
    else if (tags.includes('慢摇') || tags.includes('纯欲') || tags.includes('奢华') || tags.includes('高精度')) setStyle('luxury')
    else if (tags.includes('律动') || tags.includes('街头')) setStyle('street')

    // Selecting new motion resets completed display so user can render newly selected motion
    if (currentTask) {
      setCurrentTask(null)
      clearUrlTaskId()
    }
  }

  const handleStartGeneration = async () => {
    if (!imageFile) {
      setErrorMsg(t('dance.cta.needImage'))
      return
    }
    setErrorMsg(null)
    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('image', imageFile)
      formData.append('duration', duration.toString())
      formData.append('style', style)
      formData.append('bpm', customBpm.toString())
      formData.append('tenant_id', user?.tenant_id || 'default')
      formData.append('aspect_ratio', aspectRatio)
      if (selectedViewIndex !== null) {
        formData.append('selected_view_index', selectedViewIndex.toString())
      }
      if (selectedTemplate) {
        formData.append('template_id', selectedTemplate.dance_id)
      }
      if (promptDesc.trim()) {
        formData.append('prompt_desc', promptDesc.trim())
      }

      const res = await danceApi.generateDance(formData)
      const taskId = res.task_id
      window.history.replaceState(null, '', `/dance?task_id=${taskId}`)
      pollTaskStatus(taskId)
    } catch (err: any) {
      setLoading(false)
      setErrorMsg(err?.response?.data?.detail || t('dance.character.failedToSubmit'))
    }
  }

  const handleStartChoreograph = async (
    sequence: PoseSlot[],
    choreoBpm: number,
    choreoStyle: string,
    enableJianying: boolean
  ) => {
    if (!imageFile) {
      setErrorMsg(t('dance.cta.needImage'))
      return
    }
    setErrorMsg(null)
    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('image', imageFile)
      formData.append('sequence_json', JSON.stringify(sequence))
      formData.append('bpm', choreoBpm.toString())
      formData.append('style', choreoStyle)
      formData.append('enable_jianying_draft', enableJianying ? 'true' : 'false')
      formData.append('tenant_id', user?.tenant_id || 'default')
      formData.append('aspect_ratio', aspectRatio)
      if (selectedViewIndex !== null) {
        formData.append('selected_view_index', selectedViewIndex.toString())
      }

      const res = await danceApi.choreographDance(formData)
      const taskId = res.task_id
      window.history.replaceState(null, '', `/dance?task_id=${taskId}`)
      pollTaskStatus(taskId)
    } catch (err: any) {
      setLoading(false)
      setErrorMsg(err?.response?.data?.detail || t('dance.character.failedToSubmit'))
    }
  }

  const pollTaskStatus = (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const taskData = await danceApi.getTaskStatus(taskId)
        setCurrentTask(taskData)

        if (taskData.status === 'completed') {
          clearInterval(interval)
          setLoading(false)
        } else if (taskData.status === 'failed') {
          clearInterval(interval)
          setLoading(false)
          setErrorMsg(taskData.message || t('dance.character.generationFailed'))
        }
      } catch (err) {
        console.error('Polling error', err)
      }
    }, 2000)
  }

  const handleResetForNew = () => {
    setCurrentTask(null)
    setImageFile(null)
    setImagePreview(null)
    setErrorMsg(null)
    clearUrlTaskId()
  }

  // Active duration for display (prioritize task duration if available)
  const displayDuration = currentTask?.duration || duration

  return (
    <div className="p-6 lg:p-8 max-w-[1600px] mx-auto space-y-8 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-800/80 pb-6">
        <div className="flex items-center space-x-3.5">
          <div className="p-3 bg-gradient-to-tr from-pink-500/20 via-purple-500/20 to-indigo-500/20 border border-pink-500/30 rounded-2xl shadow-lg shadow-pink-500/10">
            <Flame className="w-7 h-7 text-pink-400 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl lg:text-3xl font-bold bg-gradient-to-r from-pink-400 via-purple-300 to-indigo-400 bg-clip-text text-transparent">
                {t('dance.title')}
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center space-x-1.5 shadow-sm shadow-emerald-500/10">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span>{t('dance.badges.v2Engine')}</span>
              </span>
            </div>
            <p className="text-xs lg:text-sm text-gray-400 mt-1">
              {t('dance.subtitle', { count: templates.length || 14 })}
            </p>
          </div>
        </div>

        {/* Status Badges */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-gray-900/80 border border-pink-500/30 text-xs text-pink-300 shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-pink-400" />
            <span>{t('dance.badges.facialFidelity')}</span>
          </div>
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-gray-900/80 border border-amber-500/30 text-xs text-amber-300 shadow-sm">
            <Flame className="w-3.5 h-3.5 text-amber-400" />
            <span>{t('dance.badges.curvySilhouette')}</span>
          </div>
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-gray-900/80 border border-gray-800 text-xs text-gray-300">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>{t('dance.badges.antiCompression')}</span>
          </div>
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-gray-900/80 border border-gray-800 text-xs text-gray-300">
            <Zap className="w-3.5 h-3.5 text-purple-400" />
            <span>{t('dance.badges.deterministicLoop')}</span>
          </div>
        </div>
      </div>

      {/* Global Error Alert */}
      {errorMsg && (
        <div className="p-4 bg-red-950/40 border border-red-500/30 rounded-2xl flex items-center space-x-3 text-red-400 text-sm animate-shake">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Studio Mode Switcher: 自由动作编舞 vs 官方爆款模版 */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-2 bg-gray-950/80 border border-gray-800/80 rounded-2xl shadow-lg">
        <div className="flex items-center space-x-2">
          <button 
            onClick={() => setStudioMode('choreography')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 shadow-sm ${
              studioMode === 'choreography'
                ? 'bg-gradient-to-r from-purple-600 via-pink-600 to-indigo-600 text-white shadow-purple-500/25 scale-[1.02]'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-900'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-pink-300" />
            <span>{t('dance.mode.choreography')}</span>
            <span className="px-1.5 py-0.2 bg-white/20 rounded-full text-[9px] font-mono">NEW</span>
          </button>
          
          <button 
            onClick={() => setStudioMode('template')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 shadow-sm ${
              studioMode === 'template'
                ? 'bg-gradient-to-r from-pink-500 to-purple-600 text-white shadow-pink-500/25 scale-[1.02]'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-900'
            }`}
          >
            <Flame className="w-3.5 h-3.5 text-amber-300" />
            <span>{t('dance.mode.template')}</span>
          </button>
        </div>

        <div className="text-xs text-gray-400 flex items-center space-x-2 px-3">
          <Film className="w-3.5 h-3.5 text-purple-400" />
          <span>{t('dance.mode.dualDelivery')}</span>
        </div>
      </div>

      {/* Studio Workbench: Left Control Panel + Right Stage */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
        
        {/* ================= LEFT: Creation Control Studio ================= */}
        <div className={`${studioMode === 'choreography' ? 'xl:col-span-7' : 'xl:col-span-5'} space-y-6`}>
          {studioMode === 'choreography' ? (
            <ChoreographyWorkbench
              imageFile={imageFile}
              imagePreview={imagePreview}
              onStartChoreograph={handleStartChoreograph}
              loading={loading}
            />
          ) : (
            <>
              {/* Section 1: Template Selector */}
              <div className="bg-gray-950 border border-gray-800/80 rounded-2xl p-4 lg:p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Layers className="w-4 h-4 text-pink-400" />
                <h3 className="text-sm font-semibold text-gray-200">
                  {t('dance.templates.title')}
                </h3>
              </div>
              <span className="text-xs text-gray-400">
                {t('dance.templates.count', { count: templates.length || 14 })}
              </span>
            </div>

            {/* Category Filter Tabs */}
            <div className="flex items-center space-x-1.5 bg-gray-900/80 p-1 rounded-xl border border-gray-800 overflow-x-auto">
              {[
                { id: 'all', label: t('dance.templates.tabs.all') },
                { id: 'kpop', label: t('dance.templates.tabs.kpop') },
                { id: 'fitness', label: t('dance.templates.tabs.fitness') },
                { id: 'street', label: t('dance.templates.tabs.street') },
                { id: 'luxury', label: t('dance.templates.tabs.luxury') }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveCategory(tab.id as TemplateCategory)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                    activeCategory === tab.id
                      ? 'bg-gradient-to-r from-pink-500/20 to-purple-500/20 text-pink-300 border border-pink-500/30'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Compact Template Matrix */}
            <div className="grid grid-cols-2 gap-2.5 max-h-[210px] overflow-y-auto pr-1">
              {filteredTemplates.map((tpl) => {
                const isSelected = selectedTemplate?.dance_id === tpl.dance_id
                return (
                  <div
                    key={tpl.dance_id}
                    onClick={() => handleSelectTemplate(tpl)}
                    className={`p-3 rounded-xl border transition-all cursor-pointer flex flex-col justify-between space-y-2 text-left ${
                      isSelected
                        ? 'bg-pink-500/10 border-pink-500 shadow-md shadow-pink-500/10 ring-1 ring-pink-500/50'
                        : 'bg-gray-900/60 border-gray-800/80 hover:bg-gray-900 hover:border-gray-700'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between gap-1">
                        <span className="font-bold text-xs text-gray-100 truncate">
                          {tpl.name}
                        </span>
                        <span className="px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 text-[10px] font-mono whitespace-nowrap">
                          {tpl.bpm} BPM
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {(tpl.tags || []).slice(0, 2).map((tag, idx) => (
                          <span key={idx} className="px-1.5 py-0.2 rounded bg-gray-800 text-gray-400 text-[9px]">
                            #{tag}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="pt-1.5 border-t border-gray-800/60 flex items-center justify-between text-[10px]">
                      <span className="text-gray-500">{tpl.stats?.views || '10w+'}</span>
                      <span className={`font-semibold ${isSelected ? 'text-pink-400' : 'text-gray-400'}`}>
                        {isSelected ? `✓ ${t('dance.templates.selected')}` : t('dance.templates.select')}
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Section 2: Character Reference Image */}
          <div className="bg-gray-950 border border-gray-800/80 rounded-2xl p-5 lg:p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Film className="w-4 h-4 text-purple-400" />
                <h3 className="text-sm font-semibold text-gray-200">
                  {t('dance.character.title')}
                </h3>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-xs text-pink-400/80 bg-pink-500/10 px-2 py-0.5 rounded-full font-mono">
                  {aspectRatio === '9:16' ? t('dance.params.ratio916') : t('dance.params.ratio169')}
                </span>
                {imagePreview && (
                  <button 
                    onClick={() => { setImageFile(null); setImagePreview(null) }}
                    className="text-xs text-gray-400 hover:text-red-400 transition-colors"
                  >
                    {t('dance.character.reselect')}
                  </button>
                )}
              </div>
            </div>

            {/* Drop & Upload Box */}
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`relative border-2 border-dashed rounded-xl transition-all cursor-pointer overflow-hidden flex flex-col items-center justify-center ${
                imagePreview 
                  ? `border-gray-700 bg-gray-900/50 ${aspectRatio === '16:9' ? 'aspect-[16/9] max-h-[300px]' : 'aspect-[9/16] max-h-[380px]'}` 
                  : 'border-gray-700/80 hover:border-pink-500/50 bg-gray-900/30 py-12 hover:bg-gray-900/50'
              }`}
            >
              <input 
                ref={fileInputRef} 
                type="file" 
                accept="image/*" 
                className="hidden" 
                onChange={handleImageChange} 
              />

              {imagePreview ? (
                <div className="relative w-full h-full group">
                  <img 
                    src={imagePreview} 
                    alt="Character Reference" 
                    className="w-full h-full object-contain" 
                  />
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <span className="px-3 py-1.5 bg-gray-900/80 text-xs text-white rounded-lg border border-gray-700">
                      {t('dance.character.reselect')}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="text-center px-4 space-y-2.5">
                  <div className="w-11 h-11 rounded-full bg-pink-500/10 border border-pink-500/20 flex items-center justify-center mx-auto text-pink-400">
                    <UploadCloud className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-gray-200">
                      {t('dance.character.uploadTitle')}
                    </p>
                    <p className="text-[11px] text-gray-400 mt-0.5">
                      {t('dance.character.uploadDesc')}
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Privacy & AI Vision Analysis Notice */}
            <p className="text-[10px] text-gray-400 mt-2 text-center flex items-center justify-center space-x-1">
              <span>🔒</span>
              <span>{t('dance.stage.privacyNotice')}</span>
            </p>

            {/* Multi-view Analyzing Indicator */}
            {isAnalyzingViews && (
              <div className="p-3 bg-purple-500/10 border border-purple-500/30 rounded-xl flex items-center space-x-2 text-xs text-purple-300 animate-pulse">
                <RefreshCw className="w-4 h-4 animate-spin text-purple-400" />
                <span>{t('dance.multiview.detecting')}</span>
              </div>
            )}

            {/* Multi-view detected card selector */}
            {multiViewData && multiViewData.is_multiview && (
              <div className="p-3 bg-gray-900/90 border border-purple-500/40 rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-1.5 text-xs font-semibold text-purple-300">
                    <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                    <span>{t('dance.multiview.adaptiveBadge')}</span>
                    <span className="px-1.5 py-0.5 rounded bg-purple-500/20 text-[10px] text-purple-300 font-mono">
                      N = {multiViewData.detected_n}
                    </span>
                  </div>
                  <span className="text-[10px] text-gray-400">
                    {multiViewData.elapsed_ms}ms
                  </span>
                </div>
                <p className="text-[11px] text-gray-400">
                  {t('dance.multiview.hitlTooltip')}
                </p>
                <div className="grid grid-cols-3 gap-2 pt-1">
                  {multiViewData.views.map((v) => {
                    const isSelected = selectedViewIndex === v.index;
                    return (
                      <div
                        key={v.index}
                        onClick={() => setSelectedViewIndex(v.index)}
                        className={`cursor-pointer rounded-lg border overflow-hidden transition-all relative flex flex-col items-center bg-gray-950 p-1.5 ${
                          isSelected 
                            ? 'border-pink-500 ring-2 ring-pink-500/40' 
                            : 'border-gray-800 hover:border-gray-600 opacity-70 hover:opacity-100'
                        }`}
                      >
                        <div className="relative w-full aspect-[9/16] bg-black/40 rounded overflow-hidden">
                          <img
                            src={getMediaUrl(v.preview_url)}
                            alt={v.role}
                            className="w-full h-full object-contain"
                          />
                          {isSelected && (
                            <div className="absolute top-1 right-1 bg-pink-500 text-white rounded-full p-0.5 shadow">
                              <CheckCircle2 className="w-3 h-3" />
                            </div>
                          )}
                        </div>
                        <div className="mt-1.5 text-center">
                          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                            v.role === 'FRONT' 
                              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                              : v.role === 'BACK' 
                              ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                              : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                          }`}>
                            {v.role === 'FRONT' ? t('dance.multiview.frontAnchor') : v.role === 'BACK' ? t('dance.multiview.backView') : t('dance.multiview.sideView')}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Single image detected confirmation */}
            {multiViewData && !multiViewData.is_multiview && (
              <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center space-x-2 text-xs text-emerald-400">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                <span>{t('dance.multiview.singleDetected')} (N=1)</span>
              </div>
            )}

            {imagePreview && !currentTask && (
              <div className="p-3 bg-pink-500/10 border border-pink-500/30 rounded-xl flex items-center justify-between animate-fade-in">
                <div className="text-xs text-pink-300 space-y-0.5">
                  <div className="font-bold text-white flex items-center space-x-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>{t('dance.character.loaded')}</span>
                  </div>
                  <p className="text-[11px] text-gray-400">
                    {t('dance.character.templateTag', { name: selectedTemplate?.name || t('dance.templates.unknown'), duration })}
                  </p>
                </div>
                <button
                  disabled={loading}
                  onClick={handleStartGeneration}
                  className="px-4 py-2 bg-gradient-to-r from-pink-500 via-purple-600 to-indigo-600 hover:from-pink-400 hover:to-indigo-500 text-white rounded-lg text-xs font-bold shadow-md shadow-pink-500/20 active:scale-95 transition-all flex items-center space-x-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{t('dance.character.generateNow')}</span>
                </button>
              </div>
            )}

            <p className="text-[11px] text-gray-500 leading-relaxed">
              💡 {t('dance.character.antiCompressionTip')}
            </p>
          </div>

          {/* Section 3: Duration, Style & Prompt Parameters */}
          <div className="bg-gray-950 border border-gray-800/80 rounded-2xl p-5 lg:p-6 shadow-xl space-y-4">
            <div className="flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-indigo-400" />
              <h3 className="text-sm font-semibold text-gray-200">
                {t('dance.params.title')}
              </h3>
            </div>

            {/* Target Duration Selector */}
            <div>
              <label className="text-xs text-gray-400 mb-2 block font-medium">
                {t('dance.params.duration')}
              </label>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { sec: 20, label: t('dance.params.sec20') },
                  { sec: 30, label: t('dance.params.sec30') }
                ].map((item) => (
                  <button
                    key={item.sec}
                    onClick={() => setDuration(item.sec)}
                    className={`py-2 px-3 rounded-xl text-xs font-semibold transition-all flex items-center justify-center space-x-1.5 border ${
                      duration === item.sec
                        ? 'bg-gradient-to-r from-pink-500 to-purple-600 border-transparent text-white shadow-md shadow-pink-500/20'
                        : 'bg-gray-900/60 border-gray-800 text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                    }`}
                  >
                    <Clock className="w-3.5 h-3.5" />
                    <span>{item.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Aspect Ratio Selector */}
            <div>
              <label className="text-xs text-gray-400 mb-2 block font-medium">
                {t('dance.params.aspectRatio')}
              </label>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { ratio: '9:16', label: t('dance.params.ratio916'), res: '704×1280' },
                  { ratio: '16:9', label: t('dance.params.ratio169'), res: '1280×704' }
                ].map((item) => (
                  <button
                    key={item.ratio}
                    onClick={() => setAspectRatio(item.ratio)}
                    className={`py-2 px-3 rounded-xl text-xs font-semibold transition-all flex flex-col items-center justify-center space-y-0.5 border ${
                      aspectRatio === item.ratio
                        ? 'bg-gradient-to-r from-pink-500 to-purple-600 border-transparent text-white shadow-md shadow-pink-500/20'
                        : 'bg-gray-900/60 border-gray-800 text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                    }`}
                  >
                    <span>{item.label}</span>
                    <span className="text-[10px] opacity-75 font-mono">{item.res}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Style Selector */}
            <div>
              <label className="text-xs text-gray-400 mb-2 block font-medium">
                {t('dance.params.style')}
              </label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'kpop', label: t('dance.params.styles.kpop'), bpm: 128 },
                  { id: 'fitness', label: t('dance.params.styles.fitness'), bpm: 125 },
                  { id: 'street', label: t('dance.params.styles.street'), bpm: 118 },
                  { id: 'luxury', label: t('dance.params.styles.luxury'), bpm: 110 }
                ].map((st) => (
                  <button
                    key={st.id}
                    onClick={() => { setStyle(st.id); setCustomBpm(st.bpm) }}
                    className={`py-2 px-3 rounded-lg text-xs font-medium border transition-all ${
                      style === st.id
                        ? 'bg-purple-500/20 border-purple-500 text-purple-300 font-bold'
                        : 'bg-gray-900 border-gray-800 text-gray-400 hover:bg-gray-800'
                    }`}
                  >
                    {st.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Detail Prompt Override */}
            <div>
              <label className="text-xs text-gray-400 mb-1.5 block font-medium">
                {t('dance.params.promptDesc')}
              </label>
              <textarea
                rows={2}
                value={promptDesc}
                onChange={(e) => setPromptDesc(e.target.value)}
                placeholder={t('dance.params.promptPlaceholder')}
                className="w-full bg-gray-900/90 border border-gray-800 rounded-xl px-3 py-2 text-xs text-gray-200 focus:outline-none focus:border-pink-500 transition-colors placeholder:text-gray-600"
              />
            </div>

            {/* Section 4: Primary CTA Button */}
            <div className="pt-2 space-y-2">
              <button
                disabled={loading || !imageFile}
                onClick={handleStartGeneration}
                className={`w-full py-3.5 px-6 rounded-xl font-bold text-sm flex items-center justify-center space-x-2 transition-all shadow-xl ${
                  loading || !imageFile
                    ? 'bg-gray-800 text-gray-500 cursor-not-allowed border border-gray-700/50'
                    : 'bg-gradient-to-r from-pink-500 via-purple-600 to-indigo-600 hover:from-pink-400 hover:to-indigo-500 text-white shadow-pink-500/25 hover:shadow-pink-500/40 active:scale-[0.98]' 
                }`}
              >
                {loading ? (
                  <>
                    <RotateCcw className="w-4 h-4 animate-spin" />
                    <span>{t('dance.cta.generating')}</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>{t('dance.cta.generate')}</span>
                  </>
                )}
              </button>
              <p className="text-[10px] text-center text-gray-500">
                ✨ {t('dance.cta.loopClosureNote')}
              </p>
            </div>

              </div>
            </>
          )}
        </div>

        {/* ================= RIGHT: Interactive Hero Stage ================= */}
        <div className={`${studioMode === 'choreography' ? 'xl:col-span-5' : 'xl:col-span-7'} sticky top-6`}>
          <div className="bg-gray-950 border border-gray-800/80 rounded-2xl p-6 lg:p-8 shadow-2xl space-y-6">
            
            {/* Stage Header */}
            <div className="flex items-center justify-between border-b border-gray-800/60 pb-4">
              <div className="flex items-center space-x-2.5">
                <Play className="w-4 h-4 text-pink-400" />
                <h2 className="text-base font-bold text-gray-100">
                  {t('dance.stageTitle')}
                </h2>
              </div>
              
              {currentTask?.status === 'completed' && (
                <button
                  onClick={handleResetForNew}
                  className="inline-flex items-center space-x-1.5 text-xs text-gray-400 hover:text-pink-400 transition-colors"
                >
                  <RefreshCw className="w-3 h-3" />
                  <span>{t('dance.stage.recreate')}</span>
                </button>
              )}
            </div>

            {/* Sub-State A: IDLE or READY */}
            {!currentTask && (
              imagePreview ? (
                /* Ready State: Character uploaded, waiting for user generation command */
                <div className="py-10 px-6 flex flex-col items-center justify-center text-center space-y-6 border border-pink-500/30 rounded-2xl bg-gradient-to-b from-pink-500/10 via-purple-500/5 to-transparent shadow-2xl animate-fade-in">
                  <div className="inline-flex items-center space-x-2 px-3.5 py-1 bg-pink-500/20 border border-pink-500/30 text-pink-300 rounded-full text-xs font-semibold">
                    <Sparkles className="w-3.5 h-3.5 text-pink-400" />
                    <span>{t('dance.stage.readyBadge')}</span>
                  </div>

                  <div className="max-w-md space-y-2">
                    <h3 className="text-lg font-bold text-gray-100">
                      {t('dance.stage.readyTitle')}
                    </h3>
                    <p className="text-xs text-gray-400 leading-relaxed">
                      {t('dance.stage.readySubtitle')}
                    </p>
                  </div>

                  {/* Character + Selected Motion Card Preview */}
                  <div className="w-full max-w-md p-4 bg-gray-900/90 border border-gray-800 rounded-2xl flex items-center space-x-4 text-left shadow-lg">
                    <div className="w-20 h-28 rounded-xl overflow-hidden border border-gray-700 flex-shrink-0 bg-black shadow-md">
                      <img src={imagePreview} alt="Ready Character" className="w-full h-full object-cover object-top" />
                    </div>
                    <div className="space-y-1.5 text-xs text-gray-300 flex-1 min-w-0">
                      <p className="font-bold text-white text-sm truncate">
                        {t('dance.stage.readyTemplate', { name: selectedTemplate?.name || t('dance.templates.tabs.all') })}
                      </p>
                      <p className="text-gray-400">
                        {t('dance.stage.readyDuration', { duration })} · {t(`dance.params.styles.${style}`)} · {customBpm} BPM
                      </p>
                      <div className="flex items-center space-x-1.5 text-[11px] text-emerald-400 font-medium pt-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>{t('dance.character.antiCompressionMounted')}</span>
                      </div>
                    </div>
                  </div>

                  {/* High-Visibility Generation CTA on the Stage */}
                  <div className="w-full max-w-md space-y-2">
                    <button
                      disabled={loading}
                      onClick={handleStartGeneration}
                      className="w-full py-4 px-6 rounded-xl font-bold text-sm flex items-center justify-center space-x-2.5 transition-all shadow-xl bg-gradient-to-r from-pink-500 via-purple-600 to-indigo-600 hover:from-pink-400 hover:to-indigo-500 text-white shadow-pink-500/25 hover:shadow-pink-500/40 active:scale-[0.98]"
                    >
                      <Sparkles className="w-4 h-4" />
                      <span>{t('dance.stage.startNow')}</span>
                    </button>
                    <p className="text-[10px] text-gray-500 text-center">
                      {t('dance.character.loopSubtitle')}
                    </p>
                  </div>
                </div>
              ) : (
                /* V2.0 Masterpiece Showcase & Idle Stage */
                <div className="space-y-4 animate-fade-in">
                  <div className="flex items-center justify-between pb-3 border-b border-gray-800/80">
                    <div className="flex items-center space-x-2">
                      <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse" />
                      <span className="text-xs font-bold text-white tracking-wide">
                        {t('dance.stage.showcase.title')}
                      </span>
                    </div>
                    <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-pink-500/10 text-pink-300 border border-pink-500/30">
                      {t('dance.stage.showcase.tag')}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-12 gap-5 items-start">
                    {/* Left: Video Player (20s V2.0 Output) */}
                    <div className="md:col-span-6 bg-black rounded-2xl overflow-hidden border border-gray-800 shadow-2xl relative group">
                      <div className="aspect-[9/16] w-full max-h-[480px] flex items-center justify-center bg-black">
                        <video
                          src={getMediaUrl('/media/out/test_v2_consistent_clarity_20s/dance_20s.mp4')}
                          poster={getMediaUrl('/media/out/test_v2_consistent_clarity_20s/poster.jpg')}
                          className="w-full h-full object-contain"
                          autoPlay
                          loop
                          muted
                          playsInline
                          controls
                        />
                      </div>
                      <div className="absolute top-3 left-3 px-2.5 py-1 rounded-lg bg-black/75 backdrop-blur-md border border-white/10 text-[11px] text-pink-300 font-semibold flex items-center space-x-1.5 pointer-events-none shadow-md">
                        <Flame className="w-3.5 h-3.5 text-pink-400 animate-bounce" />
                        <span>{t('dance.stage.showcase.videoBadge')}</span>
                      </div>
                    </div>

                    {/* Right: Meta & Interactive CTA */}
                    <div className="md:col-span-6 space-y-3.5">
                      {/* Original Reference vs V2.0 Comparison Card */}
                      <div className="p-4 bg-gray-900/60 border border-gray-800/80 rounded-2xl space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-gray-200">
                            {t('dance.stage.showcase.comparisonTitle')}
                          </span>
                          <span className="text-[10px] text-emerald-400 font-medium">
                            {t('dance.stage.showcase.auditPassed')}
                          </span>
                        </div>
                        
                        <div className="flex items-center space-x-3 p-2.5 bg-gray-950/80 rounded-xl border border-gray-800">
                          <img
                            src={getMediaUrl('/media/out/test_v2_consistent_clarity_20s/ref_character.png')}
                            alt="Reference"
                            className="w-14 h-20 object-cover object-top rounded-lg border border-pink-500/30 flex-shrink-0"
                          />
                          <div className="text-[11px] space-y-1 text-gray-300 flex-1">
                            <p className="font-semibold text-white">{t('dance.stage.showcase.curvyModel')}</p>
                            <p className="text-[10px] text-gray-400 leading-relaxed">{t('dance.stage.showcase.curvyModelDesc')}</p>
                          </div>
                        </div>

                        {/* 4 Feature Highlights */}
                        <div className="space-y-1.5 pt-1 text-xs">
                          {[
                            { title: t('dance.stage.features.loop'), desc: t('dance.character.featureLoopDesc') },
                            { title: t('dance.stage.features.proportions'), desc: t('dance.character.featureProportionsDesc') },
                            { title: t('dance.stage.features.bpm'), desc: t('dance.character.featureBpmDesc') },
                            { title: t('dance.stage.features.quality'), desc: t('dance.character.featureQualityDesc') }
                          ].map((feat, idx) => (
                            <div key={idx} className="flex items-center space-x-2 text-[11px] text-gray-300">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                              <span className="text-gray-200 font-medium">{feat.title}：</span>
                              <span className="text-gray-400">{feat.desc}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* CTA to Upload Own Character */}
                      <div className="p-4 bg-gradient-to-br from-pink-500/10 via-purple-500/10 to-indigo-500/10 border border-pink-500/30 rounded-2xl space-y-2.5">
                        <div className="space-y-1">
                          <h4 className="text-xs font-bold text-white flex items-center space-x-1.5">
                            <Sparkles className="w-3.5 h-3.5 text-pink-400" />
                            <span>{t('dance.stage.showcase.tryYourOwn')}</span>
                          </h4>
                          <p className="text-[11px] text-gray-400 leading-relaxed">
                            {t('dance.stage.showcase.tryYourOwnDesc')}
                          </p>
                        </div>

                        <button
                          onClick={() => fileInputRef.current?.click()}
                          className="w-full py-2.5 px-4 rounded-xl font-bold text-xs flex items-center justify-center space-x-2 transition-all shadow-lg bg-gradient-to-r from-pink-500 via-purple-600 to-indigo-600 hover:from-pink-400 hover:to-indigo-500 text-white shadow-pink-500/25 active:scale-[0.98]"
                        >
                          <UploadCloud className="w-4 h-4" />
                          <span>{t('dance.stage.showcase.uploadBtn')}</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )
            )}

            {/* Sub-State B: PROCESSING (Multi-shot pipeline in progress) */}
            {currentTask && currentTask.status !== 'completed' && (
              <div className="space-y-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {currentTask.status === 'failed' ? (
                      <AlertCircle className="w-5 h-5 text-red-400" />
                    ) : (
                      <div className="w-5 h-5 border-2 border-pink-400 border-t-transparent rounded-full animate-spin" />
                    )}
                    <div>
                      <h3 className="text-sm font-semibold text-gray-200">
                        {currentTask.status === 'failed' ? t('dance.character.taskInterrupted') : t('dance.stage.renderingTitle')}
                      </h3>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {currentTask.message || t('dance.stage.renderingStep')}
                      </p>
                    </div>
                  </div>
                  <span className="text-lg font-mono text-pink-400 font-bold">
                    {currentTask.progress}%
                  </span>
                </div>

                {/* Smooth Progress Bar */}
                <div className="w-full bg-gray-900 rounded-full h-2.5 overflow-hidden border border-gray-800">
                  <div 
                    className="bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 h-full transition-all duration-500" 
                    style={{ width: `${currentTask.progress}%` }} 
                  />
                </div>

                {/* Pipeline Step Matrix Visualizer */}
                <div className="grid grid-cols-6 gap-2 pt-2">
                  {[
                    { id: 1, label: t('dance.stage.pipeline.shot1'), threshold: 25 },
                    { id: 2, label: t('dance.stage.pipeline.shot2'), threshold: 50 },
                    { id: 3, label: t('dance.stage.pipeline.shot3'), threshold: 70 },
                    { id: 4, label: t('dance.stage.pipeline.shot4'), threshold: 85 },
                    { id: 5, label: t('dance.stage.pipeline.bgm'), threshold: 92 },
                    { id: 6, label: t('dance.stage.pipeline.mux'), threshold: 98 }
                  ].map((node) => {
                    const isPassed = currentTask.progress >= node.threshold
                    const isCurrent = currentTask.progress >= (node.threshold - 20) && currentTask.progress < node.threshold
                    return (
                      <div 
                        key={node.id}
                        className={`p-2.5 rounded-xl border text-center transition-all ${
                          isPassed 
                            ? 'bg-pink-500/10 border-pink-500/40 text-pink-300' 
                            : isCurrent 
                            ? 'bg-purple-500/20 border-purple-500 text-purple-200 animate-pulse'
                            : 'bg-gray-900/40 border-gray-800 text-gray-500'
                        }`}
                      >
                        <div className="text-[10px] font-mono">0{node.id}</div>
                        <div className="text-[11px] font-semibold truncate mt-0.5">{node.label}</div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Sub-State C: COMPLETED (Hero Video Player & Spec Dashboard) */}
            {currentTask && currentTask.status === 'completed' && currentTask.video_url && (
              <div className="space-y-6 animate-fade-in">
                
                {/* Completed Badge & Dynamic Title */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-emerald-950/30 border border-emerald-500/30 rounded-2xl">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                      <CheckCircle2 className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-gray-100">
                        {t('dance.stage.completedTitle')}
                      </h3>
                      {/* CRITICAL FIX: Dynamic duration binding instead of hardcoded 30s */}
                      <p className="text-xs text-emerald-400/90 font-medium">
                        {t('dance.stage.videoTitle', { duration: displayDuration })}
                      </p>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    {currentTask.jianying_draft_zip && (
                      <a
                        href={getMediaUrl(currentTask.jianying_draft_zip)}
                        download
                        className="inline-flex items-center justify-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-purple-500/20 transition-all active:scale-[0.98]"
                      >
                        <Film className="w-4 h-4 text-purple-200" />
                        <span>{t('dance.draftOutput.downloadZip')}</span>
                      </a>
                    )}

                    <a
                      href={getMediaUrl(currentTask.video_url)}
                      download
                      className="inline-flex items-center justify-center space-x-2 px-5 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-500/20 transition-all active:scale-[0.98]"
                    >
                      <Download className="w-4 h-4" />
                      <span>{t('dance.stage.download')}</span>
                    </a>
                  </div>
                </div>

                {/* Hero Showcase: Video Player + Technical Metas */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
                  
                  {/* Left Player Column */}
                  <div className="md:col-span-7 flex justify-center">
                    <div className="w-full max-w-[340px] aspect-[9/16] bg-black rounded-2xl overflow-hidden shadow-2xl border border-gray-800/80 ring-1 ring-pink-500/20">
                      <video 
                        src={getMediaUrl(currentTask.video_url)} 
                        controls 
                        autoPlay 
                        loop 
                        className="w-full h-full object-contain bg-black" 
                      />
                    </div>
                  </div>

                  {/* Right Meta Specifications */}
                  <div className="md:col-span-5 space-y-4">
                    <div className="p-4 bg-gray-900/60 border border-gray-800/80 rounded-xl space-y-2.5 text-xs text-gray-300">
                      <div className="font-semibold text-gray-200 border-b border-gray-800 pb-2">
                        {t('dance.character.productionSpecs')}
                      </div>
                      <div className="space-y-1.5 text-gray-400">
                        <p>• {t('dance.stage.meta.codec')}</p>
                        <p>• {t('dance.stage.meta.audio')}</p>
                        <p>• {t('dance.stage.meta.loopFeature')}</p>
                        <p>• {t('dance.stage.meta.template', { 
                          name: selectedTemplate?.name || t('dance.templates.unknown'), 
                          bpm: customBpm 
                        })}</p>
                        <p>• {t('dance.stage.meta.style', { 
                          style: t(`dance.params.styles.${style}`) 
                        })}</p>
                        {currentTask.jianying_draft_zip && (
                          <p className="text-purple-300 font-medium">
                            {t('dance.draftOutput.draftDesc')}
                          </p>
                        )}
                        {currentTask.jianying_synced && (
                          <p className="text-emerald-400 font-medium">
                            {t('dance.draftOutput.synced')}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="p-4 bg-pink-500/5 border border-pink-500/20 rounded-xl space-y-1 text-xs text-pink-300">
                      <span className="font-semibold flex items-center space-x-1.5">
                        <Zap className="w-3.5 h-3.5" />
                        <span>{t('dance.character.seamlessLoop')}</span>
                      </span>
                      <p className="text-[11px] text-pink-400/80 leading-relaxed">
                        {t('dance.character.seamlessLoopDesc')}
                      </p>
                    </div>

                    <button
                      onClick={handleResetForNew}
                      className="w-full py-2.5 px-4 bg-gray-900 hover:bg-gray-800 text-gray-300 rounded-xl text-xs font-semibold border border-gray-800 transition-all flex items-center justify-center space-x-2"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      <span>{t('dance.stage.recreate')}</span>
                    </button>
                  </div>

                </div>

              </div>
            )}

          </div>
        </div>

      </div>
    </div>
  )
}
