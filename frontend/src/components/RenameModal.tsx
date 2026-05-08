import { useState } from 'react'

type RenameModalProps = {
  isOpen: boolean
  currentName: string
  onClose: () => void
  onConfirm: (newName: string) => Promise<void>
}

export default function RenameModal({ isOpen, currentName, onClose, onConfirm }: RenameModalProps) {
  const [value, setValue] = useState(currentName)
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-xl border border-zinc-800 bg-zinc-900 p-6">
        <h3 className="mb-3 text-lg font-medium">Rename file</h3>
        <input
          className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-white outline-none"
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />

        <div className="mt-4 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-800"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={async () => {
              if (!value.trim()) return
              setIsSubmitting(true)
              try {
                await onConfirm(value.trim())
                onClose()
              } catch {
                // swallow and allow caller to show alert
              } finally {
                setIsSubmitting(false)
              }
            }}
            className="rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50"
            disabled={isSubmitting}
          >
            Rename
          </button>
        </div>
      </div>
    </div>
  )
}
