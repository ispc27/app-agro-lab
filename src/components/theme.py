import streamlit as st

def apply_enterprise_theme():
    """Injects global corporate CSS rules (Poppins font, clean white palette, crisp input borders)."""
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

        /* Global Poppins typography */
        html, body, .stApp, button, input, select, textarea, p, h1, h2, h3, h4, h5, h6, label,
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stWidgetLabel"] label {
            font-family: 'Poppins', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }

        /* Preserve native Streamlit Material Symbols icons font */
        [data-testid="stIcon"],
        [data-testid="stIcon"] *,
        span[data-testid="stIcon"],
        .material-symbols-rounded,
        .material-symbols-outlined,
        .material-icons,
        [class*="material-symbols"] {
            font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
            font-weight: normal !important;
            font-style: normal !important;
        }

        /* Minimalist enterprise app background */
        .stApp {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
        }

        /* Maximize main content container width & top alignment */
        .main .block-container,
        [data-testid="stMainBlockContainer"],
        [data-testid="stBlockContainer"] {
            max-width: 100% !important;
            padding-top: 1.25rem !important;
            padding-bottom: 2rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }

        /* Primary buttons in main container */
        .main button[kind="primary"],
        .main div.stButton > button[data-testid="stBaseButton-primary"] {
            background-color: #111827 !important;
            color: #FFFFFF !important;
            border-radius: 6px !important;
            border: 1px solid #111827 !important;
            font-weight: 600 !important;
        }

        .main button[kind="primary"] *,
        .main div.stButton > button[data-testid="stBaseButton-primary"] * {
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }

        /* Text inputs and select inputs with clean 1px borders in resting state */
        div[data-testid="stTextInput"] div[data-baseweb="input"],
        div[data-baseweb="input"],
        div[data-baseweb="select"] > div {
            border: 1px solid #D1D5DB !important;
            border-radius: 6px !important;
            background-color: #FFFFFF !important;
            box-shadow: none !important;
        }

        div[data-baseweb="base-input"] {
            border: none !important;
            background-color: transparent !important;
            box-shadow: none !important;
        }

        div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
        div[data-baseweb="input"]:focus-within,
        div[data-baseweb="select"] > div:focus-within {
            border: 2px solid #111827 !important;
            box-shadow: none !important;
        }

        div[data-baseweb="input"] input, div[data-testid="stTextInput"] input {
            color: #0F172A !important;
            font-size: 0.95rem !important;
            background-color: transparent !important;
        }

        /* Widget Labels */
        [data-testid="stWidgetLabel"] label {
            color: #111827 !important;
            font-weight: 600 !important;
            font-size: 0.875rem !important;
            margin-bottom: 4px !important;
        }

        /* Enterprise Metric Cards */
        [data-testid="stMetric"] {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 14px 18px;
        }

        [data-testid="stMetricValue"] {
            color: #0F172A !important;
            font-weight: 600;
        }

        [data-testid="stMetricLabel"] {
            color: #64748B !important;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        /* Dividers */
        hr {
            margin-top: 0.5rem;
            margin-bottom: 1.25rem;
            border-color: #E2E8F0;
        }
        </style>
    """, unsafe_allow_html=True)

def render_header(title: str, subtitle: str = ""):
    """Renders a standardized section header (Title + Subtitle)."""
    apply_enterprise_theme()
    st.markdown(f"<h2 style='font-size: 1.5rem; font-weight: 700; color: #111827; margin-bottom: 2px; margin-top: 0;'>{title}</h2>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<p style='color: #64748B; font-size: 0.95rem; margin-bottom: 1.5rem;'>{subtitle}</p>", unsafe_allow_html=True)
