/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Base & Backgrounds (Warm & Soft Cream)
        "surface": "#F9F6F0",
        "background": "#F9F6F0",
        "surface-container-lowest": "#FFFFFF",
        "surface-container-low": "#F4EFE6",
        "surface-container": "#EFE9DE",
        "surface-container-high": "#E7DFCEx",
        "surface-container-highest": "#DFD6C3",
        "surface-variant": "#E8E2D5",
        "surface-dim": "#D8CFBD",

        // Text & Structure (Deep Navy Blue)
        "primary": "#1E293B",
        "primary-container": "#0F172A",
        "on-primary": "#FFFFFF",
        "on-primary-container": "#E2E8F0",
        "on-surface": "#0F172A",
        "on-surface-variant": "#334155",
        "on-background": "#0F172A",
        "outline": "#64748B",
        "outline-variant": "#CBD5E1",

        // Primary Accent / Vitality (Terracotta / Burnt Orange)
        "secondary": "#C25E38",
        "secondary-container": "#FDEEE8",
        "on-secondary": "#FFFFFF",
        "on-secondary-container": "#7C2D12",
        "secondary-fixed": "#FFDBCF",

        // Health & Progress (Deep Olive Green / Sage)
        "tertiary": "#4A6B5B",
        "tertiary-container": "#E8F0EC",
        "on-tertiary": "#FFFFFF",
        "on-tertiary-container": "#1B382B",
        "sage": "#4A6B5B",
        "sage-light": "#E8F0EC",
        "sage-dark": "#2E473B",

        // Alert & Critical (Dark Burgundy)
        "error": "#881337",
        "error-container": "#FFE4E6",
        "on-error": "#FFFFFF",
        "on-error-container": "#4C0519",
        "burgundy": "#881337",

        // Attention / Moderate Warning (Warm Amber)
        "warning": "#D97706",
        "warning-container": "#FEF3C7",
        "on-warning": "#FFFFFF",
        "on-warning-container": "#78350F",
        "amber-warm": "#D97706",
      },
      borderRadius: {
        "DEFAULT": "0.5rem",
        "md": "0.75rem",
        "lg": "1rem",
        "xl": "1.25rem",
        "2xl": "1.5rem",
        "3xl": "2rem",
        "full": "9999px"
      },
      spacing: {
        "touch-target-min": "48px",
        "touch-target-large": "56px",
        "touch-target-xl": "64px",
        "margin-mobile": "20px",
        "margin-desktop": "64px",
        "gutter": "24px",
        "stack-sm": "12px",
        "stack-md": "24px",
        "stack-lg": "48px"
      },
      fontFamily: {
        "sans": ["Lexend", "Inter", "sans-serif"],
        "lexend": ["Lexend", "sans-serif"],
        "inter": ["Inter", "sans-serif"]
      },
      fontSize: {
        "body-sm": ["16px", "24px"],
        "body-md": ["18px", "28px"],
        "body-lg": ["20px", "30px"],
        "label-md": ["16px", "22px"],
        "label-lg": ["18px", "24px"],
        "headline-sm": ["22px", "30px"],
        "headline-md": ["26px", "34px"],
        "headline-lg": ["32px", "40px"],
        "headline-xl": ["40px", "48px"]
      },
      boxShadow: {
        "soft-sm": "0 2px 8px rgba(15, 23, 42, 0.05)",
        "soft-md": "0 4px 16px rgba(15, 23, 42, 0.07)",
        "soft-lg": "0 8px 24px rgba(15, 23, 42, 0.09)",
        "soft-xl": "0 12px 32px rgba(15, 23, 42, 0.12)",
      }
    },
  },
  plugins: [],
}
