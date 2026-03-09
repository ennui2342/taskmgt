import { useState } from 'react'
import { useCloseTask, useDeleteTask } from '../hooks'

export default function ActionBar({ selected, activeFilter, onDeselect }) {
  const [confirming, setConfirming] = useState(false)
  const closeTask  = useCloseTask()
  const deleteTask = useDeleteTask()

  // Reset confirm state when selection changes
  if (!selected && confirming) setConfirming(false)

  if (!selected) {
    return (
      <div className="action-bar-empty flex h-12 items-center border-b border-gray-700 px-4">
        <span className="font-mono text-xs text-gray-400">
          Task Filter: {activeFilter || 'all tasks'}
        </span>
      </div>
    )
  }

  if (confirming) {
    return (
      <div className="flex h-12 items-center gap-2 border-b border-gray-700 px-3">
        <span className="text-sm text-gray-400">Delete this task?</span>
        <button
          className="btn-delete-confirm ml-auto rounded bg-red-700 px-3 py-1 text-xs font-medium text-white hover:bg-red-600"
          onClick={async () => {
            await deleteTask.mutateAsync(selected.id)
            onDeselect()
          }}
        >
          Yes, delete
        </button>
        <button
          className="rounded px-3 py-1 text-xs text-gray-400 hover:bg-gray-700 hover:text-gray-100"
          onClick={() => setConfirming(false)}
        >
          Cancel
        </button>
      </div>
    )
  }

  return (
    <div className="flex h-12 items-center gap-2 border-b border-gray-700 px-3">
      <button
        className="btn-close rounded bg-indigo-700 px-3 py-1 text-xs font-medium text-white hover:bg-indigo-600"
        onClick={async () => {
          await closeTask.mutateAsync(selected.id)
          onDeselect()
        }}
      >
        ✓ Close task
      </button>
      <button
        className="btn-delete ml-auto rounded px-3 py-1 text-xs text-gray-400 hover:bg-red-900/50 hover:text-red-300"
        onClick={() => setConfirming(true)}
      >
        Delete
      </button>
    </div>
  )
}
