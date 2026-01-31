import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      colors: {
        // Cyberpunk neon colors
        neon: {
          purple: "#a855f7",
          magenta: "#ec4899",
          pink: "#f472b6",
          violet: "#8b5cf6",
        },
        // Dark theme backgrounds
        dark: {
          950: "#030712",
          900: "#0a0a0f",
          800: "#111118",
          700: "#1a1a24",
          600: "#252532",
        },
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "neon-glow": "linear-gradient(135deg, #a855f7 0%, #ec4899 50%, #f472b6 100%)",
        "neon-glow-hover": "linear-gradient(135deg, #c084fc 0%, #f472b6 50%, #fb7185 100%)",
      },
      boxShadow: {
        "neon-sm": "0 0 10px rgba(168, 85, 247, 0.3), 0 0 20px rgba(236, 72, 153, 0.2)",
        "neon-md": "0 0 20px rgba(168, 85, 247, 0.4), 0 0 40px rgba(236, 72, 153, 0.3)",
        "neon-lg": "0 0 30px rgba(168, 85, 247, 0.5), 0 0 60px rgba(236, 72, 153, 0.4)",
        "neon-glow": "0 0 15px rgba(168, 85, 247, 0.5), 0 0 30px rgba(236, 72, 153, 0.3), 0 0 45px rgba(168, 85, 247, 0.2)",
        "glass": "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
        "glass-lg": "0 8px 32px 0 rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(168, 85, 247, 0.1)",
      },
      backdropBlur: {
        xs: "2px",
      },
      animation: {
        "glow-pulse": "glow-pulse 2s ease-in-out infinite alternate",
        "float": "float 6s ease-in-out infinite",
      },
      keyframes: {
        "glow-pulse": {
          "0%": { boxShadow: "0 0 20px rgba(168, 85, 247, 0.4), 0 0 40px rgba(236, 72, 153, 0.2)" },
          "100%": { boxShadow: "0 0 30px rgba(168, 85, 247, 0.6), 0 0 60px rgba(236, 72, 153, 0.4)" },
        },
        "float": {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
