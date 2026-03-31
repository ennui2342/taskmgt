import { useState } from 'react'
import { useCloseTask, useDeleteTask } from '../hooks'

function ToggleSwitch({ checked, onChange }) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      onClick={onChange}
      className={`relative inline-flex h-4 w-7 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none ${
        checked ? 'bg-indigo-600' : 'bg-gray-600'
      }`}
    >
      <span className={`pointer-events-none inline-block h-3 w-3 transform rounded-full bg-white shadow transition duration-200 ${
        checked ? 'translate-x-3' : 'translate-x-0'
      }`} />
    </button>
  )
}

export default function ActionBar({ selected, activeFilter, onDeselect, showClosed, onToggleClosed, hideClosedToggle }) {
  const [confirming, setConfirming] = useState(false)
  const closeTask  = useCloseTask()
  const deleteTask = useDeleteTask()

  // Reset confirm state when selection changes
  if (!selected && confirming) setConfirming(false)

  if (!selected) {
    return (
      <div className="action-bar-empty flex h-12 items-center border-b border-gray-700 px-4">
        {activeFilter != null && (
          <span className="font-mono text-xs text-gray-400">
            Task Filter: {activeFilter || 'all tasks'}
          </span>
        )}
        {!hideClosedToggle && (
          <div className="ml-auto flex items-center gap-2">
            <span className="text-xs text-gray-500">closed</span>
            <ToggleSwitch checked={showClosed} onChange={onToggleClosed} />
          </div>
        )}
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
      {selected.status !== 'closed' && (
        <button
          className="btn-close rounded bg-indigo-700 px-3 py-1 text-xs font-medium text-white hover:bg-indigo-600"
          onClick={async () => {
            await closeTask.mutateAsync({ id: selected.id, text: selected.text })
            onDeselect()
          }}
        >
          ✓ Close task
        </button>
      )}
      <button
        className="btn-delete ml-auto rounded px-3 py-1 text-xs text-gray-400 hover:bg-red-900/50 hover:text-red-300"
        onClick={() => setConfirming(true)}
      >
        Delete
      </button>
    </div>
  )
}
