import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import SignallyApp from './App.jsx'
// Import the logo image so Vite includes it in the build and we can reference its hashed URL
import logoPng from './assets/logo.png'

// Ensure favicon uses the bundled logo (works in dev & build)
(function ensureFavicon() {
  try {
    let link = document.querySelector("link[rel='icon']")
    if (!link) {
      link = document.createElement('link')
      link.rel = 'icon'
      document.head.appendChild(link)
    }
    // Only replace if different
    if (link.href !== logoPng) {
      link.type = 'image/png'
      link.href = logoPng
    }
  } catch (e) {
    // Silently ignore; favicon not critical
    console.warn('Unable to set favicon:', e)
  }
})()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <SignallyApp />
  </StrictMode>,
)
