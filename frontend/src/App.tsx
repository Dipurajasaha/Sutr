import { useEffect, useState } from 'react'
import MainArea from './components/MainArea'
import Sidebar from './components/Sidebar'
import UploadModal, { type UploadedFileResponse } from './components/UploadModal'
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

export default function App() {
  const [activeFile, setActiveFile] = useState<FileSystemItem | null>(null)
  const [tree, setTree] = useState<FileSystemItem[]>([])
  const [isLoadingFiles, setIsLoadingFiles] = useState(true)
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [mode, setMode] = useState<'chat' | 'summary'>('chat')
  const [currentSeekTime, setCurrentSeekTime] = useState<number>(0)

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

  const handleUploadSuccess = (uploadedFile: UploadedFileResponse) => {
    const newFile: FileSystemItem = {
      id: uploadedFile.id,
      name: uploadedFile.filename,
      type: 'file',
      fileType: mapBackendFileType(uploadedFile.file_type),
    }

    setTree((prev) => [newFile, ...prev])
    setActiveFile(newFile)
    setIsUploadModalOpen(false)
  }

  function mapBackendFileType(fileType: string): 'pdf' | 'video' | 'audio' {
    if (fileType === 'video') return 'video'
    if (fileType === 'audio') return 'audio'
    return 'pdf'
  }

  const handleDeleteFile = async (fileId: string) => {
    try {
      await apiClient.delete(`/api/files/${fileId}`)
      setTree((prev) => prev.filter((item) => item.id !== fileId))
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
      setTree((prev) =>
        prev.map((item) =>
          item.id === fileId
            ? { ...item, name: response.data.filename }
            : item
        )
      )
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
          onOpenUpload={() => setIsUploadModalOpen(true)}
          onDeleteFile={handleDeleteFile}
          onRenameFile={handleRenameFile}
          isLoadingFiles={isLoadingFiles}
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
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />
    </div>
  )
}