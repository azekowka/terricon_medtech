import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
        },
        teal: {
          500: "#14b8a6",
          600: "#0d9488",
        },
        ink: "#0f172a",
      },
      fontFamily: {
        // Aviasales font stack (Stapel is proprietary -> falls back to Inter, which
        // is the typeface they actually use). Inter is loaded via next/font.
        sans: [
          "Stapel",
          "-apple-system",
          "BlinkMacSystemFont",
          "var(--font-inter)",
          "Inter",
          "Roboto",
          "Helvetica",
          "Arial",
          "sans-serif",
        ],
      },
      boxShadow: {
        card: "0 1px 3px rgba(15,23,42,0.08), 0 1px 2px rgba(15,23,42,0.04)",
        hover: "0 8px 24px rgba(37,99,235,0.12)",
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.125rem",
      },
    },
  },
  plugins: [],
};

export default config;
