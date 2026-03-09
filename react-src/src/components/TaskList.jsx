import { stripTokens } from '../api'

const PRIORITY_BG = {
  1: 'bg-red-500',
  2: 'bg-amber-500',
  3: 'bg-blue-500',
}

function Chip({ children, color }) {
  const colors = {
    tag:      'bg-indigo-900/60 text-indigo-300',
    location: 'bg-emerald-900/60 text-emerald-300',
    agent:    'bg-purple-900/60 text-purple-300',
    due:      'bg-amber-900/60 text-amber-300',
  }
  return (
    <span className={`rounded px-1.5 py-0.5 text-xs ${colors[color] ?? colors.tag}`}>
      {children}
    </span>
  )
}

function TaskRow({ task, isSelected, onSelect }) {
  return (
    <li
      id={`task-${task.id}`}
      className={`task-row flex cursor-pointer border-b border-gray-800 transition-colors ${
        isSelected
          ? 'selected bg-indigo-900/30 text-white'
          : 'text-gray-300 hover:bg-gray-800/60 hover:text-gray-100'
      }`}
      onClick={() => onSelect(task.id)}
    >
      <div className={`w-1 flex-shrink-0 ${PRIORITY_BG[task.priority] ?? 'bg-transparent'}`} />
      <div className="flex flex-col px-3 py-2.5">
      <span className="task-text text-sm leading-snug">
        {stripTokens(task.text)}
      </span>
      {(task.tags?.length > 0 || task.location || task.assignee_agent || task.due) && (
        <div className="task-meta mt-1 flex flex-wrap gap-1">
          {task.tags?.map(t => <Chip key={t} color="tag">#{t}</Chip>)}
          {task.location    && <Chip color="location">@{task.location}</Chip>}
          {task.assignee_agent && <Chip color="agent">+{task.assignee_agent}</Chip>}
          {task.due         && <Chip color="due">{task.due.slice(0, 10)}</Chip>}
        </div>
      )}
      </div>
    </li>
  )
}

export default function TaskList({ tasks, selectedId, onSelect, isLoading }) {
  if (isLoading) {
    return (
      <ul className="task-list flex-1 overflow-y-auto">
        {[...Array(4)].map((_, i) => (
          <li key={i} className="h-12 animate-pulse border-b border-gray-800 bg-gray-800/40" />
        ))}
      </ul>
    )
  }

  return (
    <ul className="task-list flex-1 overflow-y-auto">
      {tasks.length === 0 ? (
        <li className="task-empty px-4 py-6 text-center text-sm text-gray-500">
          No tasks here.
        </li>
      ) : (
        tasks.map(task => (
          <TaskRow
            key={task.id}
            task={task}
            isSelected={task.id === selectedId}
            onSelect={onSelect}
          />
        ))
      )}
    </ul>
  )
}
