"""Visual system: typography and theme-agnostic CSS.

Every custom color is derived from ``currentColor`` so the same CSS works with
Streamlit's native light and dark themes (configured in .streamlit/config.toml).
"""

import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
  --ec-sans: 'IBM Plex Sans', -apple-system, 'Segoe UI', sans-serif;
  --ec-mono: 'IBM Plex Mono', ui-monospace, monospace;
}

/* Typography: body text, headings and widgets (icons keep their own font). */
.stApp, .stApp p, .stApp li, .stApp label, .stApp button, .stApp input,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
.stApp [data-testid="stMarkdownContainer"] {
  font-family: var(--ec-sans) !important;
}
.stApp code, .ec-num { font-family: var(--ec-mono) !important; }
.ec-num { font-variant-numeric: tabular-nums; }

/* Layout */
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
footer { visibility: hidden; }
.block-container { max-width: 1280px !important; padding-top: 2.5rem !important; padding-bottom: 4rem !important; }

/* Shared lines and tints, derived from the active text color. */
.ec-line { border-color: color-mix(in srgb, currentColor 14%, transparent) !important; }

/* Masthead */
.ec-mast h1 {
  font-size: clamp(1.35rem, 2.4vw, 1.8rem); font-weight: 600; letter-spacing: -0.015em;
  line-height: 1.2; margin: 0; padding: 0;
}
.ec-mast p { margin: 0.4rem 0 0; font-size: 0.95rem; opacity: 0.72; max-width: 68ch; }

/* Project strip */
.ec-strip {
  display: flex; flex-wrap: wrap; gap: 0.4rem 1.75rem; padding: 0.7rem 0;
  border-top: 1px solid color-mix(in srgb, currentColor 14%, transparent);
  border-bottom: 1px solid color-mix(in srgb, currentColor 14%, transparent);
  font-size: 0.84rem; margin: 0.5rem 0 0.25rem;
}
.ec-strip span { opacity: 0.68; }
.ec-strip b { font-weight: 600; }

/* Section heading */
.ec-sec {
  margin: 2.5rem 0 1rem; padding-top: 1rem;
  border-top: 1px solid color-mix(in srgb, currentColor 22%, transparent);
}
.ec-sec h2 { font-size: 1.12rem !important; font-weight: 600 !important; margin: 0 !important; padding: 0 !important; }
.ec-sec p { margin: 0.3rem 0 0; font-size: 0.9rem; opacity: 0.72; max-width: 72ch; }

/* Verdict */
.ec-state {
  display: inline-flex; align-items: center; gap: 0.4rem;
  font-family: var(--ec-mono); font-size: 0.82rem; font-weight: 600; letter-spacing: 0.02em;
}
.ec-pos { color: color-mix(in srgb, #16A34A 72%, currentColor); }
.ec-neg { color: color-mix(in srgb, #DC2626 72%, currentColor); }
.ec-mid { color: color-mix(in srgb, #D97706 72%, currentColor); }
.ec-svg { display: inline-block; vertical-align: -0.18em; flex-shrink: 0; }
.ec-verdict h3 {
  font-size: clamp(1.4rem, 2.6vw, 1.95rem) !important; font-weight: 600 !important;
  letter-spacing: -0.015em; line-height: 1.2; margin: 0.45rem 0 0.7rem !important; padding: 0 !important;
}
.ec-verdict p { font-size: 0.97rem; line-height: 1.65; max-width: 62ch; margin: 0; }

/* Metrics: ledger style, no floating cards. */
div[data-testid="stMetric"] {
  border-top: 2px solid color-mix(in srgb, currentColor 75%, transparent);
  padding: 0.65rem 0 0.4rem;
}
div[data-testid="stMetric"] label p { font-size: 0.82rem !important; opacity: 0.75; }
div[data-testid="stMetricValue"] > div {
  font-family: var(--ec-mono) !important; font-variant-numeric: tabular-nums;
  font-size: clamp(1.25rem, 2vw, 1.6rem) !important; font-weight: 600 !important; letter-spacing: -0.02em;
}

/* Tabs: editorial minimal underline without pill blobs */
.stTabs [data-baseweb="tab-list"] {
  gap: 1.5rem;
  border-bottom: 1px solid color-mix(in srgb, currentColor 18%, transparent) !important;
  background: transparent !important;
  padding: 0 0 0.2rem 0 !important;
  margin-top: 1.25rem !important;
  margin-bottom: 1rem !important;
}
.stTabs [data-baseweb="tab"] {
  font-family: var(--ec-sans) !important;
  font-size: 0.88rem !important;
  font-weight: 500 !important;
  padding: 0.65rem 0.2rem !important;
  color: color-mix(in srgb, currentColor 65%, transparent) !important;
  background: transparent !important;
  border: none !important;
  border-bottom: 2px solid transparent !important;
  transition: all 0.15s ease !important;
}
.stTabs [data-baseweb="tab"]:hover {
  color: currentColor !important;
  border-bottom-color: color-mix(in srgb, currentColor 35%, transparent) !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
  color: currentColor !important;
  font-weight: 600 !important;
  border-bottom: 2px solid currentColor !important;
  background: transparent !important;
}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {
  display: none !important;
}

/* Subhead for dual charts */
.ec-chart-title {
  font-size: 0.88rem;
  font-weight: 600;
  margin-bottom: 0.4rem;
  opacity: 0.85;
}

/* Ledger table */
.ec-table { overflow-x: auto; }
.ec-table table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
.ec-table th {
  text-align: right; font-weight: 600; padding: 0.55rem 0.6rem;
  border-bottom: 2px solid color-mix(in srgb, currentColor 70%, transparent);
}
.ec-table th:first-child, .ec-table td:first-child { text-align: left; padding-left: 0; }
.ec-table td {
  text-align: right; padding: 0.6rem; font-family: var(--ec-mono); font-variant-numeric: tabular-nums;
  border-bottom: 1px solid color-mix(in srgb, currentColor 12%, transparent);
}
.ec-table td:first-child { font-family: var(--ec-sans); }
.ec-table td small { display: block; opacity: 0.6; font-size: 0.76rem; }
.ec-table tr.ec-total td { font-weight: 600; background: color-mix(in srgb, currentColor 5%, transparent); }
.ec-table .ec-hl { font-weight: 600; }

/* Reading notes */
.ec-note { font-size: 0.88rem; line-height: 1.6; max-width: 70ch; margin: 0.25rem 0 0; }
.ec-note b { font-weight: 600; }
.ec-note-label { font-size: 0.78rem; font-weight: 600; opacity: 0.6; margin-bottom: 0.2rem; }

/* Empty state */
.ec-empty { padding: 2rem 0 1rem; max-width: 70ch; }
.ec-empty h3 { font-size: 1.2rem !important; font-weight: 600 !important; margin: 0 0 0.6rem !important; padding: 0 !important; }
.ec-empty p, .ec-empty li { font-size: 0.95rem; line-height: 1.65; }
.ec-empty ul { padding-left: 1.1rem; margin: 0.4rem 0 0; }

@media (max-width: 640px) {
  .block-container { padding-left: 1rem !important; padding-right: 1rem !important; padding-top: 1.5rem !important; }
  .ec-strip { gap: 0.3rem 1rem; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
</style>
"""


def aplicar_tema() -> None:
    """Inject the shared stylesheet once per run."""
    st.markdown(_CSS, unsafe_allow_html=True)
