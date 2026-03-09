import { useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { useTasks, useTask, useFilters } from '../hooks'
import { viewToFilter } from '../api'
import ActionBar from './ActionBar'
import SmartAddBar from './SmartAddBar'
import TaskList from './TaskList'
import TaskDetail from './TaskDetail'

export default function MainPanel({ favourite }) {
  const { view = 'all', idx } = useParams()
  const [searchParams] = useSearchParams()
  const tag      = searchParams.get('tag')
  const location = searchParams.get('location')

  const [selectedId, setSelectedId] = useState(null)

  const { data: favs = [] } = useFilters()

  // For favourite views, derive a filter string from the favourites list
  const favFilter = favourite && idx !== undefined ? favs[parseInt(idx)]?.filter : undefined

  const { data: tasks = [], isLoading } = useTasks(
    favourite ? 'favourite' : view,
    tag,
    location,
    favFilter,
  )
  const { data: selected } = useTask(selectedId)

  // Pre-seed new tasks with context tokens from the current view.
  // ^inbox and ^overdue are view-only filters with no task text equivalent; exclude them.
  const EXCLUDE_TOKENS = new Set(['^inbox', '^overdue'])
  const seed = favourite
    ? (favFilter?.match(/[!#@^=][^\s]+|\+\+?[^\s]+/g) ?? [])
        .filter(tok => !EXCLUDE_TOKENS.has(tok))
        .join(' ')
    : view === 'tag' && tag ? `#${tag}`
    : view === 'location' && location ? `@${location}`
    : ''

  function handleSelect(id) {
    setSelectedId(prev => (prev === id ? null : id))
  }

  return (
    <div className="flex flex-1 overflow-hidden">
      <div className="flex w-80 flex-shrink-0 flex-col border-r border-gray-700 bg-gray-900">
        <ActionBar
          selected={selected}
          activeFilter={favourite ? (favFilter ?? '') : viewToFilter(view, tag, location)}
          onDeselect={() => setSelectedId(null)}
        />
        <SmartAddBar seed={seed} />
        <TaskList
          tasks={tasks}
          selectedId={selectedId}
          onSelect={handleSelect}
          isLoading={isLoading}
        />
      </div>
      <div className="detail-panel flex flex-1 flex-col overflow-y-auto bg-gray-850">
        <TaskDetail selected={selected} onDeselect={() => setSelectedId(null)} />
      </div>
    </div>
  )
}
