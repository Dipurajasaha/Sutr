import { useEffect, useRef, useState } from 'react'
import MainArea from './components/MainArea'
import Sidebar from './components/Sidebar'
import UploadModal, {
  type UploadQueueStatus,
  type UploadQueueUpdate,
  type UploadedFileResponse,
} from './components/UploadModal'
import { apiClient } from './api/client'
import type { FileSystemItem } from './components/types'

declare global {
  interface Window {
    __sutrTestHooks?: {
      setCitationTime: (seconds: number) => void
    }
  }
}

type BackendFile = {
  id: string
  filename: string
  file_type: string
  file_path: string
  status: string
  created_at: string
}

export type UploadQueueItem = {
  clientId: string
  name: string
  progress: number
  status: UploadQueueStatus
  errorMessage?: string
  updatedAt: number
}

function removeItemRecursive(items: FileSystemItem[], targetId: string): FileSystemItem[] {
  const next: FileSystemItem[] = []

  for (const item of items) {
    if (item.id === targetId) {
      continue
    }

    if (item.type === 'folder' && item.children) {
      next.push({ ...item, children: removeItemRecursive(item.children, targetId) })
    } else {
      next.push(item)
    }
  }

  return next
}

function renameItemRecursive(items: FileSystemItem[], targetId: string, newName: string): FileSystemItem[] {
  return items.map((item) => {
    if (item.id === targetId) {
      return { ...item, name: newName }
    }

    if (item.type === 'folder' && item.children) {
      return { ...item, children: renameItemRecursive(item.children, targetId, newName) }
    }

    return item
  })
}

function hasFolderRecursive(items: FileSystemItem[], folderId: string): boolean {
  for (const item of items) {
    if (item.id === folderId && item.type === 'folder') {
      return true
    }

    if (item.type === 'folder' && item.children && hasFolderRecursive(item.children, folderId)) {
      return true
    }
  }

  return false
}

function insertFileIntoFolderRecursive(items: FileSystemItem[], folderId: string, newFile: FileSystemItem): FileSystemItem[] {
  return items.map((item) => {
    if (item.id === folderId && item.type === 'folder') {
      const children = item.children ?? []
      return { ...item, isOpen: true, children: [newFile, ...children] }
    }

    if (item.type === 'folder' && item.children) {
      return { ...item, children: insertFileIntoFolderRecursive(item.children, folderId, newFile) }
    }

    return item
  })
}

function ScrambleSubtitle() {
  const text = 'Unlock the knowledge inside your documents, audio, and video.'
  const scrambleChars = '!<>-_\\/[]{}—=+*^?#________'

  const [displayedText, setDisplayedText] = useState('')

  useEffect(() => {
    const revealIntervalMs = Math.max(30, Math.floor(1800 / text.length))
    const holdTimeoutMs = 3000
    let revealIndex = 0
    let holdTimeoutId: number | null = null

    const buildScrambledText = (lockedCount: number) => {
      return text
        .split('')
        .map((char, index) => {
          if (char === ' ') {
            return ' '
          }

          if (index < lockedCount) {
            return char
          }

          return scrambleChars[Math.floor(Math.random() * scrambleChars.length)]
        })
        .join('')
    }

    setDisplayedText(buildScrambledText(0))

    const intervalId = window.setInterval(() => {
      revealIndex += 1

      if (revealIndex >= text.length) {
        window.clearInterval(intervalId)
        setDisplayedText(text)

        holdTimeoutId = window.setTimeout(() => {
          holdTimeoutId = null
        }, holdTimeoutMs)

        return
      }

      setDisplayedText(buildScrambledText(revealIndex))
    }, revealIntervalMs)

    return () => {
      window.clearInterval(intervalId)

      if (holdTimeoutId !== null) {
        window.clearTimeout(holdTimeoutId)
      }
    }
  }, [])

  return (
    <p className="mt-6 mb-8 px-4 text-lg leading-relaxed text-zinc-300">
      <span className="inline-block whitespace-pre-wrap font-mono tracking-[0.14em] text-zinc-200">
        {displayedText}
      </span>
    </p>
  )
}

