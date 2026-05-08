import { ChevronRight, ChevronDown, Folder, MoreVertical, Trash2, Edit3 } from 'lucide-react'
import { useState } from 'react'
import type { FileSystemItem } from './types'

type FolderNodeProps = {
  item: FileSystemItem
  depth: number
  isSelected: boolean
  onSelect: (id: string) => void
  onToggle: (id: string) => void
  onMoveSelectedFileHere: (folderId: string) => void
  canMoveSelectedFile: boolean
  onRename: (id: string, currentName: string) => Promise<void> | void
  onDelete: (id: string) => Promise<void> | void
}

export default function FolderNode({
  item,
  depth,
  isSelected,
  onSelect,
  onToggle,
  onMoveSelectedFileHere,
  canMoveSelectedFile,
  onRename,
  onDelete,
}: FolderNodeProps) {
  const [isHovering, setIsHovering] = useState(false)
  const [showMenu, setShowMenu] = useState(false)

  return (
    <div
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => {
        setIsHovering(false)
        setShowMenu(false)
      }}
      className="relative"
    >
      <div
        onClick={() => onSelect(item.id)}
        style={{ paddingLeft: `${depth * 1 + 0.75}rem` }}
        className={`flex w-full cursor-pointer items-center gap-3 rounded-lg border px-3 py-2 text-left transition-none ${
          isSelected
            ? 'border-fuchsia-500 bg-zinc-800 text-purple-400'
            : 'border-transparent text-zinc-300 hover:bg-zinc-800/50'
        }`}
      >
        <button
          type="button"
          onClick={() => onToggle(item.id)}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded hover:bg-zinc-700"
          aria-label={item.isOpen ? 'Collapse folder' : 'Expand folder'}
        >
          {item.isOpen ? (
            <ChevronDown className="h-4 w-4 text-zinc-500" />
          ) : (
            <ChevronRight className="h-4 w-4 text-zinc-500" />
          )}
        </button>

        <div className="flex h-8 w-8 shrink-0 items-center justify-center">
          <Folder className="h-4 w-4 text-zinc-400" />
        </div>

        <div className="min-w-0 flex-1 max-w-45 truncate text-sm font-medium">{item.name}</div>

        {isHovering && (
          <div className="relative ml-auto">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                setShowMenu(!showMenu)
              }}
              className="flex h-6 w-6 items-center justify-center rounded text-zinc-400 hover:bg-zinc-700 hover:text-white"
              aria-label="More options"
            >
              <MoreVertical className="h-4 w-4" />
            </button>

            {showMenu && (
              <div className="absolute right-0 top-8 z-50 w-48 rounded-lg border border-zinc-700 bg-zinc-800 py-1 shadow-lg">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    onMoveSelectedFileHere(item.id)
                    setShowMenu(false)
                  }}
                  disabled={!canMoveSelectedFile}
                  className="flex w-full items-center gap-3 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-700 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <ChevronRight className="h-4 w-4" />
                  Move selected file here
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    void onRename(item.id, item.name)
                    setShowMenu(false)
                  }}
                  className="flex w-full items-center gap-3 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-700 hover:text-white"
                >
                  <Edit3 className="h-4 w-4" />
                  Rename
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    void onDelete(item.id)
                    setShowMenu(false)
                  }}
                  className="flex w-full items-center gap-3 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-700 hover:text-red-400"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
