import { Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import MainPanel from './components/MainPanel'

export default function App() {
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
