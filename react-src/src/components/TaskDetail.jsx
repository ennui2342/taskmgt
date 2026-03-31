import { useState, useEffect } from 'react'
import { stripTokens, annotations } from '../api'
import { useUpdateTask, useDeleteTask } from '../hooks'

function Chip({ children, color }) {
  const colors = {
    tag:      'bg-indigo-900/60 text-indigo-300',
    location: 'bg-emerald-900/60 text-emerald-300',
    agent:    'bg-purple-900/60 text-purple-300',
  }
  return (
    <span className={`rounded px-1.5 py-0.5 text-xs ${colors[color] ?? colors.tag}`}>
      {children}
    </span>
  )
}

function Prop({ label, children }) {
  return (
    <div className="flex gap-4 py-1.5 text-sm">
      <dt className="w-24 flex-shrink-0 text-gray-500">{label}</dt>
      <dd className="text-gray-200">{children}</dd>
    </div>
  )
}

const PRIORITY_LABEL = { 1: 'High', 2: 'Medium', 3: 'Low' }

function EditForm({ selected, onDone }) {
  const [text, setText] = useState(selected.text)
  const updateTask = useUpdateTask()

  async function handleSubmit(e) {
    e.preventDefault()
    await updateTask.mutateAsync({ id: selected.id, text })
    onDone()
  }

  return (
    <form className="detail-edit-form flex flex-col gap-4 p-6" onSubmit={handleSubmit}>
      <textarea
        className="detail-edit-input w-full rounded bg-gray-800 p-3 text-sm text-gray-100 outline-none ring-1 ring-gray-600 focus:ring-indigo-500"
        rows={5}
        value={text}
        onChange={e => setText(e.target.value)}
        autoFocus
      />
      <div className="flex gap-2">
        <button
          type="submit"
          className="btn-save rounded bg-indigo-700 px-4 py-1.5 text-sm font-medium text-white hover:bg-indigo-600"
        >
          Save
        </button>
        <button
          type="button"
          className="btn-cancel rounded px-4 py-1.5 text-sm text-gray-400 hover:bg-gray-700 hover:text-gray-100"
          onClick={onDone}
        >
          Cancel
        </button>
      </div>
    </form>
  )
}

export default function TaskDetail({ selected, onDeselect }) {
  const [editing, setEditing] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const deleteTask = useDeleteTask()

  // Reset state when selection changes
  useEffect(() => { setEditing(false); setConfirming(false) }, [selected?.id])

  if (!selected) {
    return (
      <div className="detail-empty flex flex-1 items-center justify-center">
        <p className="text-sm text-gray-500">Select a task to view details.</p>
      </div>
    )
  }

  if (editing) {
    return <EditForm selected={selected} onDone={() => setEditing(false)} />
  }

  return (
    <div className="p-6">
      <div className="detail-header mb-4 flex items-start justify-between gap-4">
        <h2 className="text-base font-semibold leading-snug text-gray-100">
          {stripTokens(selected.text)}
        </h2>
        <div className="flex flex-shrink-0 items-center gap-2">
          {!confirming ? (
            <>
              <button
                className="btn-edit rounded px-3 py-1 text-xs text-gray-400 ring-1 ring-gray-600 hover:bg-gray-700 hover:text-gray-100"
                onClick={() => setEditing(true)}
              >
                Edit
              </button>
              <button
                className="btn-delete rounded px-3 py-1 text-xs text-gray-400 ring-1 ring-gray-600 hover:bg-red-900/50 hover:text-red-300 hover:ring-red-800"
                onClick={() => setConfirming(true)}
              >
                Delete
              </button>
            </>
          ) : (
            <>
              <span className="text-xs text-gray-400">Delete?</span>
              <button
                className="btn-delete-confirm rounded bg-red-700 px-3 py-1 text-xs font-medium text-white hover:bg-red-600"
                onClick={async () => { await deleteTask.mutateAsync(selected.id); onDeselect?.() }}
              >
                Yes
              </button>
              <button
                className="btn-cancel rounded px-3 py-1 text-xs text-gray-400 ring-1 ring-gray-600 hover:bg-gray-700"
                onClick={() => setConfirming(false)}
              >
                Cancel
              </button>
            </>
          )}
        </div>
      </div>

      <dl className="detail-props divide-y divide-gray-800">
        <Prop label="Status">{selected.status}</Prop>
        {selected.priority && (
          <Prop label="Priority">
            <span className={selected.priority === 1 ? 'text-red-400' : selected.priority === 2 ? 'text-amber-400' : 'text-blue-400'}>
              {PRIORITY_LABEL[selected.priority]}
            </span>
          </Prop>
        )}
        {selected.due && (
          <Prop label="Due">{selected.due.slice(0, 16).replace('T', ' ')}</Prop>
        )}
        {selected.duration && (
          <Prop label="Duration">{selected.duration}</Prop>
        )}
        {selected.tags?.length > 0 && (
          <Prop label="Tags">
            <div className="flex flex-wrap gap-1">
              {selected.tags.map(t => <Chip key={t} color="tag">#{t}</Chip>)}
            </div>
          </Prop>
        )}
        {selected.location && (
          <Prop label="Location"><Chip color="location">@{selected.location}</Chip></Prop>
        )}
        {selected.assignee_agent && (
          <Prop label="Assigned to"><Chip color="agent">+{selected.assignee_agent}</Chip></Prop>
        )}
        {selected.assignee_human && (
          <Prop label="Assignee">{selected.assignee_human}</Prop>
        )}
        <Prop label="Created">{selected.created_at.slice(0, 16).replace('T', ' ')}</Prop>
      </dl>

      {(() => {
        const notes = annotations(selected.text)
        return notes.length > 0 ? (
          <div className="mt-6">
            <div className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-500">Notes</div>
            <ul className="space-y-1.5">
              {notes.map((note, i) => (
                <li key={i} className="whitespace-pre-wrap rounded bg-gray-800 px-3 py-2 text-sm text-gray-300">
                  {note}
                </li>
              ))}
            </ul>
          </div>
        ) : null
      })()}

      <div className="detail-full-text mt-6">
        <div className="mb-1 text-xs font-medium uppercase tracking-wider text-gray-500">Raw text</div>
        <code className="block whitespace-pre-wrap rounded bg-gray-800 p-3 text-xs text-gray-300">
          {selected.text}
        </code>
      </div>
    </div>
  )
}
