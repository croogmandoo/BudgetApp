/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        surface: {
          0: '#111210',
          1: '#1a1918',
          2: '#242220',
          3: '#302e2b'
        },
        ink: {
          primary: '#f2ede4',
          secondary: '#9a9389',
          muted: '#5a5650'
        },
        accent: '#c9a84c',
        positive: '#5bbf8a',
        negative: '#d9594c',
        caution: '#d4903a',
        info: '#6b9fca'
      },
      fontFamily: {
        display: ['Fraunces', 'Georgia', 'serif'],
        sans: ['DM Sans', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace']
      },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.5), 0 1px 2px rgba(0,0,0,0.4)',
        elevated: '0 4px 16px rgba(0,0,0,0.6)'
      },
      borderRadius: {
        sm: '4px',
        DEFAULT: '6px',
        md: '8px',
        lg: '12px',
        xl: '16px'
      }
    }
  },
  plugins: []
};
