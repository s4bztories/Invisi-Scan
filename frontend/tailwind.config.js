/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        soc: {
          dark: '#0f172a',    // slate-900 
          card: '#1e293b',    // slate-800
          border: '#334155',  // slate-700
          accent: '#38bdf8',  // sky-400
          danger: '#ef4444',  // red-500
          warning: '#f59e0b', // amber-500
          success: '#10b981', // emerald-500
        }
      },
      animation: {
        'pulse-fast': 'pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'ping-slow': 'ping 2s cubic-bezier(0, 0, 0.2, 1) infinite',
      }
    },
  },
  plugins: [],
}
