import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { 
  UploadCloud, Sparkles, Music, Flame, CheckCircle2, 
  AlertCircle, Download, RotateCcw, Clock, Layers, Sliders
} from 'lucide-react'

interface DanceTemplate {
  dance_id: string
  name: string
  bpm: string
  duration_range: number[]
  tags: string[]
  stats?: { views?: string; difficulty?: number; virality?: number }
  timeline?: Array<{ time: string; name: string; action_prompt: string; expression?: string }>
}

interface TaskStatus {
  task_id: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  progress: number
  message: string
  video_url?: string
}

export default function DanceStudio() {
  const [templates, setTemplates] = useState<DanceTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<DanceTemplate | null>(null)
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [duration, setDuration] = useState<number>(20)
  const [style, setStyle] = useState<string>('kpop')
  const [promptDesc, setPromptDesc] = useState<string>('')
  const [customBpm, setCustomBpm] = useState<number>(128)
  const [loading, setLoading] = useState<boolean>(false)
  const [currentTask, setCurrentTask] = useState<TaskStatus | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    fetchTemplates()
  }, [])

  const fetchTemplates = async () => {
    try {
      const res = await axios.get('http://localhost:8008/api/dance/templates')
      setTemplates(res.data)
      if (res.data.length > 0) {
        setSelectedTemplate(res.data[0])
      }
    } catch (err) {
      console.error('Failed to fetch dance templates', err)
    }
  }

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      setImageFile(file)
      setImagePreview(URL.createObjectURL(file))
      setErrorMsg(null)
    }
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      setImageFile(file)
      setImagePreview(URL.createObjectURL(file))
      setErrorMsg(null)
    }
  }

  const handleStartGeneration = async () => {
    if (!imageFile) {
      setErrorMsg('请先上传一张全身模特或人物立绘参考图')
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
      if (selectedTemplate) {
        formData.append('template_id', selectedTemplate.dance_id)
      }
      if (promptDesc.trim()) {
        formData.append('prompt_desc', promptDesc.trim())
      }

      const res = await axios.post('http://localhost:8008/api/dance/generate', formData)
      const taskId = res.data.task_id
      pollTaskStatus(taskId)
    } catch (err: any) {
      setLoading(false)
      setErrorMsg(err?.response?.data?.detail || '任务提交失败，请检查网络和服务状态')
    }
  }

  const pollTaskStatus = (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`http://localhost:8008/api/dance/tasks/${taskId}`)
        const taskData = res.data
        setCurrentTask(taskData)

        if (taskData.status === 'completed') {
          clearInterval(interval)
          setLoading(false)
        } else if (taskData.status === 'failed') {
          clearInterval(interval)
          setLoading(false)
          setErrorMsg(taskData.message || '生成失败')
        }
      } catch (err) {
        console.error('Polling error', err)
      }
    }, 4000)
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-800 pb-6">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-gradient-to-tr from-pink-500/20 to-purple-500/20 border border-pink-500/30 rounded-xl">
              <Flame className="w-6 h-6 text-pink-400 animate-pulse" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-pink-400 via-purple-300 to-indigo-400 bg-clip-text text-transparent">
                AI Dance Studio 舞蹈工坊
              </h1>
              <p className="text-sm text-gray-400 mt-0.5">
                单图生成 20-30s 无缝循环舞蹈 · 12 款爆款热舞模版 · BPM 节拍音乐卡点 · 9头身高挑身材防压缩
              </p>
            </div>
          </div>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 bg-red-950/40 border border-red-500/30 rounded-2xl flex items-center space-x-3 text-red-400 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Image Upload & Config */}
        <div className="lg:col-span-4 space-y-6">
          {/* Image Upload Area */}
          <div className="bg-gray-950 border border-gray-800/80 rounded-2xl p-6 shadow-xl">
            <label className="block text-sm font-semibold text-gray-200 mb-3 flex items-center justify-between">
              <span>1. 人物参考图像 (9:16 全身立绘)</span>
              {imagePreview && (
                <button 
                  onClick={() => { setImageFile(null); setImagePreview(null) }}
                  className="text-xs text-gray-400 hover:text-red-400 transition-colors"
                >
                  重新选择
                </button>
              )}
            </label>

            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`relative border-2 border-dashed rounded-xl transition-all cursor-pointer overflow-hidden flex flex-col items-center justify-center ${
                imagePreview 
                  ? 'border-gray-700 bg-gray-900/50 aspect-[9/16] max-h-[420px]' 
                  : 'border-gray-700/80 hover:border-pink-500/50 bg-gray-900/30 py-16 hover:bg-gray-900/50'
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
                <img 
                  src={imagePreview} 
                  alt="Preview" 
                  className="w-full h-full object-contain" 
                />
              ) : (
                <div className="text-center px-4 space-y-3">
                  <div className="w-12 h-12 rounded-full bg-pink-500/10 border border-pink-500/20 flex items-center justify-center mx-auto text-pink-400">
                    <UploadCloud className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-200">点击或拖拽上传人物图</p>
                    <p className="text-xs text-gray-500 mt-1">推荐 9:16 比例、清晰全身立绘</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Duration & Style Parameters */}
          <div className="bg-gray-950 border border-gray-800/80 rounded-2xl p-6 shadow-xl space-y-5">
            <h3 className="text-sm font-semibold text-gray-200 flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-purple-400" />
              <span>2. 生成参数设置</span>
            </h3>

            {/* Duration Selector */}
            <div>
              <label className="text-xs text-gray-400 mb-2 block">视频目标时长</label>
              <div className="grid grid-cols-2 gap-3">
                {[20, 30].map((sec) => (
                  <button
                    key={sec}
                    onClick={() => setDuration(sec)}
                    className={`py-2.5 px-4 rounded-xl text-sm font-semibold transition-all flex items-center justify-center space-x-2 border ${
                      duration === sec
                        ? 'bg-gradient-to-r from-pink-500 to-purple-600 border-transparent text-white shadow-lg shadow-pink-500/20'
                        : 'bg-gray-900/60 border-gray-800 text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                    }`}
                  >
                    <Clock className="w-4 h-4" />
                    <span>{sec} 秒 ({sec === 20 ? '4 段' : '6 段'})</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Style Selector */}
            <div>
              <label className="text-xs text-gray-400 mb-2 block">风格分类</label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'kpop', label: 'K-pop 女团', bpm: 128 },
                  { id: 'fitness', label: '健身活力', bpm: 125 },
                  { id: 'street', label: '街头律动', bpm: 118 },
                  { id: 'luxury', label: '优雅慢摇', bpm: 110 }
                ].map((st) => (
                  <button
                    key={st.id}
                    onClick={() => { setStyle(st.id); setCustomBpm(st.bpm) }}
                    className={`py-2 px-3 rounded-lg text-xs font-medium border transition-all ${
                      style === st.id
                        ? 'bg-purple-500/20 border-purple-500 text-purple-300'
                        : 'bg-gray-900 border-gray-800 text-gray-400 hover:bg-gray-800'
                    }`}
                  >
                    {st.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Optional Prompt Refinement */}
            <div>
              <label className="text-xs text-gray-400 mb-1.5 block">细节特征微调 (可选)</label>
              <textarea
                rows={2}
                value={promptDesc}
                onChange={(e) => setPromptDesc(e.target.value)}
                placeholder="例如：留着微卷长发，白色短裙，黑色高跟长靴，纯黑影棚背景..."
                className="w-full bg-gray-900/90 border border-gray-800 rounded-xl px-3 py-2 text-xs text-gray-200 focus:outline-none focus:border-pink-500 transition-colors placeholder:text-gray-600"
              />
            </div>

            {/* Action Trigger */}
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
                  <span>正在调度 AI 渲染管线...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>一键生成 100% 闭环循环舞蹈</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Middle & Right Column: Template Library & Generation Monitor */}
        <div className="lg:col-span-8 space-y-6">
          {/* Real-time Status Box if Task Active */}
          {currentTask && (
            <div className="bg-gray-950 border border-gray-800 rounded-2xl p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {currentTask.status === 'completed' ? (
                    <CheckCircle2 className="w-5 h-5 text-green-400" />
                  ) : currentTask.status === 'failed' ? (
                    <AlertCircle className="w-5 h-5 text-red-400" />
                  ) : (
                    <div className="w-4 h-4 border-2 border-pink-400 border-t-transparent rounded-full animate-spin" />
                  )}
                  <span className="text-sm font-semibold text-gray-200">
                    {currentTask.status === 'completed' ? '渲染质检已通过 · 成品就绪' : 'AI 舞蹈多镜头渲染中...'}
                  </span>
                </div>
                <span className="text-xs font-mono text-pink-400 font-bold">{currentTask.progress}%</span>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-gray-900 rounded-full h-2 overflow-hidden border border-gray-800">
                <div 
                  className="bg-gradient-to-r from-pink-500 to-purple-500 h-full transition-all duration-500" 
                  style={{ width: `${currentTask.progress}%` }} 
                />
              </div>

              <p className="text-xs text-gray-400 font-mono">{currentTask.message}</p>

              {/* Video Player if Completed */}
              {currentTask.status === 'completed' && currentTask.video_url && (
                <div className="mt-4 pt-4 border-t border-gray-800 flex flex-col md:flex-row gap-6 items-center">
                  <div className="w-full md:w-64 aspect-[9/16] bg-black rounded-xl overflow-hidden shadow-2xl border border-gray-800">
                    <video 
                      src={`http://localhost:8008${currentTask.video_url}`} 
                      controls 
                      autoPlay 
                      loop 
                      className="w-full h-full object-cover" 
                    />
                  </div>
                  <div className="flex-1 space-y-3">
                    <h4 className="text-base font-bold text-gray-100">30s 广播级无缝循环成片</h4>
                    <ul className="text-xs text-gray-400 space-y-1">
                      <li>• 编码标准：H.264 / yuv420p (704x1280 竖屏)</li>
                      <li>• 音频配置：AAC 44.1kHz 多声部卡点舞曲</li>
                      <li>• 闭环特性：首尾姿态 100% 确定性收敛无跳帧</li>
                    </ul>
                    <div className="pt-2">
                      <a
                        href={`http://localhost:8008${currentTask.video_url}`}
                        download
                        className="inline-flex items-center space-x-2 px-5 py-2.5 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-green-500/20 transition-all"
                      >
                        <Download className="w-4 h-4" />
                        <span>下载 MP4 舞蹈视频</span>
                      </a>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Template Gallery */}
          <div className="bg-gray-950 border border-gray-800/80 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-gray-200 flex items-center space-x-2">
                <Layers className="w-4 h-4 text-pink-400" />
                <span>3. 选择爆款舞蹈动作模板 ({templates.length} 款)</span>
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[640px] overflow-y-auto pr-1">
              {templates.map((tpl) => {
                const isSelected = selectedTemplate?.dance_id === tpl.dance_id
                return (
                  <div
                    key={tpl.dance_id}
                    onClick={() => {
                      setSelectedTemplate(tpl)
                      if (tpl.bpm) {
                        const b = parseInt(tpl.bpm.split('-')[0]) || 128
                        setCustomBpm(b)
                      }
                    }}
                    className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col justify-between space-y-3 ${
                      isSelected
                        ? 'bg-pink-500/10 border-pink-500 shadow-md shadow-pink-500/10'
                        : 'bg-gray-900/60 border-gray-800/80 hover:bg-gray-900 hover:border-gray-700'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <h4 className="font-bold text-sm text-gray-100 flex items-center space-x-1.5">
                          <span>{tpl.name}</span>
                        </h4>
                        <span className="px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 text-[10px] font-mono font-bold flex items-center space-x-1">
                          <Music className="w-3 h-3" />
                          <span>{tpl.bpm} BPM</span>
                        </span>
                      </div>
                      
                      <div className="flex flex-wrap gap-1 mt-2">
                        {tpl.tags.slice(0, 3).map((tag, idx) => (
                          <span key={idx} className="px-1.5 py-0.5 rounded bg-gray-800 text-gray-400 text-[10px]">
                            #{tag}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="pt-2 border-t border-gray-800/60 flex items-center justify-between text-[11px] text-gray-500">
                      <span>热度: {tpl.stats?.views || '爆款'}</span>
                      <span className="text-pink-400/80 font-medium">{isSelected ? '✓ 已选中' : '选择'}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
