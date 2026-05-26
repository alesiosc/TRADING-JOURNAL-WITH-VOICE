/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sidebar: '#1a1a2e',
        'sidebar-hover': '#16213e',
        'sidebar-active': '#0f3460',
        surface: '#ffffff',
        'page-bg': '#f8f9fa',
        'positive': '#22c55e',
        'negative': '#ef4444',
        'accent': '#3b82f6',
      },
      fontFamily: {
        sans: ['system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
