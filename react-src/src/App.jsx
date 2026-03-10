import { useEffect, useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import MainPanel from './components/MainPanel'
import CaptureView from './components/CaptureView'
import MobileShell from './components/MobileShell'

function useMobile() {
  const [mobile, setMobile] = useState(
    () => window.matchMedia('(max-width: 767px)').matches
  )
  useEffect(() => {
    const mq = window.matchMedia('(max-width: 767px)')
    const handler = e => setMobile(e.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])
  return mobile
}

function Shell() {
  const mobile = useMobile()

  if (mobile) return <MobileShell />

  return (
    <div className="flex h-full overflow-hidden bg-gray-900 text-gray-100">
      <Sidebar />
      <div className="flex flex-1 overflow-hidden">
        <Routes>
          <Route path="/"                element={<Navigate to="/view/all" replace />} />
          <Route path="/view/:view"      element={<MainPanel />} />
          <Route path="/favourite/:idx"  element={<MainPanel favourite />} />
        </Routes>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/capture" element={<CaptureView />} />
      <Route path="/*"       element={<Shell />} />
    </Routes>
  )
}
