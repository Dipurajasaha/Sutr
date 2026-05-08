import { useEffect, useRef, useState } from 'react'
import type { ChangeEvent, DragEvent } from 'react'
import axios from 'axios'
import { LoaderCircle, UploadCloud, X } from 'lucide-react'
import { apiClient, uploadClient } from '../api/client'

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
  onUploadSuccess: (file: UploadedFileResponse) => void
}

export default function UploadModal({ isOpen, onClose, onUploadSuccess }: UploadModalProps) {
  const inputRef = useRef<HTMLInputElement | null>(null)
  const isMountedRef = useRef(false)
  const [isUploading, setIsUploading] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    isMountedRef.current = true

    return () => {
      isMountedRef.current = false
    }
  }, [])

  if (!isOpen) return null

  const openPicker = () => inputRef.current?.click()

  const uploadFile = async (file: File) => {
    if (isUploading) return

    const formData = new FormData()
    formData.append('file', file)

    setIsUploading(true)
    setIsProcessing(false)
    setErrorMessage('')

    try {
      const response = await uploadClient.post<UploadedFileResponse>('/api/upload/', formData)

      if (!isMountedRef.current) return

      setIsProcessing(true)
      await apiClient.post('/api/process/', {
        file_id: response.data.id,
        file_path: response.data.file_path,
        file_type: response.data.file_type,
      })

      if (!isMountedRef.current) return

      onUploadSuccess(response.data)
      onClose()
    } catch (error: unknown) {
      if (!isMountedRef.current) return

      const detail = axios.isAxiosError(error) ? error.response?.data?.detail : undefined
      setErrorMessage(typeof detail === 'string' ? detail : 'Upload failed. Please try again.')
    } finally {
      if (isMountedRef.current) {
        setIsUploading(false)
        setIsProcessing(false)
      }
    }
  }

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      void uploadFile(file)
    }
    event.target.value = ''
  }

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    const file = event.dataTransfer.files?.[0]
    if (file) {
      void uploadFile(file)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
      <div className="relative w-full max-w-lg rounded-2xl border border-zinc-800 bg-zinc-900 p-6 shadow-2xl shadow-black/40">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-2 text-zinc-400 hover:bg-zinc-800 hover:text-white"
          aria-label="Close upload modal"
        >
          <X className="h-5 w-5" />
        </button>

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
          className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-6 py-14 text-center transition ${
            isUploading ? 'border-purple-500/40 bg-zinc-900/80' : 'border-zinc-700 hover:border-zinc-500'
          }`}
        >
          <div className="rounded-full bg-zinc-800 p-4">
            {isUploading ? (
              <LoaderCircle className="h-8 w-8 animate-spin text-purple-400" />
            ) : (
              <UploadCloud className="h-8 w-8 text-purple-400" />
            )}
          </div>
          <div className="text-lg font-semibold text-white">
            {isProcessing
              ? 'Analyzing document with AI... this may take a minute.'
              : isUploading
                ? 'Uploading... Please wait'
                : 'Click to upload or drag and drop'}
          </div>
          <div className="text-sm text-zinc-400">PDF, MP4, MP3 up to 50MB</div>
          {errorMessage ? <div className="max-w-sm text-sm text-red-400">{errorMessage}</div> : null}
          <input
            ref={inputRef}
            type="file"
            className="hidden"
            accept=".pdf,video/*,audio/*"
            multiple={false}
            onChange={handleChange}
          />
        </div>
      </div>
    </div>
  )
}