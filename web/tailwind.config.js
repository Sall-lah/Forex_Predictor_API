/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: '#000000',
        secondary: '#14b8a6',
        'on-secondary': '#ffffff',
        'outline-variant': '#3f3f46',
      },
      fontFamily: {
        headline: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}