import { create } from 'zustand'

import { type AnalyzeSummary, type VideoUploadResponse } from '@/lib/api'

type SessionState = {
  audioSummary: AnalyzeSummary | null
  videoResult: VideoUploadResponse | null
  setAudioSummary: (summary: AnalyzeSummary | null) => void
  setVideoResult: (result: VideoUploadResponse | null) => void
}

export const useSessionStore = create<SessionState>((set) => ({
  audioSummary: null,
  videoResult: null,
  setAudioSummary: (audioSummary) => set({ audioSummary }),
  setVideoResult: (videoResult) => set({ videoResult }),
}))
