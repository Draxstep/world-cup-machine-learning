/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        "field-green": "#1a472a",
        "gold": "#f5a623",
        "dark-bg": "#0d1117",
        "card-bg": "#161b22",
        "border-subtle": "#30363d",
      },
      fontFamily: {
        display: ["'Bebas Neue'", "sans-serif"],
        body: ["'DM Sans'", "sans-serif"],
      },
    },
  },
  plugins: [],
};
