import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useCounts, useTags, useLocations, useFilters, useCreateFilter, useDeleteFilter, useTaskCount } from '../hooks'

function Badge({ count, urgent }) {
  if (!count) return null
  return (
    <span className={`ml-auto rounded px-1.5 py-0.5 text-xs font-medium ${
      urgent ? 'bg-red-800 text-red-200' : 'bg-gray-700 text-gray-300'
    }`}>
      {count}
    </span>
  )
}

function NavItem({ to, label, badge, urgent }) {
  const { pathname, search } = useLocation()
  const current = pathname + search
  const isActive = current === to || (pathname === to && !search)

  return (
    <div className={`nav-item ${isActive ? 'active' : ''} flex items-center`}>
      <Link
        to={to}
        className={`flex flex-1 items-center gap-2 rounded px-3 py-1.5 text-sm transition-colors ${
          isActive
            ? 'border-l-2 border-indigo-500 bg-indigo-600/25 pl-[10px] text-white'
            : 'text-gray-400 hover:bg-gray-800 hover:text-gray-100'
        }`}
      >
        {label}
      </Link>
      <Badge count={badge} urgent={urgent} />
      <div className="w-5 flex-shrink-0" />
    </div>
  )
}

function SectionHeading({ label, onAdd }) {
  return (
    <div className="mb-1 mt-4 flex items-center justify-between px-3">
      <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">{label}</span>
      {onAdd && (
        <button
          onClick={onAdd}
          className="filter-add-btn rounded p-0.5 text-gray-500 hover:bg-gray-800 hover:text-gray-300"
          title="Add filter"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
          </svg>
        </button>
      )}
    </div>
  )
}

function AddFilterForm({ onDone }) {
  const [name, setName] = useState('')
  const [filter, setFilter] = useState('')
  const createFilter = useCreateFilter()

  async function handleSubmit(e) {
    e.preventDefault()
    if (!name.trim() || !filter.trim()) return
    await createFilter.mutateAsync({ name: name.trim(), filter: filter.trim() })
    onDone()
  }

  function handleKeyDown(e) {
    if (e.key === 'Escape') onDone()
  }

  return (
    <form
      className="filter-add-form mx-1 mb-1 flex flex-col gap-1 rounded bg-gray-800 p-2"
      onSubmit={handleSubmit}
      onKeyDown={handleKeyDown}
    >
      <input
        className="filter-add-name rounded bg-gray-700 px-2 py-1 text-xs text-gray-100 outline-none ring-1 ring-gray-600 focus:ring-indigo-500"
        placeholder="Name"
        value={name}
        onChange={e => setName(e.target.value)}
        autoFocus
      />
      <input
        className="filter-add-filter rounded bg-gray-700 px-2 py-1 text-xs text-gray-100 outline-none ring-1 ring-gray-600 focus:ring-indigo-500"
        placeholder="Filter  e.g. #tag !1"
        value={filter}
        onChange={e => setFilter(e.target.value)}
      />
      <div className="flex gap-1">
        <button
          type="submit"
          className="filter-add-submit flex-1 rounded bg-indigo-700 py-1 text-xs font-medium text-white hover:bg-indigo-600"
        >
          Add
        </button>
        <button
          type="button"
          className="filter-add-cancel rounded px-2 py-1 text-xs text-gray-400 hover:bg-gray-700 hover:text-gray-100"
          onClick={onDone}
        >
          Cancel
        </button>
      </div>
    </form>
  )
}

function FilterNavItem({ to, label, idx, filter }) {
  const { pathname, search } = useLocation()
  const current = pathname + search
  const isActive = current === to || (pathname === to && !search)
  const deleteFilter = useDeleteFilter()
  const count = useTaskCount(filter)

  return (
    <div className={`nav-item group flex items-center ${isActive ? 'active' : ''}`}>
      <Link
        to={to}
        className={`flex flex-1 items-center gap-2 rounded px-3 py-1.5 text-sm transition-colors ${
          isActive
            ? 'border-l-2 border-indigo-500 bg-indigo-600/25 pl-[10px] text-white'
            : 'text-gray-400 hover:bg-gray-800 hover:text-gray-100'
        }`}
      >
        {label}
      </Link>
      <Badge count={count} />
      <button
        onClick={() => deleteFilter.mutate(idx)}
        className="mr-1 rounded p-0.5 text-gray-600 opacity-0 hover:bg-gray-800 hover:text-gray-400 group-hover:opacity-100"
        title="Remove filter"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>
    </div>
  )
}

export default function Sidebar() {
  const { data: counts = {} }   = useCounts()
  const { data: tags = [] }     = useTags()
  const { data: locs = [] }     = useLocations()
  const { data: filters = [] }  = useFilters()
  const [addingFilter, setAddingFilter] = useState(false)

  return (
    <nav className="flex w-full flex-shrink-0 flex-col gap-0.5 overflow-y-auto bg-gray-950 px-2 py-4 md:w-52">
      <div className="mb-4 px-3 text-lg font-semibold tracking-tight text-indigo-400">
        aswarm
      </div>

      <NavItem to="/view/inbox"   label="Inbox"     badge={counts.inbox}   />
      <NavItem to="/view/all"     label="All Tasks"  badge={counts.all}    />
      <NavItem to="/view/today"   label="Today"     badge={counts.today}   />
      <NavItem to="/view/overdue" label="Overdue"   badge={counts.overdue} urgent />

      <SectionHeading label="Filters" onAdd={() => setAddingFilter(true)} />
      {addingFilter && <AddFilterForm onDone={() => setAddingFilter(false)} />}
      {filters.map((f, i) => (
        <FilterNavItem key={i} to={`/favourite/${i}`} label={f.name} idx={i} filter={f.filter} />
      ))}

      {tags.length > 0 && (
        <>
          <SectionHeading label="Tags" />
          <div className="nav-section">
            {tags.map(t => (
              <NavItem
                key={t.tag}
                to={`/view/tag?tag=${encodeURIComponent(t.tag)}`}
                label={`#${t.tag}`}
                badge={t.count}
              />
            ))}
          </div>
        </>
      )}

      {locs.length > 0 && (
        <>
          <SectionHeading label="Locations" />
          <div className="nav-section">
            {locs.map(l => (
              <NavItem
                key={l.location}
                to={`/view/location?location=${encodeURIComponent(l.location)}`}
                label={`@${l.location}`}
                badge={l.count}
              />
            ))}
          </div>
        </>
      )}
    </nav>
  )
}
