import { useEffect, useState } from 'react'
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

export default function App() {
  const [activeFile, setActiveFile] = useState<FileSystemItem | null>(null)
  const [tree, setTree] = useState<FileSystemItem[]>([])
  const [isLoadingFiles, setIsLoadingFiles] = useState(true)
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [uploadTargetFolderId, setUploadTargetFolderId] = useState<string | null>(null)
  const [mode, setMode] = useState<'chat' | 'summary'>('chat')
  const [currentSeekTime, setCurrentSeekTime] = useState<number>(0)
  const [uploadQueue, setUploadQueue] = useState<UploadQueueItem[]>([])

  useEffect(() => {
    setCurrentSeekTime(0)
  }, [activeFile?.id])

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
    <div className="flex h-screen w-full text-white">
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