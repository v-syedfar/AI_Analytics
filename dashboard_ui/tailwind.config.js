module.exports = {
  content: ["./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0d1117",
        card: "#161b22",
        border: "#21262d",
        accent: {
          green: "#3fb950",
          yellow: "#d29922",
          red: "#f85149",
          blue: "#58a6ff",
          purple: "#bc8cff",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
