import { useCloseTask } from '../hooks'

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
  const closeTask = useCloseTask()

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
      {!hideClosedToggle && (
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs text-gray-500">closed</span>
          <ToggleSwitch checked={showClosed} onChange={onToggleClosed} />
        </div>
      )}
    </div>
  )
}
