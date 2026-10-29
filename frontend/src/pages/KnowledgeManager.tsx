import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { useTranslation } from '../locales/i18n';
import client from '../api/client';
import { 
  BookOpen, 
  Search, 
  FileText, 
  Database, 
  Sparkles,
  Upload
} from 'lucide-react';

interface KnowledgeBaseItem {
  id: number;
  name: string;
  description?: string;
  created_at?: string;
}

interface DocumentItem {
  id: number;
  kb_id: number;
  doc_id: string;
  title: string;
  content: string;
  chunk_count: number;
}

interface SearchResultItem {
  chunk_id: string;
  title?: string;
  content: string;
  score: number;
}

export const KnowledgeManager: React.FC = () => {
  const { t } = useTranslation();
  const [kbList, setKbList] = useState<KnowledgeBaseItem[]>([]);
  const [activeKbId, setActiveKbId] = useState<number | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);

  // 搜索联调状态
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // 创建知识库弹窗
  const [showKbModal, setShowKbModal] = useState(false);
  const [newKbName, setNewKbName] = useState('');
  const [newKbDesc, setNewKbDesc] = useState('');

  // 上传文档弹窗
  const [showDocModal, setShowDocModal] = useState(false);
  const [newDocTitle, setNewDocTitle] = useState('');
  const [newDocContent, setNewDocContent] = useState('');

  const loadKbList = async () => {
    try {
      const res = await client.get('/api/v1/knowledge');
      const list: KnowledgeBaseItem[] = res.data || [];
      setKbList(list);
      if (list.length > 0 && !activeKbId) {
        setActiveKbId(list[0].id);
      }
    } catch (err) {
      console.warn('Failed to load KB list', err);
    }
  };

  const loadDocuments = async (kbId: number) => {
    try {
      const res = await client.get(`/api/v1/knowledge/${kbId}/documents`);
      setDocuments(res.data || []);
    } catch (err) {
      console.warn('Failed to load docs', err);
    }
  };

  useEffect(() => {
    loadKbList();
  }, []);

  useEffect(() => {
    if (activeKbId) {
      loadDocuments(activeKbId);
    }
  }, [activeKbId]);

  const handleCreateKb = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKbName.trim()) return;

    try {
      const res = await client.post('/api/v1/knowledge', {
        name: newKbName.trim(),
        description: newKbDesc.trim() || '默认直播带货专业知识库',
      });
      setShowKbModal(false);
      setNewKbName('');
      setNewKbDesc('');
      await loadKbList();
      if (res.data?.id) {
        setActiveKbId(res.data.id);
      }
    } catch (err) {
      console.error('Failed to create KB', err);
    }
  };

  const handleUploadDoc = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeKbId || !newDocTitle.trim() || !newDocContent.trim()) return;

    try {
      await client.post(`/api/v1/knowledge/${activeKbId}/documents`, {
        title: newDocTitle.trim(),
        content: newDocContent.trim(),
        doc_id: `doc_${Date.now()}`,
      });
      setShowDocModal(false);
      setNewDocTitle('');
      setNewDocContent('');
      loadDocuments(activeKbId);
    } catch (err) {
      console.error('Failed to upload document', err);
    }
  };

  const handleTestSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !activeKbId) return;

    setIsSearching(true);
    setSearchResults([]);

    try {
      const res = await client.post(`/api/v1/knowledge/${activeKbId}/search`, {
        query: query.trim(),
        top_k: 3,
      });
      setSearchResults(res.data?.results || []);
    } catch (err) {
      console.error('RAG test query failed', err);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 顶部标题栏 */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-100 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-indigo-400" />
            {t('knowledge.title')}
          </h2>
          <p className="text-xs text-gray-400 mt-1">{t('knowledge.subtitle')}</p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            onClick={() => setShowKbModal(true)}
            leftIcon={<Database className="w-4 h-4" />}
          >
            {t('knowledge.createKb')}
          </Button>

          <Button
            variant="primary"
            onClick={() => setShowDocModal(true)}
            disabled={!activeKbId}
            leftIcon={<Upload className="w-4 h-4" />}
          >
            {t('knowledge.uploadDoc')}
          </Button>
        </div>
      </div>

      {/* 知识库切换胶囊条 */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {kbList.map((kb) => (
          <button
            key={kb.id}
            onClick={() => setActiveKbId(kb.id)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-2 ${
              activeKbId === kb.id
                ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 shadow-lg shadow-indigo-500/5'
                : 'bg-white/5 text-gray-400 hover:text-gray-200 border border-transparent'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>{kb.name}</span>
          </button>
        ))}
      </div>

      {/* 主工作区：左侧文档切片列表 + 右侧 RAG 检索联调器 */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* 左侧切片文档列表 (7 栏) */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              知识切片文档库 ({documents.length} 篇)
            </h3>
          </div>

          {documents.length === 0 ? (
            <Card className="p-8 text-center text-gray-500 text-xs">
              该知识库暂未上传切片文档，点击右上角“导入文档切片”录入商品规则或台本。
            </Card>
          ) : (
            documents.map((doc) => (
              <Card key={doc.id} className="p-4 space-y-2 hover:border-indigo-500/40 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
                    <span className="font-semibold text-sm text-gray-200">{doc.title}</span>
                  </div>
                  <Badge variant="success" size="sm">已索引 ({doc.chunk_count} chunks)</Badge>
                </div>
                <p className="text-xs text-gray-400 line-clamp-2 pl-6">
                  {doc.content}
                </p>
                <div className="pl-6 text-[10px] text-gray-500 font-mono">
                  切片编号: {doc.doc_id}
                </div>
              </Card>
            ))
          )}
        </div>

        {/* 右侧 RAG 联调器 (5 栏) */}
        <div className="lg:col-span-5 space-y-4">
          <Card className="p-5 space-y-4 border-indigo-500/30">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-gray-100 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-pink-400" />
                {t('knowledge.searchTest')}
              </h3>
              <Badge variant="info" size="sm">BM25Plus 算法</Badge>
            </div>

            <p className="text-xs text-gray-400">
              输入模拟观众在直播间的提问，实时测试知识库相似度召回与切片截取效果。
            </p>

            <form onSubmit={handleTestSearch} className="space-y-3">
              <Input
                placeholder={t('knowledge.searchPlaceholder')}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="text-xs"
              />
              <Button
                type="submit"
                variant="primary"
                className="w-full text-xs"
                isLoading={isSearching}
                leftIcon={<Search className="w-3.5 h-3.5" />}
              >
                {t('knowledge.searchBtn')}
              </Button>
            </form>

            {/* 检索结果展示 */}
            <div className="pt-3 border-t border-white/10 space-y-2">
              <span className="text-xs font-semibold text-gray-300 block">
                {t('knowledge.searchResult')}
              </span>

              {searchResults.length === 0 ? (
                <div className="p-4 rounded-xl bg-gray-950/50 border border-white/5 text-center text-gray-500 text-xs">
                  暂无匹配切片，请输入问题并点击检索测试
                </div>
              ) : (
                searchResults.map((res, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-indigo-950/40 border border-indigo-500/30 space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-indigo-300">{res.title || res.chunk_id}</span>
                      <span className="text-[10px] text-emerald-400 font-mono">
                        相关度: {Number(res.score).toFixed(3)}
                      </span>
                    </div>
                    <p className="text-gray-300 leading-relaxed text-[11px]">{res.content}</p>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* 新建知识库弹窗 */}
      {showKbModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="w-full max-w-md p-6 space-y-4">
            <h3 className="text-base font-bold text-gray-100">{t('knowledge.createKb')}</h3>
            <form onSubmit={handleCreateKb} className="space-y-3 text-xs">
              <div>
                <label className="text-gray-300 block mb-1">{t('knowledge.kbName')}</label>
                <Input
                  placeholder="如: 数码 3C 专场带货知识库"
                  value={newKbName}
                  onChange={(e) => setNewKbName(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="text-gray-300 block mb-1">知识库描述</label>
                <Input
                  placeholder="适用场景与商品类目说明..."
                  value={newKbDesc}
                  onChange={(e) => setNewKbDesc(e.target.value)}
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button variant="secondary" type="button" onClick={() => setShowKbModal(false)}>
                  {t('common.cancel')}
                </Button>
                <Button variant="primary" type="submit">
                  {t('common.save')}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* 导入文档切片弹窗 */}
      {showDocModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="w-full max-w-lg p-6 space-y-4">
            <h3 className="text-base font-bold text-gray-100">{t('knowledge.uploadDoc')}</h3>
            <form onSubmit={handleUploadDoc} className="space-y-3 text-xs">
              <div>
                <label className="text-gray-300 block mb-1">{t('knowledge.docTitle')}</label>
                <Input
                  placeholder="如: 降噪耳机售后政策与常见 QA"
                  value={newDocTitle}
                  onChange={(e) => setNewDocTitle(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="text-gray-300 block mb-1">{t('knowledge.docContent')}</label>
                <textarea
                  rows={6}
                  placeholder="输入知识库正文内容，系统将自动基于 512 字符滑窗和 64 字符重叠进行智能切片并建立倒排索引..."
                  value={newDocContent}
                  onChange={(e) => setNewDocContent(e.target.value)}
                  className="w-full bg-gray-900 border border-white/15 rounded-xl p-3 text-gray-200 text-xs focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button variant="secondary" type="button" onClick={() => setShowDocModal(false)}>
                  {t('common.cancel')}
                </Button>
                <Button variant="primary" type="submit">
                  {t('common.save')}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
};
export default KnowledgeManager;
