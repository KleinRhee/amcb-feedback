/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./templates/**/*.html",
    "./static/**/*.js"
  ],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'sans-serif'] },
      colors: { 
        amcprimary: '#004b72', 
        amcteal: '#00838b', 
        amcorange: '#f2a900', 
        darkbg: '#0f172a', 
        darkcard: '#1e293b' 
      },
      animation: { 'slide-down': 'slideDown 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards' },
      keyframes: { 
        slideDown: { 
          '0%': { opacity: 0, transform: 'translateY(-100%)' }, 
          '100%': { opacity: 1, transform: 'translateY(0)' } 
        } 
      }
    }
  },
  plugins: [],
}