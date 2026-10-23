// Tailwind v4 — theme is configured via @theme in globals.css.
// This file is kept for editor tooling compatibility only.
import type { Config } from 'tailwindcss'

const config: Config = {
  // Content scanning is handled by @source directives in globals.css for v4.
  // These paths are kept as a fallback reference.
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './features/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
}
export default config
