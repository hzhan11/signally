import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import SignallyApp from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <SignallyApp />
  </StrictMode>,
)
