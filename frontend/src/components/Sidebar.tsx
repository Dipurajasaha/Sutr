import type { Dispatch, SetStateAction } from 'react'
import { useState } from 'react'
import { FolderPlus, UploadCloud, Loader } from 'lucide-react'
import FolderNode from './FolderNode'
import FileNode from './FileNode'
import type { FileSystemItem } from './types'
import RenameModal from './RenameModal'

type SidebarProps = {
  activeFileId: string | null
  tree: FileSystemItem[]
  setTree: Dispatch<SetStateAction<FileSystemItem[]>>
  onSelectFile: (item: FileSystemItem) => void
  onOpenUpload: () => void
  onDeleteFile: (fileId: string) => Promise<void>
  onRenameFile: (fileId: string, newName: string) => Promise<void>
  isLoadingFiles?: boolean
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
}: SidebarProps) {
  const toggleFolder = (id: string) => {
    setTree((prev) => toggleFolderRecursive(prev, id))
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

  const renameItem = (id: string, currentName: string) => {
    setRenameTargetId(id)
    setRenameTargetName(currentName)
    setRenameOpen(true)
  }

  const deleteItem = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this item?')) {
      try {
        await onDeleteFile(id)
      } catch (error) {
        window.alert('Failed to delete file. Please try again.')
        console.error('Delete error:', error)
      }
    }
  }

  const handleConfirmRename = async (newName: string) => {
    if (!renameTargetId) return
    try {
      await onRenameFile(renameTargetId, newName)
    } catch (error) {
      window.alert('Failed to rename file. Please try again.')
      console.error('Rename error:', error)
      throw error
    }
  }

  const renderTree = (items: FileSystemItem[], depth: number = 0) => {
    return items.map((item) => {
      if (item.type === 'folder') {
        return (
          <div key={item.id}>
            <FolderNode
              item={item}
              depth={depth}
              onToggle={toggleFolder}
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
            onSelect={onSelectFile}
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
        <div className="text-2xl font-bold tracking-tight text-white">Sutr AI</div>

        <button
          type="button"
          onClick={onOpenUpload}
          className="flex w-full items-center justify-center gap-2 rounded-2xl bg-purple-600 px-4 py-3 font-semibold text-white hover:bg-purple-700 disabled:opacity-50"
          disabled={isLoadingFiles}
        >
          <UploadCloud className="h-4 w-4" />
          + Upload New File
        </button>

        <button
          type="button"
          onClick={() => {
            const name = window.prompt('Enter folder name:')
            if (name?.trim()) {
              const newFolder: FileSystemItem = {
                id: `folder-${crypto.randomUUID()}`,
                name: name.trim(),
                type: 'folder',
                isOpen: true,
                children: [],
              }
              setTree((prev) => [newFolder, ...prev])
            }
          }}
          className="flex w-full items-center justify-center gap-2 rounded-2xl border border-zinc-700 bg-zinc-800 px-4 py-3 font-semibold text-zinc-300 hover:bg-zinc-700 hover:text-white"
        >
          <FolderPlus className="h-4 w-4" />
          + New Folder
        </button>
      </div>
      
      <RenameModal
        key={`${renameTargetId ?? 'none'}-${renameOpen ? 'open' : 'closed'}`}
        isOpen={renameOpen}
        currentName={renameTargetName}
        onClose={() => setRenameOpen(false)}
        onConfirm={handleConfirmRename}
      />

      <div className="px-3 pb-3 text-xs font-medium uppercase tracking-[0.2em] text-zinc-500">
        Files & Folders
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-4">
        {isLoadingFiles ? (
          <div className="flex items-center justify-center gap-2 py-8 text-zinc-500">
            <Loader className="h-4 w-4 animate-spin" />
            <span>Loading files...</span>
          </div>
        ) : tree.length === 0 ? (
          <div className="py-8 text-center text-zinc-500">
            <p>No files yet</p>
            <p className="mt-2 text-xs">Upload a file to get started</p>
          </div>
        ) : (
          <div className="space-y-1">{renderTree(tree)}</div>
        )}
      </div>
    </aside>
  )
}