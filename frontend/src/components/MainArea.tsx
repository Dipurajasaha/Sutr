import { MessageSquareText, NotebookText } from 'lucide-react'
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

  const hasMediaFile = !!activeFile && (activeFile.fileType === 'video' || activeFile.fileType === 'audio')
  // Use API Gateway to serve uploads so we don't have CORS issues in production
  // Prefer backend stored file path (safe filename) if available
  let fileUrl = ''
  if (activeFile) {
    const stored = activeFile.filePath ? (activeFile.filePath.split(/[\\/]/).pop() ?? activeFile.name) : activeFile.name
    fileUrl = buildUploadUrl(stored)
  }

  return (
    <section className="flex h-full flex-col overflow-hidden bg-zinc-950 text-white">
      <header className="flex h-16 shrink-0 items-center justify-between border-b border-zinc-800 px-6">
        <div className="min-w-0 pr-4 text-sm font-medium text-white truncate">{activeFileName}</div>

        <div className="inline-flex rounded-full border border-zinc-800 bg-zinc-900 p-1">
          <button
            type="button"
            onClick={() => onModeChange('chat')}
            className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium ${
              mode === 'chat' ? 'bg-purple-600 text-white' : 'bg-zinc-800 text-zinc-300'
            }`}
          >
            <MessageSquareText className="h-4 w-4" />
            Chat
          </button>
          <button
            type="button"
            onClick={() => onModeChange('summary')}
            className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium ${
              mode === 'summary' ? 'bg-purple-600 text-white' : 'bg-zinc-800 text-zinc-300'
            }`}
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
        {mode === 'chat' ? (
          <ChatView key={activeFile?.id ?? 'no-file'} activeFile={activeFile} onCitationClick={onCitationClick} />
        ) : (
          <SummaryView key={activeFile?.id ?? 'no-file'} activeFile={activeFile} />
        )}
      </div>
    </section>
  )
}