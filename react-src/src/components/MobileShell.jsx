import { useState, useEffect, useRef, useCallback } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import MainPanel from './MainPanel'
import TaskDetail from './TaskDetail'
import { useTask, useCloseTask, useDeleteTask } from '../hooks'

export default function MobileShell() {
  const [pane, setPane] = useState(0)
  const [selectedId, setSelectedId] = useState(null)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const location = useLocation()
  const prevPath = useRef(location.pathname + location.search)
  const containerRef = useRef(null)
  const touchStartX = useRef(0)
  const touchStartY = useRef(0)
  const closeTask = useCloseTask()
  const deleteTask = useDeleteTask()

  const { data: selected } = useTask(selectedId)

  // Advance to task list when route changes (sidebar nav tap)
  useEffect(() => {
    const curr = location.pathname + location.search
    if (curr !== prevPath.current) {
      setPane(1)
      setSelectedId(null)
      prevPath.current = curr
    }
  }, [location])

  function handleTaskSelect(id) {
    setSelectedId(id)
    setConfirmDelete(false)
    setPane(2)
  }

  function handleDeselect() {
    setSelectedId(null)
    setPane(1)
  }

  const onTouchStart = useCallback(e => {
    touchStartX.current = e.touches[0].clientX
    touchStartY.current = e.touches[0].clientY
  }, [])

  const onTouchEnd = useCallback(e => {
    const dx = e.changedTouches[0].clientX - touchStartX.current
    const dy = e.changedTouches[0].clientY - touchStartY.current
    if (dx > 60 && Math.abs(dx) > Math.abs(dy) * 1.5 && pane > 0) {
      setPane(p => p - 1)
    }
  }, [pane])

  // Register as passive listeners so the browser can scroll without waiting
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    el.addEventListener('touchstart', onTouchStart, { passive: true })
    el.addEventListener('touchend', onTouchEnd, { passive: true })
    return () => {
      el.removeEventListener('touchstart', onTouchStart)
      el.removeEventListener('touchend', onTouchEnd)
    }
  }, [onTouchStart, onTouchEnd])

  return (
    <div
      ref={containerRef}
      className="mobile-shell h-dvh overflow-hidden bg-gray-900 text-gray-100"
    >
      <div
        className="flex h-full transition-transform duration-300 ease-out"
        style={{ width: '300vw', transform: `translateX(-${pane * 100}vw)` }}
      >
        {/* Pane 0: Navigation */}
        <div
          className="w-screen h-full overflow-y-auto"
          onClick={e => { if (e.target.closest('a')) { setPane(1); setSelectedId(null) } }}
        >
          <Sidebar />
        </div>

        {/* Pane 1: Task list */}
        <div className="w-screen h-full flex flex-col overflow-hidden">
          <div className="flex h-12 flex-shrink-0 items-center border-b border-gray-700 px-3">
            <button
              onClick={() => setPane(0)}
              className="rounded px-2 py-1 text-sm text-gray-400 hover:text-gray-100"
            >
              ← Menu
            </button>
          </div>
          <div className="flex flex-col flex-1 overflow-hidden">
            <Routes>
              <Route path="/" element={<Navigate to="/view/all" replace />} />
              <Route path="/view/:view" element={
                <MainPanel
                  mobile
                  selectedId={selectedId}
                  onTaskSelect={handleTaskSelect}
                  onDeselect={handleDeselect}
                />
              } />
              <Route path="/favourite/:idx" element={
                <MainPanel
                  mobile
                  favourite
                  selectedId={selectedId}
                  onTaskSelect={handleTaskSelect}
                  onDeselect={handleDeselect}
                />
              } />
            </Routes>
          </div>
        </div>

        {/* Pane 2: Task detail */}
        <div className="w-screen h-full flex flex-col overflow-hidden">
          <div className="flex h-12 flex-shrink-0 items-center gap-2 border-b border-gray-700 px-3">
            <button
              onClick={() => setPane(1)}
              className="rounded px-2 py-1 text-sm text-gray-400 hover:text-gray-100"
            >
              ← Tasks
            </button>
            {selected && !confirmDelete && (
              <>
                <button
                  onClick={async () => { await closeTask.mutateAsync(selected.id); handleDeselect() }}
                  className="btn-close ml-auto rounded bg-indigo-700 px-3 py-1 text-xs font-medium text-white hover:bg-indigo-600"
                >
                  ✓ Close
                </button>
                <button
                  onClick={() => setConfirmDelete(true)}
                  className="btn-delete rounded px-3 py-1 text-xs text-gray-400 hover:bg-red-900/50 hover:text-red-300"
                >
                  Delete
                </button>
              </>
            )}
            {selected && confirmDelete && (
              <>
                <span className="ml-auto text-sm text-gray-400">Delete?</span>
                <button
                  onClick={async () => { await deleteTask.mutateAsync(selected.id); handleDeselect() }}
                  className="btn-delete-confirm rounded bg-red-700 px-3 py-1 text-xs font-medium text-white hover:bg-red-600"
                >
                  Yes, delete
                </button>
                <button
                  onClick={() => setConfirmDelete(false)}
                  className="rounded px-2 py-1 text-xs text-gray-400 hover:bg-gray-700"
                >
                  Cancel
                </button>
              </>
            )}
          </div>
          <div className="flex-1 overflow-y-auto">
            <TaskDetail selected={selected} />
          </div>
        </div>
      </div>
    </div>
  )
}
