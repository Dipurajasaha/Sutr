import type { Dispatch, SetStateAction } from 'react'
import type { RefObject } from 'react'
import { useEffect, useState } from 'react'
import { FolderPlus, UploadCloud, Loader, Inbox, Search } from 'lucide-react'
import FolderNode from './FolderNode'
import FileNode from './FileNode'
import type { FileSystemItem } from './types'
import RenameModal from './RenameModal'

type UploadQueueItem = {
  clientId: string
  name: string
  progress: number
  status: 'queued' | 'uploading' | 'processing' | 'completed' | 'failed'
  errorMessage?: string
}

type SidebarProps = {
  activeFileId: string | null
  tree: FileSystemItem[]
  setTree: Dispatch<SetStateAction<FileSystemItem[]>>
  onSelectFile: (item: FileSystemItem) => void
  onOpenUpload: (targetFolderId?: string) => void
  onDeleteFile: (fileId: string) => Promise<void>
  onRenameFile: (fileId: string, newName: string) => Promise<void>
  isLoadingFiles?: boolean
  uploadQueue: UploadQueueItem[]
  logoAnchorRef?: RefObject<HTMLDivElement | null>
}

export default function Sidebar({
  activeFileId,
  tree,
  setTree,
  onSelectFile,
  onOpenUpload,
  onDeleteFile,
  onRenameFile,
  isLoadingFiles = false,
  uploadQueue,
  logoAnchorRef,
}: SidebarProps) {
  const toggleFolder = (id: string) => {
    setTree((prev) => toggleFolderRecursive(prev, id))
  }

  const findItemByIdRecursive = (items: FileSystemItem[], targetId: string): FileSystemItem | null => {
    for (const item of items) {
      if (item.id === targetId) {
        return item
      }
      if (item.type === 'folder' && item.children) {
        const found = findItemByIdRecursive(item.children, targetId)
        if (found) {
          return found
        }
      }
    }
    return null
  }

  const renameItemRecursive = (items: FileSystemItem[], targetId: string, newName: string): FileSystemItem[] => {
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

  const deleteItemRecursive = (items: FileSystemItem[], targetId: string): FileSystemItem[] => {
    const next: FileSystemItem[] = []
    for (const item of items) {
      if (item.id === targetId) {
        continue
      }

      if (item.type === 'folder' && item.children) {
        next.push({ ...item, children: deleteItemRecursive(item.children, targetId) })
      } else {
        next.push(item)
      }
    }
    return next
  }

  const removeFileRecursive = (
    items: FileSystemItem[],
    targetId: string,
  ): { nextItems: FileSystemItem[]; removedFile: FileSystemItem | null } => {
    const nextItems: FileSystemItem[] = []
    let removedFile: FileSystemItem | null = null

    for (const item of items) {
      if (item.id === targetId && item.type === 'file') {
        removedFile = item
        continue
      }

      if (item.type === 'folder' && item.children) {
        const result = removeFileRecursive(item.children, targetId)
        if (result.removedFile) {
          removedFile = result.removedFile
        }
        nextItems.push({ ...item, children: result.nextItems })
      } else {
        nextItems.push(item)
      }
    }

    return { nextItems, removedFile }
  }

  const insertFileIntoFolderRecursive = (
    items: FileSystemItem[],
    folderId: string,
    fileItem: FileSystemItem,
  ): FileSystemItem[] => {
    return items.map((item) => {
      if (item.id === folderId && item.type === 'folder') {
        const children = item.children ?? []
        return { ...item, isOpen: true, children: [fileItem, ...children] }
      }

      if (item.type === 'folder' && item.children) {
        return {
          ...item,
          children: insertFileIntoFolderRecursive(item.children, folderId, fileItem),
        }
      }

      return item
    })
  }

  const insertFolderIntoFolderRecursive = (
    items: FileSystemItem[],
    folderId: string,
    newFolder: FileSystemItem,
  ): FileSystemItem[] => {
    return items.map((item) => {
      if (item.id === folderId && item.type === 'folder') {
        const children = item.children ?? []
        return { ...item, isOpen: true, children: [newFolder, ...children] }
      }

      if (item.type === 'folder' && item.children) {
        return {
          ...item,
          children: insertFolderIntoFolderRecursive(item.children, folderId, newFolder),
        }
      }

      return item
    })
  }

  const toggleFolderRecursive = (items: FileSystemItem[], targetId: string): FileSystemItem[] => {
    return items.map((item) => {
      if (item.id === targetId && item.type === 'folder') {
        return { ...item, isOpen: !item.isOpen }
      }
      if (item.type === 'folder' && item.children) {
        return { ...item, children: toggleFolderRecursive(item.children, targetId) }
      }
      return item
    })
  }

  const [renameOpen, setRenameOpen] = useState(false)
  const [renameTargetId, setRenameTargetId] = useState<string | null>(null)
  const [renameTargetName, setRenameTargetName] = useState<string>('')
  const [createFolderOpen, setCreateFolderOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null)
  const [deleteTargetName, setDeleteTargetName] = useState<string>('')
  const [deleteTargetType, setDeleteTargetType] = useState<'file' | 'folder' | null>(null)
  const [uiMessage, setUiMessage] = useState<string>('')
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState<string>('')

  const renameItem = (id: string, currentName: string) => {
    setRenameTargetId(id)
    setRenameTargetName(currentName)
    setRenameOpen(true)
  }

  const selectFolder = (folderId: string) => {
    setSelectedFolderId(folderId)
    setUiMessage('')
  }

  const deleteItem = (id: string) => {
    const target = findItemByIdRecursive(tree, id)
    if (!target) {
      return
    }

    setDeleteTargetId(target.id)
    setDeleteTargetName(target.name)
    setDeleteTargetType(target.type)
    setDeleteDialogOpen(true)
  }

  const confirmDeleteItem = async () => {
    if (!deleteTargetId || !deleteTargetType) {
      return
    }

    try {
      if (deleteTargetType === 'folder') {
        setTree((prev) => deleteItemRecursive(prev, deleteTargetId))
        if (selectedFolderId === deleteTargetId) {
          setSelectedFolderId(null)
        }
        return
      }

      await onDeleteFile(deleteTargetId)
    } catch (error) {
      setUiMessage('Failed to delete item. Please try again.')
      console.error('Delete error:', error)
      throw error
    }
  }

  const handleConfirmRename = async (newName?: string) => {
    const normalizedName = (newName ?? '').trim()
    if (!normalizedName) {
      return
    }

    if (!renameTargetId) return
    try {
      const target = findItemByIdRecursive(tree, renameTargetId)
      if (!target) {
        return
      }

      if (target.type === 'folder') {
        setTree((prev) => renameItemRecursive(prev, renameTargetId, normalizedName))
        return
      }

      await onRenameFile(renameTargetId, normalizedName)
    } catch (error) {
      setUiMessage('Failed to rename item. Please try again.')
      console.error('Rename error:', error)
      throw error
    }
  }

  const handleCreateFolder = async (folderName?: string) => {
    const name = (folderName ?? '').trim()
    if (!name) {
      return
    }

    const newFolder: FileSystemItem = {
      id: `folder-${crypto.randomUUID()}`,
      name,
      type: 'folder',
      isOpen: true,
      children: [],
    }

    setTree((prev) => {
      if (!selectedFolderId) {
        return [newFolder, ...prev]
      }
      return insertFolderIntoFolderRecursive(prev, selectedFolderId, newFolder)
    })
  }

  const moveSelectedFileIntoFolder = (folderId: string) => {
    if (!activeFileId) {
      setUiMessage('Select a file first, then choose a destination folder.')
      return
    }

    const selected = findItemByIdRecursive(tree, activeFileId)
    if (!selected || selected.type !== 'file') {
      setUiMessage('Select a file first, then choose a destination folder.')
      return
    }

    setTree((prev) => {
      const removal = removeFileRecursive(prev, activeFileId)
      if (!removal.removedFile) {
        return prev
      }

      return insertFileIntoFolderRecursive(removal.nextItems, folderId, removal.removedFile)
    })
  }

  useEffect(() => {
    if (!selectedFolderId) {
      return
    }

    if (!findItemByIdRecursive(tree, selectedFolderId)) {
      setSelectedFolderId(null)
    }
  }, [tree, selectedFolderId])

  const activeUploads = uploadQueue.filter(
    (item) => item.status === 'queued' || item.status === 'uploading' || item.status === 'processing',
  )
  const uploadPanelItems = activeUploads.length > 0 ? activeUploads : uploadQueue
  const hasFailedUploads = uploadQueue.some((item) => item.status === 'failed')
  const averageProgress =
    uploadPanelItems.length > 0
      ? Math.round(uploadPanelItems.reduce((sum, item) => sum + item.progress, 0) / uploadPanelItems.length)
      : 0

  const filteredTree = (items: FileSystemItem[]): FileSystemItem[] => {
    if (!searchQuery.trim()) return items
    return items.filter((item) => {
      const matchesSearch = item.name.toLowerCase().includes(searchQuery.toLowerCase())
      if (item.type === 'folder' && item.children) {
        const hasMatchingChildren = filteredTree(item.children).length > 0
        return matchesSearch || hasMatchingChildren
      }
      return matchesSearch
    })
  }

  const sortedItems = (items: FileSystemItem[]): FileSystemItem[] => {
    const folders = items.filter((item) => item.type === 'folder').sort((a, b) => a.name.localeCompare(b.name))
    const files = items.filter((item) => item.type === 'file').sort((a, b) => a.name.localeCompare(b.name))
    return [...folders, ...files]
  }

  const renderTree = (items: FileSystemItem[], depth: number = 0) => {
    const filtered = filteredTree(items)
    return sortedItems(filtered).map((item) => {
      if (item.type === 'folder') {
        return (
          <div key={item.id}>
            <FolderNode
              item={item}
              depth={depth}
              onSelect={selectFolder}
              onToggle={toggleFolder}
              onMoveSelectedFileHere={moveSelectedFileIntoFolder}
              canMoveSelectedFile={!!activeFileId}
              onRename={renameItem}
              onDelete={deleteItem}
            />
            {item.isOpen && item.children && renderTree(item.children, depth + 1)}
          </div>
        )
      } else {
        return (
          <FileNode
            key={item.id}
            item={item}
            depth={depth}
            isActive={activeFileId === item.id}
            onSelect={(fileItem) => {
              setSelectedFolderId(null)
              onSelectFile(fileItem)
            }}
            onRename={renameItem}
            onDelete={deleteItem}
            fileName={item.name}
          />
        )
      }
    })
  }

  return (
    <aside className="flex h-full w-full min-h-0 flex-col border-r border-zinc-800 bg-zinc-900 text-white">
      <div className="space-y-3 p-5">
        <div ref={logoAnchorRef} className="text-2xl font-bold tracking-tight text-white leading-none">
          Sutr AI
        </div>

        <button
          type="button"
          onClick={() => onOpenUpload(selectedFolderId ?? undefined)}
          className="flex w-full items-center justify-center gap-2 rounded-2xl bg-purple-600 px-4 py-3 font-semibold text-white shadow-[0_10px_30px_rgba(168,85,247,0.18)] transition-all duration-200 hover:-translate-y-0.5 hover:bg-purple-500 hover:shadow-[0_14px_36px_rgba(168,85,247,0.24)] active:translate-y-0 disabled:opacity-50"
          disabled={isLoadingFiles}
        >
          <UploadCloud className="h-4 w-4" />
          + Upload New File
        </button>

        <button
          type="button"
          onClick={() => {
            setUiMessage('')
            setCreateFolderOpen(true)
          }}
          className="flex w-full items-center justify-center gap-2 rounded-2xl border border-zinc-700 bg-zinc-800 px-4 py-3 font-semibold text-zinc-300 transition-all duration-200 hover:-translate-y-0.5 hover:border-zinc-600 hover:bg-zinc-700 hover:text-white active:translate-y-0"
        >
          <FolderPlus className="h-4 w-4" />
          + New Folder
        </button>

        {uiMessage ? <p className="text-xs text-red-400">{uiMessage}</p> : null}
      </div>
      
      <RenameModal
        isOpen={renameOpen}
        title="Rename item"
        currentName={renameTargetName}
        confirmLabel="Rename"
        onClose={() => setRenameOpen(false)}
        onConfirm={handleConfirmRename}
      />

      <RenameModal
        isOpen={createFolderOpen}
        title="Create New Folder"
        currentName=""
        confirmLabel="Create"
        onClose={() => setCreateFolderOpen(false)}
        onConfirm={handleCreateFolder}
      />

      <RenameModal
        isOpen={deleteDialogOpen}
        title={`Delete ${deleteTargetType ?? 'item'}`}
        message={`Are you sure you want to delete "${deleteTargetName}"?`}
        requireInput={false}
        confirmLabel="Delete"
        danger
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={confirmDeleteItem}
      />

      <div className="space-y-3 px-3 pb-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search documents..."
            className="w-full rounded-lg border border-zinc-700 bg-zinc-800 py-2 pl-10 pr-3 text-sm text-white outline-none placeholder:text-zinc-500 focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
          />
        </div>
        <div className="text-xs font-medium uppercase tracking-[0.2em] text-zinc-500">
          Document Manager
        </div>
      </div>

      <div className="relative z-10 flex-1 overflow-y-auto px-2 pb-4 pt-2">
        {isLoadingFiles ? (
          <div className="flex items-center justify-center gap-2 py-8 text-zinc-500">
            <Loader className="h-4 w-4 animate-spin" />
            <span>Loading files...</span>
          </div>
        ) : tree.length === 0 ? (
          <div className="flex min-h-72 flex-col items-center justify-center px-6 py-10 text-center">
            <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-3xl border border-zinc-800 bg-zinc-900/80 shadow-[0_0_0_1px_rgba(39,39,42,0.6)]">
              <Inbox className="h-10 w-10 text-zinc-600" />
            </div>
            <p className="text-lg font-medium text-zinc-300">It&apos;s quiet in here...</p>
            <p className="mt-2 max-w-xs text-sm text-zinc-500">
              Upload or Select a document, audio, or video file to get started.
            </p>
          </div>
        ) : (
          <div className="space-y-1">{renderTree(tree)}</div>
        )}
      </div>

      {uploadQueue.length > 0 ? (
        <div className="border-t border-zinc-800 p-3">
          <div className="group relative rounded-xl border border-zinc-800 bg-zinc-950/70 p-3 transition-colors duration-200 hover:border-zinc-700 hover:bg-zinc-950">
            <div className="mb-2 flex items-center justify-between gap-3 text-xs">
              <span className="font-medium text-zinc-200">
                {activeUploads.length > 0
                  ? `${activeUploads.length} file${activeUploads.length > 1 ? 's' : ''} uploading`
                  : hasFailedUploads
                    ? 'Upload finished with errors'
                    : 'Upload complete'}
              </span>
              <span className="text-zinc-400">{averageProgress}%</span>
            </div>

            <div className="h-2 overflow-hidden rounded-full bg-zinc-800">
              <div
                className={`h-full transition-all duration-300 ${hasFailedUploads ? 'bg-red-500' : 'bg-purple-500'}`}
                style={{ width: `${averageProgress}%` }}
              />
            </div>

            <div className="pointer-events-none absolute bottom-full left-0 right-0 mb-2 max-h-56 overflow-y-auto rounded-xl border border-zinc-700 bg-zinc-900 p-2 opacity-0 shadow-2xl transition-opacity duration-150 group-hover:pointer-events-auto group-hover:opacity-100">
              {uploadQueue.map((item) => (
                <div
                  key={item.clientId}
                  className="mb-2 last:mb-0 rounded-lg border border-zinc-800 bg-zinc-950/70 p-2 transition-all duration-200 hover:-translate-y-0.5 hover:border-zinc-700 hover:bg-zinc-900"
                >
                  <div className="mb-1 truncate text-xs font-medium text-zinc-200">{item.name}</div>
                  <div className="mb-1 h-1.5 overflow-hidden rounded-full bg-zinc-800">
                    <div
                      className={`h-full transition-all duration-300 ${item.status === 'failed' ? 'bg-red-500' : 'bg-purple-500'}`}
                      style={{ width: `${item.progress}%` }}
                    />
                  </div>
                  <div className="text-[11px] text-zinc-400">
                    {item.status === 'processing'
                      ? 'Analyzing'
                      : item.status === 'uploading'
                        ? 'Uploading'
                        : item.status === 'completed'
                          ? 'Completed'
                          : item.status === 'failed'
                            ? item.errorMessage ?? 'Failed'
                            : 'Queued'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </aside>
  )
}