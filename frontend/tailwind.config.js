/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        neonblue: '#00f3ff',
        neongreen: '#39ff14',
        neonred: '#ff3131',
      }
    },
  },
  plugins: [],
}
