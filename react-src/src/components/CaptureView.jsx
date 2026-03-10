import { useState, useRef, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useCreateTask, useTags, useLocations } from '../hooks'

const STATIC = {
  '!': ['!1', '!2', '!3'],
  '^': ['^today', '^tomorrow', '^+1w'],
  '=': ['=15m', '=30m', '=1h', '=2h'],
}

export default function CaptureView() {
  const [text, setText] = useState('')
  const [added, setAdded] = useState(false)
  const inputRef = useRef(null)
  const createTask = useCreateTask()
  const { data: tags = [] } = useTags()
  const { data: locs = [] } = useLocations()

  const lastToken = text.split(/\s+/).at(-1) ?? ''

  const suggestions = useMemo(() => {
    if (!lastToken) return []
    const prefix = lastToken[0]
    const q = lastToken.slice(1).toLowerCase()
    if (prefix === '#') {
      const all = tags.map(t => `#${t.tag}`)
      return q ? all.filter(s => s.slice(1).startsWith(q)) : all
    }
    if (prefix === '@') {
      const all = locs.map(l => `@${l.location}`)
      return q ? all.filter(s => s.slice(1).startsWith(q)) : all
    }
    if (STATIC[prefix]) return STATIC[prefix].filter(s => s.startsWith(lastToken))
    return []
  }, [lastToken, tags, locs])

  function applySuggestion(s) {
    const parts = text.trimEnd().split(/\s+/)
    parts[parts.length - 1] = s
    setText(parts.join(' ') + ' ')
    inputRef.current?.focus()
  }

  function insertToken(tok) {
    setText(prev => (prev.trimEnd() ? prev.trimEnd() + ' ' + tok : tok))
    inputRef.current?.focus()
  }

  async function handleSubmit(e) {
    e?.preventDefault()
    const trimmed = text.trim()
    if (!trimmed) return
    await createTask.mutateAsync(trimmed)
    setText('')
    setAdded(true)
    setTimeout(() => setAdded(false), 1500)
    inputRef.current?.focus()
  }

  return (
    <div className="capture-view flex h-dvh flex-col gap-3 bg-gray-950 px-4 py-4 text-gray-100">
      {/* Header */}
      <div className="flex flex-shrink-0 items-center justify-between">
        <span className="text-lg font-semibold text-indigo-400">aswarm</span>
        <Link to="/view/all" className="rounded px-2 py-1 text-sm text-gray-500 hover:text-gray-300">
          ← Tasks
        </Link>
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex-shrink-0">
        <input
          ref={inputRef}
          autoFocus
          type="text"
          className="capture-input w-full rounded-xl bg-gray-800 px-4 py-3.5 text-xl text-gray-100 placeholder-gray-600 outline-none ring-1 ring-gray-700 focus:ring-indigo-500"
          placeholder="Add task…"
          autoComplete="off"
          autoCorrect="off"
          autoCapitalize="sentences"
          value={text}
          onChange={e => setText(e.target.value)}
        />
      </form>

      {/* Autocomplete suggestions */}
      {suggestions.length > 0 && (
        <div className="capture-suggestions flex-shrink-0 flex gap-2 overflow-x-auto pb-1">
          {suggestions.slice(0, 8).map(s => (
            <button
              key={s}
              type="button"
              onClick={() => applySuggestion(s)}
              className="whitespace-nowrap rounded-full bg-gray-800 px-3 py-1.5 text-sm text-indigo-300 active:bg-gray-700"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Token buttons */}
      <div className="capture-tokens flex flex-shrink-0 gap-2">
        {[
          { tok: '!', cls: 'text-red-400' },
          { tok: '#', cls: 'text-indigo-400' },
          { tok: '@', cls: 'text-green-400' },
          { tok: '^', cls: 'text-yellow-400' },
          { tok: '=', cls: 'text-purple-400' },
        ].map(({ tok, cls }) => (
          <button
            key={tok}
            type="button"
            onClick={() => insertToken(tok)}
            className={`flex-1 rounded-xl bg-gray-800 py-3 font-mono text-xl font-bold active:bg-gray-700 ${cls}`}
          >
            {tok}
          </button>
        ))}
      </div>

      {/* Add button */}
      <div className="flex flex-shrink-0 items-center gap-3">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!text.trim() || createTask.isPending}
          className="btn-add flex-1 rounded-xl bg-indigo-700 py-3.5 text-base font-semibold text-white active:bg-indigo-800 disabled:opacity-40"
        >
          {createTask.isPending ? 'Adding…' : 'Add'}
        </button>
        {added && (
          <span className="capture-added text-sm text-green-400">✓ Added</span>
        )}
      </div>
    </div>
  )
}
