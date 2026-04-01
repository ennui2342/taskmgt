/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // fills the gap between gray-800 and gray-900
        'gray-850': '#1a1f2e',
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
}
