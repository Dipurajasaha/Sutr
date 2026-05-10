import { useEffect, useRef, useState } from 'react'
import type { ChangeEvent, DragEvent } from 'react'
import axios from 'axios'
import { UploadCloud } from 'lucide-react'
import { apiClient, uploadClient } from '../api/client'

export type UploadQueueStatus = 'queued' | 'uploading' | 'processing' | 'completed' | 'failed'

export type UploadQueueUpdate = {
  clientId: string
  name: string
  progress: number
  status: UploadQueueStatus
  errorMessage?: string
}

export type UploadedFileResponse = {
  id: string
  filename: string
  file_type: string
  file_path: string
  status: string
}

type UploadModalProps = {
  isOpen: boolean
  onClose: () => void
  onUploadSuccess: (file: UploadedFileResponse, targetFolderId: string | null) => void
  onUploadQueueUpdate: (update: UploadQueueUpdate) => void
  targetFolderId: string | null
}

export default function UploadModal({
  isOpen,
  onClose,
  onUploadSuccess,
  onUploadQueueUpdate,
  targetFolderId,
}: UploadModalProps) {
  const inputRef = useRef<HTMLInputElement | null>(null)
  const isMountedRef = useRef(false)
  const overlayRef = useRef<HTMLDivElement | null>(null)
  const [isVisible, setIsVisible] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    isMountedRef.current = true

    return () => {
      isMountedRef.current = false
    }
  }, [])

  useEffect(() => {
    if (isOpen) {
      setErrorMessage('')
    }
  }, [isOpen])

  useEffect(() => {
    // Trigger mount animation after the component renders
    setIsVisible(false)
    if (isOpen) {
      requestAnimationFrame(() => setIsVisible(true))
    }
  }, [isOpen])

  if (!isOpen) return null

  const openPicker = () => inputRef.current?.click()

  const uploadFile = async (file: File, clientId: string, selectedTargetFolderId: string | null) => {
    const formData = new FormData()
    formData.append('file', file)
    const uploadStartedAt = Date.now()
    let displayedUploadProgress = 0

    onUploadQueueUpdate({
      clientId,
      name: file.name,
      progress: 0,
      status: 'queued',
    })

    try {
      onUploadQueueUpdate({
        clientId,
        name: file.name,
        progress: 5,
        status: 'uploading',
      })
      displayedUploadProgress = 5

      const response = await uploadClient.post<UploadedFileResponse>('/api/upload/', formData, {
        onUploadProgress: (progressEvent) => {
          const total = progressEvent.total ?? file.size
          const loaded = progressEvent.loaded
          const rawUploadRatio = total > 0 ? loaded / total : 0

          // Stage model:
          // 0-60%: network upload (byte-based, but time-gated to avoid instant jumps on tiny files)
          // 60-99%: backend processing
          const rawUploadProgress = 5 + rawUploadRatio * 55
          const elapsedMs = Date.now() - uploadStartedAt
          const timeGatedMax = Math.min(60, 5 + elapsedMs / 90)
          const nextProgress = Math.min(rawUploadProgress, timeGatedMax)

          displayedUploadProgress = Math.max(displayedUploadProgress, nextProgress)

          onUploadQueueUpdate({
            clientId,
            name: file.name,
            progress: Number(displayedUploadProgress.toFixed(1)),
            status: 'uploading',
          })
        },
      })

      if (!isMountedRef.current) return

      const processingStartedAt = Date.now()
      let processingProgress = Math.max(displayedUploadProgress, 60)
      onUploadQueueUpdate({
        clientId,
        name: file.name,
        progress: Number(processingProgress.toFixed(1)),
        status: 'processing',
      })

      const processingPulse = window.setInterval(() => {
        if (!isMountedRef.current) {
          return
        }

        const elapsedMs = Date.now() - processingStartedAt
        const dynamicCeiling = Math.min(99, 90 + elapsedMs / 1500)
        const easeInBoost = Math.min(0.9, elapsedMs / 18000)
        const baseStep = 0.12 + easeInBoost
        const distanceFactor = Math.max(0.25, (dynamicCeiling - processingProgress) / 9)

        processingProgress = Math.min(dynamicCeiling, processingProgress + baseStep * distanceFactor)

        onUploadQueueUpdate({
          clientId,
          name: file.name,
          progress: Number(processingProgress.toFixed(1)),
          status: 'processing',
        })
      }, 450)

      try {
        await apiClient.post('/api/process/', {
          file_id: response.data.id,
          file_path: response.data.file_path,
          file_type: response.data.file_type,
        })
      } finally {
        window.clearInterval(processingPulse)
      }

      if (!isMountedRef.current) return

      onUploadQueueUpdate({
        clientId,
        name: file.name,
        progress: 100,
        status: 'completed',
      })
      onUploadSuccess(response.data, selectedTargetFolderId)
    } catch (error: unknown) {
      if (!isMountedRef.current) return

      const detail = axios.isAxiosError(error) ? error.response?.data?.detail : undefined
      const normalizedError = typeof detail === 'string' ? detail : 'Upload failed. Please try again.'
      setErrorMessage(normalizedError)
      onUploadQueueUpdate({
        clientId,
        name: file.name,
        progress: 100,
        status: 'failed',
        errorMessage: normalizedError,
      })
    }
  }

  const startUploads = (files: FileList | File[]) => {
    const selectedFiles = Array.from(files)
    if (selectedFiles.length === 0) {
      return
    }

    setErrorMessage('')
    const selectedTargetFolderId = targetFolderId

    onClose()

    void Promise.allSettled(
      selectedFiles.map(async (file) => {
        const clientId = crypto.randomUUID()
        await uploadFile(file, clientId, selectedTargetFolderId)
      }),
    )
  }

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      startUploads(event.target.files)
    }
    event.target.value = ''
  }

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
      startUploads(event.dataTransfer.files)
    }
  }

  return (
    <div
      ref={overlayRef}
      onMouseDown={(e) => {
        if (e.target === overlayRef.current) {
          onClose()
        }
      }}
      className={`fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4 transition-opacity duration-300 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
    >
      <div
        className={`relative w-full max-w-lg rounded-2xl border border-zinc-800 bg-zinc-900 p-6 shadow-2xl shadow-black/40 modal-enter transform ${
          isVisible ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-6 scale-95'
        }`}
      >
        {/* subtle purple glow behind modal */}
        <div className="absolute -inset-2 rounded-2xl modal-glow pointer-events-none" style={{ zIndex: -1 }} />

        

        <div
          role="button"
          tabIndex={0}
          onClick={openPicker}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault()
              openPicker()
            }
          }}
          onDragOver={(event) => event.preventDefault()}
          onDrop={handleDrop}
          className="relative flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed border-zinc-700 px-6 py-14 text-center transition hover:border-zinc-500"
        >
          <div className="relative rounded-full bg-zinc-800 p-4">
            <span className="absolute -inset-2 rounded-full bg-linear-to-r from-purple-600/40 to-pink-500/10 blur-2xl opacity-30"></span>
            <UploadCloud className="h-8 w-8 text-purple-400 relative" />
          </div>
          <div className="text-lg font-semibold text-white">Click to upload or drag and drop</div>
          <div className="text-sm text-zinc-400">PDF, MP4, MP3 up to 50MB. Multiple files supported.</div>
          {errorMessage ? <div className="max-w-sm text-sm text-red-400">{errorMessage}</div> : null}
          <input
            ref={inputRef}
            type="file"
            className="hidden"
            accept=".pdf,video/*,audio/*"
            multiple
            onChange={handleChange}
          />
        </div>
      </div>
    </div>
  )
}