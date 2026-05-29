/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'ghost-border': '#E5E7EB',
        'ghost-bg': '#F9FAFB',
        'ghost-hover': '#F3F4F6',
        'surface': '#FFFFFF',
        'page-bg': '#F9FAFB',
        'text-primary': '#111827',
        'text-secondary': '#6B7280',
        'text-body': '#4B5563',
        'positive': '#22c55e',
        'negative': '#ef4444',
        'accent': '#3b82f6',
        'accent-soft': '#EFF6FF',
        'pill-blue': '#EFF6FF',
        'pill-blue-text': '#2563EB',
        'pill-gray': '#F3F4F6',
        'pill-gray-text': '#4B5563',
        'pill-green': '#ECFDF5',
        'pill-green-text': '#059669',
        'pill-red': '#FEF2F2',
        'pill-red-text': '#DC2626',
        'pill-orange': '#FFF7ED',
        'pill-orange-text': '#EA580C',
        'pill-purple': '#F5F3FF',
        'pill-purple-text': '#7C3AED',
        // Legacy aliases so existing code doesn't break
        'sidebar': '#FFFFFF',
        'sidebar-hover': '#F9FAFB',
        'sidebar-active': '#F3F4F6',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      borderRadius: {
        'pill': '9999px',
      },
      boxShadow: {
        'ghost': '0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.06)',
        'ghost-hover': '0 4px 12px 0 rgba(0, 0, 0, 0.06), 0 1px 3px 0 rgba(0, 0, 0, 0.04)',
        'ghost-modal': '0 20px 60px 0 rgba(0, 0, 0, 0.08), 0 1px 3px 0 rgba(0, 0, 0, 0.04)',
      },
    },
  },
  plugins: [],
};
