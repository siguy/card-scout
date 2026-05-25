/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          950: "#030712", // Deep obsidian background
          900: "#090d16", // Slightly elevated container dark
          800: "#111827", // Accent dark
          700: "#1f2937",
        },
        gold: {
          50: "#fffbeb",
          100: "#fef3c7",
          200: "#fde68a",
          300: "#fcd34d",
          400: "#fbbf24",
          500: "#f59e0b",
          600: "#d97706",
          700: "#b45309",
          800: "#92400e",
          900: "#78350f",
          950: "#451a03",
        },
        luxury: {
          card: "rgba(255, 255, 255, 0.02)",
          border: "rgba(255, 255, 255, 0.06)",
          borderHover: "rgba(255, 255, 255, 0.12)",
          glow: "rgba(99, 102, 241, 0.15)", // Subtle indigo background glow
        }
      },
      borderRadius: {
        '3xl': '24px', // Standardized 24px rounded corners per Vibe Profile!
      },
      fontFamily: {
        sans: ["Outfit", "Inter", "sans-serif"], // Sleek modern typography
      },
      boxShadow: {
        'glass-sm': '0 4px 12px 0 rgba(0, 0, 0, 0.15)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.25)',
        'glass-lg': '0 16px 48px 0 rgba(0, 0, 0, 0.35)',
      }
    },
  },
  plugins: [],
}
