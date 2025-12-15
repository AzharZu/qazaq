/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        night: "#0f1724",
        midnight: "#101a2a",
        panel: "#1c2635",
        ink: "#e5e7eb",
        slate: "#2a3b56",
        slateDeep: "#1f2937",
        gold: "#f5d57a",
        goldDark: "#d9b44c",
        accent: "#1f2937",
      },
      boxShadow: {
        soft: "0 16px 40px rgba(0,0,0,0.22)",
        card: "0 12px 28px rgba(0,0,0,0.18)",
      },
      fontSize: {
        "hero": ["2.5rem", { lineHeight: "1.1" }],
      },
      borderRadius: {
        xl: "18px",
      },
    },
  },
  plugins: [],
};
