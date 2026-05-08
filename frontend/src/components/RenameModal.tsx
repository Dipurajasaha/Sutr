import { useEffect, useState } from 'react'

type RenameModalProps = {
  isOpen: boolean
  title?: string
  currentName?: string
  message?: string
  confirmLabel?: string
  cancelLabel?: string
  requireInput?: boolean
  danger?: boolean
  onClose: () => void
  onConfirm: (value?: string) => Promise<void> | void
}

export default function RenameModal({
  isOpen,
  title = 'Rename file',
  currentName = '',
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  requireInput = true,
  danger = false,
  onClose,
  onConfirm,
}: RenameModalProps) {
  const [value, setValue] = useState(currentName)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setValue(currentName)
    }
  }, [isOpen, currentName])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-xl border border-zinc-800 bg-zinc-900 p-6">
        <h3 className="mb-3 text-lg font-medium">{title}</h3>

        {message ? <p className="mb-3 text-sm text-zinc-300">{message}</p> : null}

        {requireInput ? (
          <input
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-white outline-none"
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />
        ) : null}

        <div className="mt-4 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-800"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={async () => {
              if (requireInput && !value.trim()) return
              setIsSubmitting(true)
              try {
                await onConfirm(requireInput ? value.trim() : undefined)
                onClose()
              } catch {
                // swallow and allow caller to show alert
              } finally {
                setIsSubmitting(false)
              }
            }}
            className={`rounded-md px-4 py-2 text-sm font-medium text-white disabled:opacity-50 ${
              danger ? 'bg-red-600 hover:bg-red-700' : 'bg-purple-600 hover:bg-purple-700'
            }`}
            disabled={isSubmitting}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
