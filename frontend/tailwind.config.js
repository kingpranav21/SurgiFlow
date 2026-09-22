/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0b1220",
          900: "#111a2b",
          800: "#1a2740",
          700: "#243354",
        },
        steel: {
          100: "#e8eef7",
          300: "#b8c4d9",
          400: "#8a9bb8",
          500: "#6b7c99",
        },
        signal: {
          high: "#e35d5d",
          med: "#d4a017",
          low: "#2f9e6b",
          accent: "#3d8bfd",
        },
      },
      fontFamily: {
        display: ['"IBM Plex Sans"', "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
      boxShadow: {
        panel: "0 1px 0 rgba(255,255,255,0.04) inset, 0 8px 24px rgba(0,0,0,0.35)",
      },
    },
  },
  plugins: [],
};
