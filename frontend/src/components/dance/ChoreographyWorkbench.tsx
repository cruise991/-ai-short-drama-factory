import React, { useState, useEffect, useMemo } from 'react'
import { 
  Sparkles, Plus, Trash2, ArrowUp, ArrowDown, Share2, 
  Film, Check, Copy, Sliders, Music, Eye, Compass, Zap
} from 'lucide-react'
import { 
  danceApi, 
  type PoseItem, 
  type PoseCategory, 
  type PoseAngle, 
  type PoseSlot,
  type ChoreographyRecipe
} from '../../api/dance'
import { useTranslation } from '../../locales/i18n'

interface ChoreographyWorkbenchProps {
  imageFile: File | null
  imagePreview: string | null
  onStartChoreograph: (sequence: PoseSlot[], bpm: number, style: string, enableJianying: boolean) => void
  loading: boolean
}

export const ChoreographyWorkbench: React.FC<ChoreographyWorkbenchProps> = ({
  imageFile,
  imagePreview,
  onStartChoreograph,
  loading
}) => {
  const { t } = useTranslation()
  const [categories, setCategories] = useState<PoseCategory[]>([])
  const [angles, setAngles] = useState<PoseAngle[]>([])
  const [poses, setPoses] = useState<PoseItem[]>([])
  const [activeCategory, setActiveCategory] = useState<string>('all')
  const [activeAngleFilter, setActiveAngleFilter] = useState<string>('all')
  const [searchKeyword, setSearchKeyword] = useState<string>('')
  const [bpm, setBpm] = useState<number>(128)
  const [style, setStyle] = useState<string>('kpop')
  const [recipeTitle, setRecipeTitle] = useState<string>(t('dance.choreo.defaultRecipeTitle'))
  const [enableJianying, setEnableJianying] = useState<boolean>(true)
  
  // 自由编舞时间轴槽位列表
  const [timeline, setTimeline] = useState<PoseSlot[]>([])
  
  // 3:4 配方卡弹窗与分享状态
  const [showShareModal, setShowShareModal] = useState<boolean>(false)
  const [shareData, setShareData] = useState<any>(null)
  const [copied, setCopied] = useState<boolean>(false)
  const [importRecipeId, setImportRecipeId] = useState<string>('')
  const [importMsg, setImportMsg] = useState<string | null>(null)

  // 1. 加载动作知识库并检查 URL 参数是否有分享的 recipe_id
  useEffect(() => {
    loadGalleryAndCheckUrl()
  }, [])

  const loadGalleryAndCheckUrl = async () => {
    try {
      const res = await danceApi.getPoseGallery()
      if (res) {
        setCategories(res.categories || [])
        setAngles(res.angles || [])
        const allPoses = res.poses || []
        setPoses(allPoses)

        // 检查 URL 是否携带分享配方 ID
        const params = new URLSearchParams(window.location.search)
        const sharedRecipeId = params.get('recipe_id')

        if (sharedRecipeId) {
          await handleImportRecipeById(sharedRecipeId, allPoses, true)
        } else if (allPoses.length >= 4) {
          // 初始自动填充一套 4 段式经典黄金编舞示例 (起承转合)
          const intro = allPoses.find(p => p.category === 'intro') || allPoses[0]
          const rhythm1 = allPoses.find(p => p.category === 'rhythm') || allPoses[1]
          const trans = allPoses.find(p => p.category === 'transition') || allPoses[2]
          const ending = allPoses.find(p => p.category === 'ending') || allPoses[3]
          
          setTimeline([
            createSlot(intro, 'oblique', 4, 2.0),
            createSlot(rhythm1, 'front', 4, 2.0),
            createSlot(trans, 'oblique', 4, 2.0),
            createSlot(ending, 'low', 4, 2.0)
          ])
        }
      }
    } catch (err) {
      console.error('Failed to load pose gallery:', err)
    }
  }

  const createSlot = (pose: PoseItem, angle: string, beats: number = 4, seconds: number = 2.0): PoseSlot => {
    return {
      slot_id: `slot_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
      pose_id: pose.id,
      name: pose.name,
      category: pose.category,
      angle: angle || pose.default_angle || 'front',
      beats: beats,
      seconds: seconds,
      dynamic_prompt: pose.dynamic_prompt,
      tags: pose.tags,
      preview_urls: pose.preview_urls
    }
  }

  // 过滤后的动作知识库
  const filteredPoses = useMemo(() => {
    return poses.filter(p => {
      if (activeCategory !== 'all' && p.category !== activeCategory) return false
      if (activeAngleFilter !== 'all' && !(p.available_angles || []).includes(activeAngleFilter)) return false
      if (searchKeyword.trim()) {
        const kw = searchKeyword.toLowerCase()
        const matchName = p.name.toLowerCase().includes(kw)
        const matchTag = (p.tags || []).some(t => t.toLowerCase().includes(kw))
        const matchPrompt = (p.dynamic_prompt || '').toLowerCase().includes(kw)
        if (!matchName && !matchTag && !matchPrompt) return false
      }
      return true
    })
  }, [poses, activeCategory, activeAngleFilter, searchKeyword])

  // 添加动作到时间轴
  const handleAddPose = (pose: PoseItem) => {
    const newSlot = createSlot(pose, pose.default_angle || 'oblique', pose.recommended_beats || 4, pose.recommended_seconds || 2.0)
    setTimeline(prev => [...prev, newSlot])
  }

  // 删除槽位
  const handleRemoveSlot = (slotId: string) => {
    setTimeline(prev => prev.filter(s => s.slot_id !== slotId))
  }

  // 上移/下移槽位
  const handleMoveSlot = (index: number, direction: 'up' | 'down') => {
    const newTimeline = [...timeline]
    const targetIdx = direction === 'up' ? index - 1 : index + 1
    if (targetIdx < 0 || targetIdx >= newTimeline.length) return
    const temp = newTimeline[index]
    newTimeline[index] = newTimeline[targetIdx]
    newTimeline[targetIdx] = temp
    setTimeline(newTimeline)
  }

  // 修改槽位视角
  const handleChangeAngle = (slotId: string, newAngle: string) => {
    setTimeline(prev => prev.map(s => s.slot_id === slotId ? { ...s, angle: newAngle } : s))
  }

  // 修改槽位节拍数
  const handleChangeBeats = (slotId: string, newBeats: number) => {
    const clampedBeats = Math.max(2, Math.min(16, newBeats))
    const sec = (clampedBeats / (bpm / 60)).toFixed(1)
    setTimeline(prev => prev.map(s => s.slot_id === slotId ? { ...s, beats: clampedBeats, seconds: parseFloat(sec) } : s))
  }

  // 计算总时长和总拍数
  const totalBeats = useMemo(() => timeline.reduce((acc, cur) => acc + cur.beats, 0), [timeline])
  const totalSeconds = useMemo(() => timeline.reduce((acc, cur) => acc + cur.seconds, 0), [timeline])

  // 保存配方挑战卡
  const handleSaveRecipe = async () => {
    if (timeline.length === 0) return
    try {
      const recipeData: ChoreographyRecipe = {
        title: recipeTitle,
        creator: 'AI 独立编舞师',
        style: style,
        bpm: bpm,
        sequence: timeline
      }
      const res = await danceApi.saveRecipe(recipeData)
      setShareData(res)
      setShowShareModal(true)
    } catch (err) {
      console.error('Failed to save recipe:', err)
    }
  }

  // 一键同款导入逻辑 (支持外部直接传入 ID 与 poses 库以实现自动回填)
  const handleImportRecipeById = async (rawId: string, customPoses?: PoseItem[], isAutoFromUrl = false) => {
    if (!rawId.trim()) return
    setImportMsg(null)
    const poseCatalog = customPoses || poses
    try {
      const cleanId = rawId.trim().replace(/^rec_/, '')
      const fullId = `rec_${cleanId}`
      const recipe = await danceApi.getRecipe(fullId)
      if (recipe && recipe.sequence) {
        // 补全 slot_id 与 preview_urls 防止缩略图丢失或 React Key 碰撞
        const enriched = recipe.sequence.map((item: any, idx: number) => {
          const pDef = poseCatalog.find(p => p.id === item.pose_id)
          return {
            slot_id: item.slot_id || `slot_imported_${Date.now()}_${idx}`,
            pose_id: item.pose_id,
            name: item.name || pDef?.name || `Pose ${idx + 1}`,
            category: item.category || pDef?.category || 'intro',
            angle: item.angle || 'front',
            beats: item.beats || 4,
            seconds: item.seconds || 2.0,
            dynamic_prompt: item.dynamic_prompt || pDef?.dynamic_prompt || '',
            tags: item.tags || pDef?.tags || [],
            preview_urls: item.preview_urls || pDef?.preview_urls || {}
          }
        })
        setTimeline(enriched)
        if (recipe.bpm) setBpm(recipe.bpm)
        if (recipe.style) setStyle(recipe.style)
        if (recipe.title) setRecipeTitle(recipe.title)
        
        const successMsg = isAutoFromUrl 
          ? t('dance.choreo.sharedLoaded', { title: recipe.title })
          : t('dance.choreo.importSuccess', { title: recipe.title })
        setImportMsg(successMsg)
        setTimeout(() => setImportMsg(null), 4500)
      }
    } catch (e) {
      setImportMsg(t('dance.choreo.importFailed'))
    }
  }

  const handleImportRecipe = async () => {
    let targetId = importRecipeId.trim()
    if (!targetId) {
      const domInput = document.querySelector<HTMLInputElement>('input[placeholder*="rec_"]')
      if (domInput && domInput.value.trim()) {
        targetId = domInput.value.trim()
      }
    }
    if (!targetId) return
    await handleImportRecipeById(targetId)
  }

  // 复制分享链接
  const handleCopyLink = () => {
    if (!shareData) return
    const url = `${window.location.origin}${shareData.share_url}`
    navigator.clipboard.writeText(`🔥 来挑战我的自由编舞配方【${shareData.title}】！${shareData.pose_count} 个神仙动作卡点，BPM ${shareData.bpm}。链接：${url}`)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-6">
      
      {/* 顶部一键同款配方导入条 */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 bg-gradient-to-r from-purple-950/40 via-indigo-950/30 to-gray-900/40 border border-purple-500/20 rounded-2xl">
        <div className="flex items-center space-x-2 text-xs text-purple-300">
          <Compass className="w-4 h-4 text-purple-400" />
          <span className="font-semibold">{t('dance.choreo.recipeImport')}</span>
          <span className="text-gray-400">{t('dance.choreo.recipeImportSub')}</span>
        </div>
        <div className="flex items-center space-x-2">
          <input 
            id="recipe-import-input"
            name="recipe-import-input"
            type="text" 
            placeholder={t('dance.choreo.recipePlaceholder')} 
            value={importRecipeId}
            onChange={(e) => setImportRecipeId(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleImportRecipe() }}
            className="px-3 py-1.5 bg-gray-900 border border-purple-500/30 rounded-xl text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-400 w-36 sm:w-44"
          />
          <button 
            id="btn-clone-recipe"
            onClick={handleImportRecipe}
            className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-bold transition-all shadow-md active:scale-95"
          >
            {t('dance.choreo.btnImport')}
          </button>
        </div>
      </div>
      {importMsg && (
        <div id="recipe-import-msg" className="text-xs text-center font-medium py-1 px-3 bg-purple-500/10 text-purple-300 rounded-lg border border-purple-500/20 animate-fade-in">
          {importMsg}
        </div>
      )}

      {/* 主工作区分割：左侧动作库抽屉 + 右侧自由编舞时间轴 */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* ================= 左侧：动作知识库 (5 视角 × 4 体系) ================= */}
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-gray-950/70 border border-gray-800 rounded-2xl p-4 space-y-4 shadow-xl">
            
            {/* 库标题与搜索 */}
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center space-x-2">
                <div className="w-2.5 h-2.5 rounded-full bg-pink-500 animate-pulse" />
                <h3 className="text-sm font-bold text-gray-200">{t('dance.choreo.galleryTitle')}</h3>
                <span className="text-[11px] text-gray-500 font-mono">({filteredPoses.length}/{poses.length})</span>
              </div>
              <input 
                id="search-pose-input"
                name="search-pose-input"
                type="text" 
                placeholder={t('dance.choreo.searchPlaceholder')} 
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="px-3 py-1.5 bg-gray-900 border border-gray-800 rounded-xl text-xs text-gray-300 placeholder-gray-500 focus:outline-none focus:border-pink-500 w-40"
              />
            </div>

            {/* 4 大体系分类标签 */}
            <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 scrollbar-none">
              <button 
                onClick={() => setActiveCategory('all')}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                  activeCategory === 'all' 
                    ? 'bg-gradient-to-r from-pink-500 to-purple-600 text-white shadow-md' 
                    : 'bg-gray-900 text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                }`}
              >
                {t('dance.choreo.allCategories')}
              </button>
              {categories.filter(c => c.id !== 'all').map(cat => (
                <button 
                  key={cat.id}
                  onClick={() => setActiveCategory(cat.id)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                    activeCategory === cat.id 
                      ? 'bg-gradient-to-r from-pink-500 to-purple-600 text-white shadow-md' 
                      : 'bg-gray-900 text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                  }`}
                >
                  {t(`dance.choreo.stages.${cat.id}`, cat.name)}
                </button>
              ))}
            </div>

            {/* 5 视角切换过滤器 (正面 0°, 斜侧 45°, 侧面 90°, 俯视 +30°, 仰视 -30°) */}
            <div className="p-2.5 bg-gray-900/60 rounded-xl border border-gray-800/80 space-y-2">
              <div className="flex items-center justify-between text-[11px] text-gray-400">
                <span className="flex items-center space-x-1">
                  <Eye className="w-3.5 h-3.5 text-indigo-400" />
                  <span>{t('dance.choreo.cameraRig')}</span>
                </span>
                <span className="text-gray-500 text-[10px]">{t('dance.choreo.cameraRigSub')}</span>
              </div>
              <div className="grid grid-cols-6 gap-1.5 text-center">
                <button
                  onClick={() => setActiveAngleFilter('all')}
                  className={`py-1.5 px-1 rounded-lg text-[11px] font-semibold transition-all ${
                    activeAngleFilter === 'all' ? 'bg-indigo-600 text-white shadow' : 'bg-gray-900 text-gray-400 hover:text-gray-200'
                  }`}
                >
                  {t('dance.choreo.allAngles')}
                </button>
                {angles.map(a => (
                  <button
                    key={a.id}
                    onClick={() => setActiveAngleFilter(a.id)}
                    className={`py-1.5 px-1 rounded-lg text-[11px] font-semibold transition-all ${
                      activeAngleFilter === a.id ? 'bg-indigo-600 text-white shadow' : 'bg-gray-900 text-gray-400 hover:text-gray-200'
                    }`}
                  >
                    {t(`dance.choreo.angles.${a.id}`, a.name)} <span className="text-[9px] opacity-70">({a.degree})</span>
                  </button>
                ))}
              </div>
            </div>

            {/* 动作列表瀑布流/网格 */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[520px] overflow-y-auto pr-1">
              {filteredPoses.map((pose) => (
                <div 
                  key={pose.id}
                  className="group relative p-3 bg-gray-900/50 hover:bg-gray-900 border border-gray-800/80 hover:border-pink-500/40 rounded-xl transition-all duration-200 flex flex-col justify-between"
                >
                  <div className="flex gap-3">
                    {/* 3:4 视角动态缩略图 */}
                    {pose.preview_urls && (
                      <div className="w-16 h-[85px] flex-shrink-0 rounded-lg overflow-hidden border border-gray-800 bg-gray-950 group-hover:border-pink-500/50 transition-all relative">
                        <img 
                          src={pose.preview_urls[activeAngleFilter !== 'all' && pose.preview_urls[activeAngleFilter] ? activeAngleFilter : (pose.default_angle || 'front')] || Object.values(pose.preview_urls)[0]} 
                          alt={pose.name}
                          className="w-full h-full object-cover object-top"
                          loading="lazy"
                        />
                      </div>
                    )}

                    <div className="flex-1 min-w-0 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-pink-500/10 text-pink-400 font-bold">
                          {pose.code}
                        </span>
                        <span className="text-[11px] text-gray-400">
                          {pose.recommended_beats} {t('dance.choreo.beatsUnit')} · {pose.recommended_seconds}s
                        </span>
                      </div>
                      <div className="font-bold text-xs text-gray-200 group-hover:text-pink-300 transition-colors truncate">
                        {pose.name}
                      </div>
                      <p className="text-[11px] text-gray-400 line-clamp-2 leading-relaxed">
                        {pose.dynamic_prompt}
                      </p>
                      <div className="flex flex-wrap gap-1 pt-1">
                        {(pose.tags || []).slice(0, 3).map((tag, i) => (
                          <span key={i} className="text-[9px] px-1.5 py-0.5 bg-gray-800 text-gray-400 rounded">
                            #{tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="pt-3 mt-2 border-t border-gray-800/60 flex items-center justify-between">
                    <div className="flex items-center space-x-1 text-[10px] text-gray-500">
                      <span>{t('dance.choreo.defaultAngle')}</span>
                      <span className="text-indigo-400 font-medium">
                        {t(`dance.choreo.angles.${pose.default_angle}`, angles.find(a => a.id === pose.default_angle)?.name || '正面')}
                      </span>
                    </div>
                    <button 
                      onClick={() => handleAddPose(pose)}
                      className="px-2.5 py-1 bg-pink-500/20 hover:bg-pink-500 text-pink-300 hover:text-white rounded-lg text-xs font-bold transition-all flex items-center space-x-1 shadow-sm active:scale-95"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>{t('dance.choreo.addToTimeline')}</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>

          </div>
        </div>

        {/* ================= 右侧：自由编舞时间轴工作台 ================= */}
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-gray-950/70 border border-gray-800 rounded-2xl p-4 space-y-4 shadow-xl">
            
            {/* 时间轴标题与统计数据 */}
            <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-gray-800">
              <div className="space-y-0.5">
                <div className="flex items-center space-x-2">
                  <Sliders className="w-4 h-4 text-pink-400" />
                  <h3 className="text-sm font-bold text-gray-100">{t('dance.choreo.timelineTitle')}</h3>
                  {imagePreview && (
                    <img 
                      src={imagePreview} 
                      alt="Target dancer" 
                      className="w-5 h-5 rounded-full object-cover object-top border border-pink-500/50" 
                    />
                  )}
                </div>
                <p className="text-[11px] text-gray-400">
                  {t('dance.choreo.currentPoses')} <span className="text-pink-400 font-bold">{timeline.length}</span> · 
                  {t('dance.choreo.totalBeats')} <span className="text-purple-400 font-bold">{totalBeats}</span> {t('dance.choreo.beatsUnit')} · 
                  {t('dance.choreo.estDuration')} <span className="text-emerald-400 font-bold">{totalSeconds.toFixed(1)}</span>s
                </p>
              </div>

              {/* BPM 快速调整 */}
              <div className="flex items-center space-x-2 bg-gray-900 px-3 py-1.5 rounded-xl border border-gray-800">
                <Music className="w-3.5 h-3.5 text-pink-400" />
                <span className="text-xs text-gray-400 font-medium">BPM:</span>
                <input 
                  id="bpm-input"
                  name="bpm-input"
                  type="number" 
                  value={bpm} 
                  onChange={(e) => setBpm(parseInt(e.target.value) || 120)}
                  className="w-12 bg-transparent text-xs font-bold text-pink-400 focus:outline-none"
                />
              </div>
            </div>

            {/* 动作槽位列表 */}
            {timeline.length === 0 ? (
              <div className="p-8 text-center space-y-2 border-2 border-dashed border-gray-800 rounded-xl">
                <p className="text-xs text-gray-400">{t('dance.choreo.emptyTimeline')}</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
                {timeline.map((slot, idx) => {
                  const isFirst = idx === 0
                  const isLast = idx === timeline.length - 1
                  const nextSlot = timeline[idx + 1]
                  const currentPoseDef = poses.find(p => p.id === slot.pose_id)
                  const isSmoothAffinity = nextSlot && currentPoseDef && (currentPoseDef.transition_affinity || []).includes(nextSlot.pose_id)

                  return (
                    <div key={slot.slot_id} className="space-y-1.5">
                      
                      {/* 单个动作槽位卡片 */}
                      <div className="p-3 bg-gray-900/70 border border-gray-800 rounded-xl flex items-center justify-between gap-3 hover:border-gray-700 transition-all">
                        
                        <div className="flex items-center space-x-2.5">
                          <div className="w-6 h-6 rounded-lg bg-pink-500/20 text-pink-300 flex items-center justify-center text-xs font-bold font-mono flex-shrink-0">
                            {idx + 1}
                          </div>
                          {slot.preview_urls && Object.keys(slot.preview_urls).length > 0 && (
                            <div className="w-9 h-12 rounded overflow-hidden border border-gray-700 bg-gray-950 flex-shrink-0 relative">
                              <img 
                                src={slot.preview_urls[slot.angle] || Object.values(slot.preview_urls)[0]} 
                                alt={slot.name}
                                className="w-full h-full object-cover object-top"
                              />
                            </div>
                          )}
                          <div>
                            <div className="text-xs font-bold text-gray-200">{slot.name}</div>
                            <div className="text-[10px] text-gray-500 flex items-center space-x-2 mt-0.5">
                              <span>{t(`dance.choreo.stages.${slot.category}`, slot.category)}</span>
                              <span>•</span>
                              <span>{slot.seconds}s</span>
                            </div>
                          </div>
                        </div>

                        {/* 视角切换下拉 */}
                        <div className="flex items-center space-x-2">
                          <select 
                            id={`angle-select-${slot.slot_id}`}
                            name={`angle-select-${slot.slot_id}`}
                            aria-label={`Angle for ${slot.name}`}
                            value={slot.angle}
                            onChange={(e) => handleChangeAngle(slot.slot_id, e.target.value)}
                            className="bg-gray-800 border border-gray-700 rounded-lg text-xs text-indigo-300 px-2 py-1 focus:outline-none"
                          >
                            <option value="front">{t('dance.choreo.angles.front')}</option>
                            <option value="oblique">{t('dance.choreo.angles.oblique')}</option>
                            <option value="side">{t('dance.choreo.angles.side')}</option>
                            <option value="top">{t('dance.choreo.angles.top')}</option>
                            <option value="low">{t('dance.choreo.angles.low')}</option>
                          </select>

                          {/* 拍数微调 */}
                          <div className="flex items-center space-x-1 bg-gray-800 px-1.5 py-0.5 rounded-lg border border-gray-700 text-xs">
                            <button 
                              onClick={() => handleChangeBeats(slot.slot_id, slot.beats - 2)}
                              className="px-1 text-gray-400 hover:text-white"
                            >
                              -
                            </button>
                            <span className="font-mono text-pink-400 text-[11px] font-bold w-6 text-center">
                              {slot.beats}{t('dance.choreo.beatsUnit')}
                            </span>
                            <button 
                              onClick={() => handleChangeBeats(slot.slot_id, slot.beats + 2)}
                              className="px-1 text-gray-400 hover:text-white"
                            >
                              +
                            </button>
                          </div>

                          {/* 顺序调换与删除 */}
                          <div className="flex items-center space-x-0.5">
                            <button 
                              disabled={isFirst} 
                              onClick={() => handleMoveSlot(idx, 'up')}
                              className="p-1 text-gray-500 hover:text-gray-200 disabled:opacity-20"
                            >
                              <ArrowUp className="w-3.5 h-3.5" />
                            </button>
                            <button 
                              disabled={isLast} 
                              onClick={() => handleMoveSlot(idx, 'down')}
                              className="p-1 text-gray-500 hover:text-gray-200 disabled:opacity-20"
                            >
                              <ArrowDown className="w-3.5 h-3.5" />
                            </button>
                            <button 
                              onClick={() => handleRemoveSlot(slot.slot_id)}
                              className="p-1 text-gray-500 hover:text-red-400 transition-colors"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>

                        </div>

                      </div>

                      {/* 相邻动作流线平滑度检测胶囊 */}
                      {!isLast && (
                        <div className="flex items-center justify-center space-x-1.5 py-0.5 text-[10px]">
                          {isSmoothAffinity ? (
                            <span className="flex items-center space-x-1 text-emerald-400 font-medium">
                              <Zap className="w-3 h-3 text-emerald-400" />
                              <span>{t('dance.choreo.bestTransition')}</span>
                            </span>
                          ) : (
                            <span className="text-gray-500">
                              {t('dance.choreo.cutTransition')}
                            </span>
                          )}
                        </div>
                      )}

                    </div>
                  )
                })}
              </div>
            )}

            {/* 配方标题与配方卡保存 */}
            <div className="pt-3 border-t border-gray-800 space-y-3">
              <div className="flex items-center gap-2">
                <input 
                  id="recipe-title-input"
                  name="recipe-title-input"
                  type="text" 
                  value={recipeTitle} 
                  onChange={(e) => setRecipeTitle(e.target.value)}
                  placeholder={t('dance.choreo.recipeNamePlaceholder')} 
                  className="flex-1 px-3 py-2 bg-gray-900 border border-gray-800 rounded-xl text-xs text-gray-200 focus:outline-none focus:border-pink-500"
                />
                <button 
                  id="btn-save-recipe"
                  onClick={handleSaveRecipe}
                  disabled={timeline.length === 0}
                  className="px-4 py-2 bg-gray-800 hover:bg-gray-700 disabled:opacity-40 text-gray-200 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all shadow"
                >
                  <Share2 className="w-3.5 h-3.5 text-pink-400" />
                  <span>{t('dance.choreo.genRecipeCard')}</span>
                </button>
              </div>

              {/* 剪映专业版草稿选项 */}
              <label className="flex items-center space-x-2 text-xs text-gray-300 cursor-pointer select-none">
                <input 
                  id="enable-jianying-draft-checkbox"
                  name="enable-jianying-draft-checkbox"
                  type="checkbox" 
                  checked={enableJianying} 
                  onChange={(e) => setEnableJianying(e.target.checked)}
                  className="rounded bg-gray-900 border-gray-700 text-purple-600 focus:ring-0"
                />
                <Film className="w-3.5 h-3.5 text-purple-400" />
                <span>{t('dance.choreo.exportJianying')}</span>
              </label>

              {/* 提交自由编舞渲染大按钮 */}
              <button 
                onClick={() => onStartChoreograph(timeline, bpm, style, enableJianying)}
                disabled={loading || timeline.length === 0 || !imageFile}
                className="w-full py-3.5 px-6 rounded-xl font-bold text-sm flex items-center justify-center space-x-2 transition-all shadow-xl bg-gradient-to-r from-pink-500 via-purple-600 to-indigo-600 hover:from-pink-400 hover:to-indigo-500 text-white shadow-pink-500/25 active:scale-[0.99] disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4" />
                <span>
                  {loading 
                    ? t('dance.choreo.rendering')
                    : !imageFile 
                    ? t('dance.choreo.needDancer')
                    : t('dance.choreo.renderBtn', { seconds: totalSeconds.toFixed(0), count: timeline.length })
                  }
                </span>
              </button>

            </div>

          </div>
        </div>

      </div>

      {/* ================= 3:4 社交裂变配方卡弹窗 (Recipe Share Modal) ================= */}
      {showShareModal && shareData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-fade-in">
          <div className="bg-gray-950 border border-purple-500/40 rounded-3xl max-w-sm w-full p-6 space-y-5 shadow-2xl relative">
            
            {/* 关闭按钮 */}
            <button 
              onClick={() => setShowShareModal(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-white text-lg"
            >
              ✕
            </button>

            {/* 3:4 比例卡片预览区域 */}
            <div className="w-full aspect-[3/4] bg-gradient-to-br from-purple-950/60 via-gray-900 to-pink-950/60 border border-purple-500/30 rounded-2xl p-4 flex flex-col justify-between shadow-inner relative overflow-hidden">
              <div className="absolute top-0 right-0 p-3 opacity-10">
                <Music className="w-32 h-32 text-pink-400" />
              </div>

              <div className="space-y-2 relative z-10">
                <div className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-pink-500/20 border border-pink-500/30 text-[10px] text-pink-300 font-bold">
                  <span>{t('dance.choreo.shareModalTitle')}</span>
                </div>
                <h4 className="text-base font-extrabold text-white leading-tight">
                  {shareData.title}
                </h4>
                <div className="text-[11px] text-gray-400 font-mono">
                  BPM {shareData.bpm} · {shareData.total_duration}s · {shareData.pose_count} Poses
                </div>
              </div>

              {/* 动作序列缩影清单 */}
              <div className="space-y-1.5 my-auto relative z-10">
                {timeline.slice(0, 4).map((slot, i) => (
                  <div key={i} className="flex items-center justify-between text-[11px] p-1.5 bg-gray-950/60 rounded-lg border border-gray-800">
                    <span className="text-gray-300 truncate max-w-[150px]">0{i+1}. {slot.name}</span>
                    <span className="text-pink-400 font-mono font-bold">{t(`dance.choreo.angles.${slot.angle}`, slot.angle)}</span>
                  </div>
                ))}
                {timeline.length > 4 && (
                  <div className="text-[10px] text-center text-gray-500">
                    {t('dance.choreo.posesRecorded', { count: timeline.length - 4 })}
                  </div>
                )}
              </div>

              {/* 底部裂变标识 */}
              <div className="pt-2 border-t border-gray-800/80 flex items-center justify-between relative z-10 text-[10px]">
                <div className="text-gray-400">
                  {t('dance.choreo.recipeIdLabel')} <span className="font-mono text-purple-400 font-bold">{shareData.recipe_id}</span>
                </div>
                <div className="text-pink-400 font-bold">
                  {t('dance.choreo.scanToClone')}
                </div>
              </div>
            </div>

            {/* 复制分享链接与 ID */}
            <div className="space-y-2">
              <button 
                onClick={handleCopyLink}
                className="w-full py-2.5 px-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white rounded-xl text-xs font-bold transition-all flex items-center justify-center space-x-2 shadow-lg"
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                <span>{copied ? t('dance.choreo.copied') : t('dance.choreo.copyCard')}</span>
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  )
}
