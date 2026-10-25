import { Route, Routes } from 'react-router-dom'

function App() {
  return (
    <div className="min-h-svh bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-4">
          <p className="text-lg font-semibold">Car Dealership Inventory</p>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Routes>
          <Route path="*" element={null} />
        </Routes>
      </main>
    </div>
  )
}

export default App
