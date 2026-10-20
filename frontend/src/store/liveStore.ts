import { create } from 'zustand';

export interface DanmakuMessage {
  id: string;
  sender: string;
  content: string;
  timestamp: string;
  type: 'danmaku' | 'gift' | 'agent_reply' | 'system';
}

export interface LiveProductItem {
  id: number;
  title: string;
  price: number;
  originalPrice?: number;
  coverImage?: string;
  isCurrent: boolean;
  sellingPoints: string[];
}

interface LiveState {
  roomId: string | null;
  sessionId: number | null;
  streamKey: string | null;
  status: 'idle' | 'streaming' | 'paused' | 'finished';
  rtmpUrl: string | null;
  httpFlvUrl: string | null;
  hlsUrl: string | null;
  viewerCount: number;
  peakViewers: number;
  currentProduct: LiveProductItem | null;
  danmakuList: DanmakuMessage[];
  latencyMs: number;
  isAudioMuted: boolean;

  setRoomInfo: (info: {
    roomId: string;
    sessionId?: number | null;
    streamKey?: string | null;
    status: 'idle' | 'streaming' | 'paused' | 'finished';
    rtmpUrl?: string;
    httpFlvUrl?: string;
    hlsUrl?: string;
  }) => void;
  updateViewers: (count: number, peak?: number) => void;
  setCurrentProduct: (product: LiveProductItem | null) => void;
  addDanmaku: (message: DanmakuMessage) => void;
  clearDanmaku: () => void;
  setLatency: (ms: number) => void;
  toggleMute: () => void;
  reset: () => void;
}

const MAX_DANMAKU_COUNT = 200;

export const useLiveStore = create<LiveState>((set) => ({
  roomId: null,
  sessionId: null,
  streamKey: null,
  status: 'idle',
  rtmpUrl: null,
  httpFlvUrl: null,
  hlsUrl: null,
  viewerCount: 0,
  peakViewers: 0,
  currentProduct: null,
  danmakuList: [],
  latencyMs: 0,
  isAudioMuted: false,

  setRoomInfo: (info) => set((state) => ({ ...state, ...info })),

  updateViewers: (count, peak) =>
    set((state) => ({
      viewerCount: count,
      peakViewers: peak !== undefined ? Math.max(state.peakViewers, peak, count) : Math.max(state.peakViewers, count),
    })),

  setCurrentProduct: (product) => set({ currentProduct: product }),

  addDanmaku: (msg) =>
    set((state) => {
      const nextList = [...state.danmakuList, msg];
      if (nextList.length > MAX_DANMAKU_COUNT) {
        nextList.splice(0, nextList.length - MAX_DANMAKU_COUNT);
      }
      return { danmakuList: nextList };
    }),

  clearDanmaku: () => set({ danmakuList: [] }),

  setLatency: (ms) => set({ latencyMs: ms }),

  toggleMute: () => set((state) => ({ isAudioMuted: !state.isAudioMuted })),

  reset: () =>
    set({
      roomId: null,
      sessionId: null,
      streamKey: null,
      status: 'idle',
      rtmpUrl: null,
      httpFlvUrl: null,
      hlsUrl: null,
      viewerCount: 0,
      peakViewers: 0,
      currentProduct: null,
      danmakuList: [],
      latencyMs: 0,
      isAudioMuted: false,
    }),
}));
