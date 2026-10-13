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

        /* Enterprise Metric Cards Styling */
        [data-testid="stMetric"] {
            background-color: #F8FAFC !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 8px !important;
            padding: 16px 20px !important;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.02) !important;
        }

        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] * {
            color: #111827 !important;
            font-size: 1.55rem !important;
            font-weight: 700 !important;
            line-height: 1.2 !important;
        }

        [data-testid="stMetricLabel"],
        [data-testid="stMetricLabel"] * {
            color: #64748B !important;
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }
        
        /* Dividers */
        hr {
            margin-top: 0.5rem;
            margin-bottom: 1.25rem;
            border-color: #E2E8F0;
        }

        /* Unified Enterprise Alert Containers (st.info, st.warning, st.error, st.success) */
        div[data-testid="stAlertContainer"],
        div[data-testid="stAlert"],
        .stAlert,
        .stAlertContainer {
            border-radius: 8px !important;
            border: 1px solid #D1D5DB !important;
            padding: 14px 18px !important;
            box-shadow: none !important;
        }

        /* Error / Danger */
        div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]),
        div[data-testid="stAlert"]:has([data-testid="stNotification-error"]),
        div[data-testid="stAlertContentError"] {
            background-color: #FEF2F2 !important;
            border-color: #FECACA !important;
            color: #7F1D1D !important;
        }

        /* Warning */
        div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]),
        div[data-testid="stAlert"]:has([data-testid="stNotification-warning"]),
        div[data-testid="stAlertContentWarning"] {
            background-color: #FFFBEB !important;
            border-color: #FDE68A !important;
            color: #78350F !important;
        }

        /* Info */
        div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]),
        div[data-testid="stAlert"]:has([data-testid="stNotification-info"]),
        div[data-testid="stAlertContentInfo"] {
            background-color: #EFF6FF !important;
            border-color: #BFDBFE !important;
            color: #1E3A8A !important;
        }

        /* Success */
        div[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]),
        div[data-testid="stAlert"]:has([data-testid="stNotification-success"]),
        div[data-testid="stAlertContentSuccess"] {
            background-color: #F0FDF4 !important;
            border-color: #BBF7D0 !important;
            color: #14532D !important;
        }

        div[data-testid="stAlertContainer"] p,
        div[data-testid="stAlertContainer"] span,
        div[data-testid="stAlert"] p,
        div[data-testid="stAlert"] span {
            font-family: 'Poppins', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            font-size: 0.92rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_header(title: str, subtitle: str = ""):
    """Renders a standardized section header (Title + Subtitle)."""
    apply_enterprise_theme()
    st.markdown(f"<h2 style='font-size: 1.5rem; font-weight: 700; color: #111827; margin-bottom: 2px; margin-top: 0;'>{title}</h2>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<p style='color: #64748B; font-size: 0.95rem; margin-bottom: 1.5rem;'>{subtitle}</p>", unsafe_allow_html=True)

def render_metric_card(
    label: str,
    value: str,
    badge_text: str | None = None,
    badge_bg: str = "#EFF6FF",
    badge_color: str = "#1E40AF",
) -> str:
    """Renders a standardized enterprise KPI card with consistent typography and optional badge."""
    badge_html = (
        f'<span style="background-color: {badge_bg}; color: {badge_color}; '
        f'font-size: 0.72rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; '
        f'white-space: nowrap;">{badge_text}</span>'
        if badge_text
        else ""
    )
    return (
        f'<div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; '
        f'padding: 16px 18px; min-height: 98px; display: flex; flex-direction: column; '
        f'justify-content: space-between; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02);">'
        f'<div style="color: #64748B; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; '
        f'letter-spacing: 0.5px; margin-bottom: 4px;">{label}</div>'
        f'<div style="display: flex; align-items: baseline; gap: 8px; flex-wrap: nowrap;">'
        f'<span style="color: #111827; font-size: 1.55rem; font-weight: 700; line-height: 1.2;">{value}</span>'
        f'{badge_html}</div></div>'
    )

def render_alert_box(title: str, message: str, alert_type: str = "warning") -> str:
    """Renders a unified enterprise alert container with 1px solid perimeter border,
    8px border radius, corporate color tokens, zero emojis, and clean typography.
    
    Supported alert_types:
    - 'danger' / 'error': Critical situations, bottlenecks, churn risk.
    - 'warning': Operational cautions, capacity warning thresholds.
    - 'info': Informative context, system notes.
    - 'success': Optimal operations, target compliance.
    """
    schemes = {
        "danger": {
            "bg": "#FEF2F2",
            "border": "#FECACA",
            "title": "#991B1B",
            "body": "#7F1D1D",
        },
        "error": {
            "bg": "#FEF2F2",
            "border": "#FECACA",
            "title": "#991B1B",
            "body": "#7F1D1D",
        },
        "warning": {
            "bg": "#FFFBEB",
            "border": "#FDE68A",
            "title": "#92400E",
            "body": "#78350F",
        },
        "info": {
            "bg": "#EFF6FF",
            "border": "#BFDBFE",
            "title": "#1E40AF",
            "body": "#1E3A8A",
        },
        "success": {
            "bg": "#F0FDF4",
            "border": "#BBF7D0",
            "title": "#166534",
            "body": "#14532D",
        },
    }
    cfg = schemes.get(alert_type.lower(), schemes["info"])
    
    return (
        f'<div style="background-color: {cfg["bg"]}; border: 1px solid {cfg["border"]}; '
        f'border-radius: 8px; padding: 16px 20px; margin: 15px 0 20px 0; font-family: \'Poppins\', sans-serif;">'
        f'<div style="margin-bottom: 6px;">'
        f'<strong style="color: {cfg["title"]}; font-size: 1.02rem; letter-spacing: -0.01em; text-transform: uppercase;">'
        f'{title}</strong></div>'
        f'<div style="color: {cfg["body"]}; font-size: 0.92rem; line-height: 1.55;">'
        f'{message}</div></div>'
    )
