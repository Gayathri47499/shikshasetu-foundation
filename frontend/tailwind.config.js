/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          pink: "#F6C9D5",
          rose: "#D97998",
          roseDark: "#C05D7E",
          soft: "#FFF1F5",
          greenBg: "#E8F5EC",
          green: "#4D9B78",
          ink: "#28313B",
          muted: "#687482",
          border: "#F3DCE3",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Plus Jakarta Sans", "Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        soft: "0 6px 24px -6px rgba(217, 121, 152, 0.14)",
        card: "0 2px 12px -2px rgba(40, 49, 59, 0.06)",
      },
    },
  },
  plugins: [],
};
