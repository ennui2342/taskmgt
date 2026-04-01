import { useState, useEffect, useRef } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { useTasks, useTask, useFilters } from '../hooks'
import { viewToFilter } from '../api'
import ActionBar from './ActionBar'
import SmartAddBar from './SmartAddBar'
import TaskList from './TaskList'
import TaskDetail from './TaskDetail'

export default function MainPanel({ favourite, mobile, selectedId: controlledId, onTaskSelect, onDeselect }) {
  const { view = 'all', idx } = useParams()
  const [searchParams] = useSearchParams()
  const tag      = searchParams.get('tag')
  const location = searchParams.get('location')
  const taskParam = searchParams.get('task')

  const [_selectedId, _setSelectedId] = useState(() => taskParam ? parseInt(taskParam) : null)
  const selectedId = mobile ? controlledId : _selectedId
  const [showClosed, setShowClosed] = useState(false)

  const isFirstRender = useRef(true)
  useEffect(() => {
    if (isFirstRender.current) { isFirstRender.current = false; return }
    _setSelectedId(null); setShowClosed(false)
  }, [view, tag, location, idx])

  const { data: favs = [] } = useFilters()

  const favFilter = favourite && idx !== undefined ? favs[parseInt(idx)]?.filter : undefined

  const { data: tasks = [], isLoading } = useTasks(
    favourite ? 'favourite' : view,
    tag,
    location,
    favFilter,
    showClosed,
  )
  const { data: selected } = useTask(selectedId)

  const EXCLUDE_TOKENS = new Set(['^inbox', '^overdue'])
  const seed = favourite
    ? (favFilter?.match(/[!#@^=][^\s()]+|\+\+?[^\s()]+/g) ?? [])
        .filter(tok => !EXCLUDE_TOKENS.has(tok))
        .join(' ')
    : view === 'tag' && tag ? `#${tag}`
    : view === 'location' && location ? `@${location}`
    : ''

  function handleSelect(id) {
    if (mobile) {
      onTaskSelect?.(id)
    } else {
      _setSelectedId(prev => (prev === id ? null : id))
    }
  }

  const activeFilter = favourite ? (favFilter ?? '') : null

  return (
    <div className="flex flex-1 overflow-hidden">
      <div className={`flex flex-col border-r border-gray-700 bg-gray-900 ${mobile ? 'flex-1' : 'w-80 flex-shrink-0'}`}>
        {!mobile && (
          <ActionBar
            selected={selected}
            activeFilter={activeFilter}
            onDeselect={() => _setSelectedId(null)}
            showClosed={showClosed}
            onToggleClosed={() => { setShowClosed(v => !v); _setSelectedId(null) }}
            hideClosedToggle={['closed', 'wait', 'started', 'overdue', 'inbox', 'today'].includes(view)}
          />
        )}
        {view !== 'closed' && !showClosed && <SmartAddBar seed={seed} />}
        <TaskList
          tasks={tasks}
          selectedId={selectedId}
          onSelect={handleSelect}
          isLoading={isLoading}
        />
      </div>
      {!mobile && (
        <div className="detail-panel flex flex-1 flex-col overflow-y-auto bg-gray-850">
          <TaskDetail selected={selected} onDeselect={() => _setSelectedId(null)} />
        </div>
      )}
    </div>
  )
}
