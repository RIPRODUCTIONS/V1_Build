/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx}",
    "./src/components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        atomic: { bg: "#0D1421", surface: "#1B2433", border: "#2B3648" },
        proton: "#FF4136",
        neutron: "#B0B0B0",
        electron: "#0074D9",
      },
      animation: {
        orbit: "orbit 24s linear infinite",
        glow: "glow 1s ease-in-out infinite",
        burst: "burst .35s ease-out",
      },
    },
  },
  plugins: [],
};
