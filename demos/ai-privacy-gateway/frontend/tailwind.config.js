/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        huawei: {
          red: '#9a0000',
          blue: '#007DFF',
          'blue-dark': '#0058DD',
          'blue-light': '#E6F4FF',
          gray: {
            50: '#F5F7FA',
            100: '#EBEDF0',
            200: '#DCE0E6',
            300: '#C4C9D4',
            600: '#646A73',
            700: '#393939',
            800: '#1D2129',
            900: '#0D1117',
          },
        },
      },
    },
  },
  plugins: [],
}
