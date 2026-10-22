/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#080808',
        surface: {
          DEFAULT: '#101010',
          elevated: '#171717',
          card: '#121212',
        },
        border: {
          DEFAULT: '#292929',
          subtle: '#1f1f1f',
          chrome: '#3d3d3d',
        },
        chrome: {
          DEFAULT: '#dedede',
          bright: '#f5f5f5',
          dim: '#b5b5b5',
        },
        muted: '#888888',
        accent: {
          DEFAULT: '#a62735',
          hover: '#bf2d3d',
        },
        critical: '#db3346',
        success: '#79a995',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['"Space Grotesk"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      borderRadius: {
        none: '0',
        sm: '2px',
        DEFAULT: '2px',
        md: '4px',
      },
    },
  },
  plugins: [],
}
