import { useState } from 'react'
import { useCreateTask } from '../hooks'

export default function SmartAddBar({ seed = '' }) {
  const [text, setText] = useState('')
  const createTask = useCreateTask()

  async function handleSubmit(e) {
    e.preventDefault()
    const trimmed = text.trim()
    if (!trimmed) return
    // Append seed tokens not already present in the text
    const seedTokens = seed.split(/\s+/).filter(Boolean)
    const extra = seedTokens.filter(tok => !trimmed.includes(tok)).join(' ')
    await createTask.mutateAsync(extra ? `${trimmed} ${extra}` : trimmed)
    setText('')
  }

  return (
    <form
      className="smartadd-bar flex gap-2 border-b border-gray-700 p-2"
      onSubmit={handleSubmit}
    >
      <input
        className="smartadd-input flex-1 rounded bg-gray-800 px-3 py-1.5 text-sm text-gray-100 placeholder-gray-500 outline-none ring-1 ring-gray-700 focus:ring-indigo-500"
        type="text"
        placeholder="Add task… !1 #tag @location ^due =30m"
        autoComplete="off"
        value={text}
        onChange={e => setText(e.target.value)}
      />
      <button
        type="submit"
        className="btn-add rounded bg-indigo-700 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-600"
      >
        Add
      </button>
    </form>
  )
}
