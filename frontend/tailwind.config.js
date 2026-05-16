/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#060d19',
          900: '#0f172a',
          800: '#1e293b',
          700: '#2d3f55',
          600: '#3d506a'
        },
        crimson: {
          700: '#991b1b',
          600: '#b91c1c',
          500: '#dc2626',
          400: '#ef4444',
          300: '#fca5a5'
        }
      },
      fontFamily: {
        sans: ['DM Sans', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['Fraunces', 'Georgia', 'serif']
      },
      backgroundImage: {
        'gradient-navy': 'linear-gradient(135deg, #060d19 0%, #0f172a 50%, #1e293b 100%)'
      }
    }
  },
  plugins: []
}