export default function App() {
  const [activeFile, setActiveFile] = useState<FileSystemItem | null>(null)
  const [tree, setTree] = useState<FileSystemItem[]>([])
  const [isLoadingFiles, setIsLoadingFiles] = useState(true)
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [uploadTargetFolderId, setUploadTargetFolderId] = useState<string | null>(null)
  const [mode, setMode] = useState<'chat' | 'summary'>('chat')
  const [currentSeekTime, setCurrentSeekTime] = useState<number>(0)
  const [uploadQueue, setUploadQueue] = useState<UploadQueueItem[]>([])
  const [hasStarted, setHasStarted] = useState(false)
  const [isWelcomeTransitioning, setIsWelcomeTransitioning] = useState(false)
  const [logoTarget, setLogoTarget] = useState<{ left: number; top: number } | null>(null)
  const logoAnchorRef = useRef<HTMLDivElement | null>(null)
  const welcomeMoveTimeoutRef = useRef<number | null>(null)

  const welcomeTransitionDurationMs = 700

  useEffect(() => {
    const updateLogoTarget = () => {
      const rect = logoAnchorRef.current?.getBoundingClientRect()
      if (!rect) {
        return
      }

      setLogoTarget({
        left: rect.left,
        top: rect.top,
      })
    }

    updateLogoTarget()
    window.addEventListener('resize', updateLogoTarget)

    return () => {
      window.removeEventListener('resize', updateLogoTarget)
    }
  }, [])

  useEffect(() => {
    return () => {
      if (welcomeMoveTimeoutRef.current) {
        window.clearTimeout(welcomeMoveTimeoutRef.current)
      }
    }
  }, [])

  useEffect(() => {
    setCurrentSeekTime(0)
  }, [activeFile?.id])

  const handleStart = () => {
    setHasStarted(true)
    setIsWelcomeTransitioning(true)

    if (welcomeMoveTimeoutRef.current) {
      window.clearTimeout(welcomeMoveTimeoutRef.current)
    }

    welcomeMoveTimeoutRef.current = window.setTimeout(() => {
      setIsWelcomeTransitioning(false)
    }, welcomeTransitionDurationMs)
  }

  // Fetch files from backend on component mount
  useEffect(() => {
    const fetchFiles = async () => {
      try {
        setIsLoadingFiles(true)
        const response = await apiClient.get<BackendFile[]>('/api/files/')
        const mappedFiles: FileSystemItem[] = response.data.map((file) => ({
          id: file.id,
          name: file.filename,
          type: 'file',
          fileType: mapBackendFileType(file.file_type),
          filePath: file.file_path,
        }))
        setTree(mappedFiles)
      } catch (error) {
        console.error('Failed to fetch files:', error)
        // Fallback to empty tree on error
        setTree([])
      } finally {
        setIsLoadingFiles(false)
      }
    }

    void fetchFiles()
  }, [])

  const handleUploadSuccess = (uploadedFile: UploadedFileResponse, targetFolderId: string | null) => {
    const newFile: FileSystemItem = {
      id: uploadedFile.id,
      name: uploadedFile.filename,
      type: 'file',
      fileType: mapBackendFileType(uploadedFile.file_type),
      filePath: uploadedFile.file_path,
    }

    setTree((prev) => {
      if (!targetFolderId) {
        return [newFile, ...prev]
      }

      if (!hasFolderRecursive(prev, targetFolderId)) {
        return [newFile, ...prev]
      }

      return insertFileIntoFolderRecursive(prev, targetFolderId, newFile)
    })
    setActiveFile(newFile)
  }

  const handleUploadQueueUpdate = (update: UploadQueueUpdate) => {
    const now = Date.now()
    setUploadQueue((prev) => {
      const existingIndex = prev.findIndex((item) => item.clientId === update.clientId)
      const nextItem: UploadQueueItem = {
        clientId: update.clientId,
        name: update.name,
        progress: update.progress,
        status: update.status,
        errorMessage: update.errorMessage,
        updatedAt: now,
      }

      if (existingIndex === -1) {
        return [...prev, nextItem]
      }

      return prev.map((item, index) => (index === existingIndex ? nextItem : item))
    })
  }

  useEffect(() => {
    const interval = window.setInterval(() => {
      const now = Date.now()
      setUploadQueue((prev) =>
        prev.filter((item) => {
          if (item.status !== 'completed') {
            return true
          }

          return now - item.updatedAt < 5000
        }),
      )
    }, 1000)

    return () => window.clearInterval(interval)
  }, [])

  function mapBackendFileType(fileType: string): 'pdf' | 'video' | 'audio' {
    if (fileType === 'video') return 'video'
    if (fileType === 'audio') return 'audio'
    return 'pdf'
  }
////////////////////////////////////////////////////////////////////////////////////
  
////////////////////////////////////////////////////////////////////////////////////
  const handleDeleteFile = async (fileId: string) => {
    try {
      await apiClient.delete(`/api/files/${fileId}`)
      setTree((prev) => removeItemRecursive(prev, fileId))
      if (activeFile?.id === fileId) {
        setActiveFile(null)
      }
    } catch (error) {
      console.error('Failed to delete file:', error)
      throw error
    }
  }

  const handleRenameFile = async (fileId: string, newName: string) => {
    try {
      const response = await apiClient.patch<BackendFile>(`/api/files/${fileId}`, {
        filename: newName,
      })
      setTree((prev) => renameItemRecursive(prev, fileId, response.data.filename))
      if (activeFile?.id === fileId) {
        setActiveFile((prev) => (prev ? { ...prev, name: response.data.filename } : null))
      }
    } catch (error) {
      console.error('Failed to rename file:', error)
      throw error
    }
  }

  useEffect(() => {
    if (!import.meta.env.DEV) return

    window.__sutrTestHooks = {
      setCitationTime: (seconds: number) => setCurrentSeekTime(seconds),
    }

    return () => {
      if (window.__sutrTestHooks?.setCitationTime) {
        delete window.__sutrTestHooks
      }
    }
  }, [])

  return (
    <div className="relative flex h-screen w-full text-white">
      {!hasStarted || isWelcomeTransitioning ? (
        <>
          <div
            className={`fixed inset-0 z-50 bg-zinc-950 transition-opacity duration-700 ease-in-out ${
              hasStarted ? 'opacity-0' : 'opacity-100'
            }`}
          />

          <div
            className={`fixed inset-0 z-60 flex items-center justify-center transition-opacity duration-700 ease-in-out ${
              hasStarted ? 'opacity-0' : 'opacity-100'
            }`}
          >
            <div className="mt-40 flex flex-col items-center text-center">
              <ScrambleSubtitle />

              <button
                type="button"
                onClick={handleStart}
                className="relative rounded-xl bg-purple-600 px-8 py-4 text-lg font-semibold text-white shadow-lg shadow-purple-900/50 transition-all duration-300 hover:bg-purple-500 hover:-translate-y-1.5 hover:shadow-2xl hover:shadow-purple-500/60 active:translate-y-0"
              >
                Get Started
              </button>
            </div>
          </div>

          <div
            className={`fixed z-50 select-none whitespace-nowrap font-bold tracking-tight text-white transition-[left,top,font-size,transform,opacity] duration-700 ease-in-out ${
              hasStarted
                ? 'text-2xl leading-none opacity-100'
                : 'left-1/2 top-1/2 text-7xl leading-none opacity-100 md:text-8xl'
            }`}
            style={{
              left: hasStarted && logoTarget ? `${logoTarget.left}px` : '50%',
              top: hasStarted && logoTarget ? `${logoTarget.top}px` : '50%',
              transform: hasStarted ? 'translate(0, 0)' : 'translate(-50%, -78%)',
            }}
          >
            Sutr AI
          </div>
        </>
      ) : null}

      <div
        className={`flex h-full w-full transition-opacity duration-700 ease-in-out ${
          hasStarted && !isWelcomeTransitioning ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
      >
        <div className="w-1/3 shrink-0">
          <Sidebar
            activeFileId={activeFile?.id ?? null}
            tree={tree}
            setTree={setTree}
            onSelectFile={setActiveFile}
            onOpenUpload={(targetFolderId?: string) => {
              setUploadTargetFolderId(targetFolderId ?? null)
              setIsUploadModalOpen(true)
            }}
            onDeleteFile={handleDeleteFile}
            onRenameFile={handleRenameFile}
            isLoadingFiles={isLoadingFiles}
            uploadQueue={uploadQueue}
            logoAnchorRef={logoAnchorRef}
          />
        </div>

        <div className="w-2/3 min-w-0">
          <MainArea
            activeFile={activeFile}
            mode={mode}
            onModeChange={setMode}
            currentSeekTime={currentSeekTime}
            onCitationClick={(start) => setCurrentSeekTime(start)}
          />
        </div>
      </div>

      <UploadModal
        isOpen={isUploadModalOpen}
        onClose={() => {
          setUploadTargetFolderId(null)
          setIsUploadModalOpen(false)
        }}
        onUploadSuccess={handleUploadSuccess}
        onUploadQueueUpdate={handleUploadQueueUpdate}
        targetFolderId={uploadTargetFolderId}
      />
    </div>
  )
}