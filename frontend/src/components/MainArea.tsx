import { useLayoutEffect, useRef, useState } from 'react'
import { MessageSquareText, NotebookText, FolderOpen } from 'lucide-react'
import type { FileSystemItem } from './types'
import ChatView from './ChatView'
import SummaryView from './SummaryView'
import MediaPlayer from './MediaPlayer'
import { buildUploadUrl } from '../api/client'

type MainAreaProps = {
  activeFile: FileSystemItem | null
  mode: 'chat' | 'summary'
  onModeChange: (mode: 'chat' | 'summary') => void
  currentSeekTime?: number
  onCitationClick?: (startTime: number) => void
}

export default function MainArea({ activeFile, mode, onModeChange, currentSeekTime = 0, onCitationClick }: MainAreaProps) {
  const activeFileName = activeFile?.name ?? 'Select a document from the sidebar'
  const toggleRef = useRef<HTMLDivElement | null>(null)
  const chatButtonRef = useRef<HTMLButtonElement | null>(null)
  const summaryButtonRef = useRef<HTMLButtonElement | null>(null)
  const [indicatorStyle, setIndicatorStyle] = useState<{ left: number; width: number } | null>(null)

  const hasMediaFile = !!activeFile && (activeFile.fileType === 'video' || activeFile.fileType === 'audio')
  // Use API Gateway to serve uploads so we don't have CORS issues in production
  // Prefer backend stored file path (safe filename) if available
  let fileUrl = ''
  if (activeFile) {
    const stored = activeFile.filePath ? (activeFile.filePath.split(/[\\/]/).pop() ?? activeFile.name) : activeFile.name
    fileUrl = buildUploadUrl(stored)
  }

  useLayoutEffect(() => {
    const updateIndicator = () => {
      const containerRect = toggleRef.current?.getBoundingClientRect()
      const activeButton = mode === 'chat' ? chatButtonRef.current : summaryButtonRef.current
      const buttonRect = activeButton?.getBoundingClientRect()

      if (!containerRect || !buttonRect) {
        return
      }

      setIndicatorStyle({
        left: buttonRect.left - containerRect.left,
        width: buttonRect.width,
      })
    }

    updateIndicator()
    window.addEventListener('resize', updateIndicator)

    return () => window.removeEventListener('resize', updateIndicator)
  }, [mode])

  return (
    <section className="flex h-full flex-col overflow-hidden bg-zinc-950 text-white">
      <header className="flex h-16 shrink-0 items-center justify-between border-b border-zinc-800 px-6">
        <div className="min-w-0 pr-4 text-sm font-medium text-white truncate">{activeFileName}</div>

        <div ref={toggleRef} className="relative inline-flex rounded-full border border-zinc-800 bg-zinc-900 p-1">
          <div
            className="absolute top-1 h-[calc(100%-0.5rem)] rounded-full bg-purple-600 shadow-[0_0_0_1px_rgba(168,85,247,0.18),0_10px_24px_rgba(147,51,234,0.28)] transition-[left,width] duration-500 ease-[cubic-bezier(0.22,1,0.36,1)]"
            style={{
              left: indicatorStyle ? `${indicatorStyle.left}px` : '0.25rem',
              width: indicatorStyle ? `${indicatorStyle.width}px` : '0px',
            }}
          />
          <button
            ref={chatButtonRef}
            type="button"
            onClick={() => onModeChange('chat')}
            className="relative z-10 inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-colors duration-300"
            style={{
              color: mode === 'chat' ? 'white' : '#a1a1aa',
            }}
          >
            <MessageSquareText className="h-4 w-4" />
            Chat
          </button>
          <button
            ref={summaryButtonRef}
            type="button"
            onClick={() => onModeChange('summary')}
            className="relative z-10 inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-colors duration-300"
            style={{
              color: mode === 'summary' ? 'white' : '#a1a1aa',
            }}
          >
            <NotebookText className="h-4 w-4" />
            Summary
          </button>
        </div>
      </header>

      {hasMediaFile && activeFile && (
        <div className="shrink-0 overflow-hidden border-b border-zinc-800 bg-zinc-950">
          <MediaPlayer
            fileUrl={fileUrl}
            fileType={activeFile.fileType === 'video' ? 'video' : 'audio'}
            seekTime={currentSeekTime ?? 0}
          />
        </div>
      )}

      <div className="min-h-0 flex-1 overflow-hidden">
        {activeFile ? (
          mode === 'chat' ? (
            <ChatView key={activeFile?.id ?? 'no-file'} activeFile={activeFile} onCitationClick={onCitationClick} />
          ) : (
            <SummaryView key={activeFile?.id ?? 'no-file'} activeFile={activeFile} />
          )
        ) : (
          <div className="flex h-full items-center justify-center px-6">
            <div className="flex max-w-md flex-col items-center text-center">
              <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-3xl border border-zinc-800 bg-zinc-900/80">
                <FolderOpen className="h-16 w-16 text-zinc-600" />
              </div>
              <p className="text-lg font-medium text-zinc-300">It&apos;s quiet in here...</p>
              <p className="mt-2 text-sm text-zinc-500">
                Upload or Select a document, audio, or video file to get started.
              </p>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}