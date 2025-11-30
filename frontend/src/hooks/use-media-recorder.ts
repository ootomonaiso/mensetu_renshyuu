import { useCallback, useEffect, useRef, useState } from 'react'

export type RecorderStatus = 'idle' | 'requesting' | 'recording' | 'stopped' | 'error'

export type UseMediaRecorderOptions = {
  audio?: boolean
  video?: boolean
  mimeType?: string
}

export const useMediaRecorder = ({
  audio = true,
  video = false,
  mimeType,
}: UseMediaRecorderOptions) => {
  const [status, setStatus] = useState<RecorderStatus>('idle')
  const [error, setError] = useState<string | null>(null)
  const [duration, setDuration] = useState(0)
  const [blob, setBlob] = useState<Blob | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const previewUrlRef = useRef<string | null>(null)

  const recorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<number | null>(null)

  const cleanupStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
  }, [])

  const reset = useCallback(() => {
    recorderRef.current?.stop()
    cleanupStream()
    chunksRef.current = []
    setBlob(null)
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current)
      previewUrlRef.current = null
    }
    setPreviewUrl(null)
    setDuration(0)
    setStatus('idle')
    setError(null)
  }, [cleanupStream])

  const start = useCallback(async () => {
    try {
      setError(null)
      setStatus('requesting')
      setDuration(0)
      chunksRef.current = []

      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('このブラウザは録音・録画に対応していません')
      }

      const constraints: MediaStreamConstraints = {
        audio,
        video,
      }

      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      streamRef.current = stream

      const resolvedMime =
        mimeType ?? (video ? 'video/webm;codecs=vp9,opus' : 'audio/webm;codecs=opus')
      const recorder = new MediaRecorder(stream, { mimeType: resolvedMime })
      recorderRef.current = recorder

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      recorder.onstop = () => {
        const recordedBlob = new Blob(chunksRef.current, { type: resolvedMime })
        setBlob(recordedBlob)
        if (previewUrlRef.current) {
          URL.revokeObjectURL(previewUrlRef.current)
        }
        const url = URL.createObjectURL(recordedBlob)
        previewUrlRef.current = url
        setPreviewUrl(url)
        cleanupStream()
        setStatus('stopped')
      }

      recorder.onerror = (event) => {
        console.error('MediaRecorder error', event)
        setError('録音中にエラーが発生しました')
        setStatus('error')
      }

      recorder.start()
      setStatus('recording')

      timerRef.current = window.setInterval(() => {
        setDuration((prev) => prev + 1)
      }, 1000)
    } catch (err) {
      console.error(err)
      setError(err instanceof Error ? err.message : 'マイク・カメラへのアクセスが許可されませんでした')
      setStatus('error')
      cleanupStream()
    }
  }, [audio, video, mimeType, cleanupStream])

  const stop = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state === 'recording') {
      recorderRef.current.stop()
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [])

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
      recorderRef.current?.stop()
      cleanupStream()
      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current)
      }
    }
  }, [cleanupStream])

  return {
    status,
    error,
    duration,
    blob,
    previewUrl,
    isRecording: status === 'recording',
    start,
    stop,
    reset,
  }
}
