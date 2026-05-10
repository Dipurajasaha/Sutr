import { FileText, Headphones, MoreVertical, Trash2, Edit3, Video } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import type { FileSystemItem } from './types'

type FileNodeProps = {
  item: FileSystemItem
  depth: number
  isActive: boolean
  onSelect: (item: FileSystemItem) => void
  onRename: (id: string, currentName: string) => Promise<void> | void
  onDelete: (id: string) => Promise<void> | void
  fileName?: string
}

const fileIconMap = {
  pdf: FileText,
  video: Video,
  audio: Headphones,
} as const

const fileIconStyleMap = {
  pdf: {
    icon: 'text-red-400',
    glow: 'bg-red-400/10',
  },
  video: {
    icon: 'text-blue-400',
    glow: 'bg-blue-400/10',
  },
  audio: {
    icon: 'text-emerald-400',
    glow: 'bg-emerald-400/10',
  },
} as const

export default function FileNode({
  item,
  depth,
  isActive,
  onSelect,
  onRename,
  onDelete,
  fileName,
}: FileNodeProps) {
  const [isHovering, setIsHovering] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const actionsRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!showMenu) {
      return
    }

    const handlePointerDown = (event: PointerEvent) => {
      if (actionsRef.current?.contains(event.target as Node)) {
        return
      }

      setShowMenu(false)
    }

    document.addEventListener('pointerdown', handlePointerDown)

    return () => {
      document.removeEventListener('pointerdown', handlePointerDown)
    }
  }, [showMenu])

  const Icon = item.fileType ? fileIconMap[item.fileType] : FileText
  const iconStyle = item.fileType ? fileIconStyleMap[item.fileType] : fileIconStyleMap.pdf
  const displayName = fileName || item.name

  return (
    <div
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      className="group relative"
    >
      <div
        onClick={() => onSelect(item)}
        style={{ paddingLeft: `${depth * 1 + 0.75}rem` }}
        className={`flex w-full cursor-pointer items-center gap-3 rounded-lg border border-transparent px-3 py-2 text-left transition-all duration-200 hover:-translate-y-1 hover:shadow-lg hover:shadow-purple-500/10 hover:border-zinc-700 ${
          isActive
            ? 'border-fuchsia-500 bg-zinc-800 text-purple-400'
            : 'text-zinc-300 hover:bg-zinc-800/50 hover:text-white'
        }`}
      >
        <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${iconStyle.glow}`}>
          <Icon className={`h-4 w-4 ${iconStyle.icon} transition-transform duration-200 group-hover:scale-105`} />
        </div>

        <div className="min-w-0 flex-1 truncate text-sm font-medium">{displayName}</div>

        {(isHovering || showMenu) && (
          <div ref={actionsRef} className="relative ml-auto">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                setShowMenu((currentValue) => !currentValue)
              }}
              className="flex h-6 w-6 items-center justify-center rounded text-zinc-400 transition-colors duration-200 hover:bg-zinc-700 hover:text-white"
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
                    void onRename(item.id, displayName)
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
