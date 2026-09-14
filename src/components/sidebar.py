import streamlit as st
from src.core.auth import has_permission
from src.core.session import get_current_user, logout

def render_sidebar() -> str:
    """Renders the corporate sidebar component:
    1. Top Brand Header (AGROLAB)
    2. Left-aligned Profile Section (Avatar container + Name + Role Badge)
    3. Vertical Navigation Modules list (Filtered by Role Permissions)
    4. Logout button anchored to bottom of flex wrapper
    """
    user = get_current_user()
    role = user.get("role", "operador")

    st.markdown("""
        <style>
        /* Hide native stSidebarHeader */
        header[data-testid="stSidebarHeader"],
        [data-testid="stSidebarHeader"] {
            display: none !important;
            padding: 0 !important;
            margin: 0 !important;
            height: 0px !important;
        }

        /* Sidebar container */
        section[data-testid="stSidebar"],
        [data-testid="stSidebar"] {
            display: flex !important;
            flex-direction: column !important;
            background-color: #FFFFFF !important;
            border-right: 1px solid #E5E7EB !important;
        }

        /* Full height Flexbox sidebar hierarchy */
        [data-testid="stSidebarContent"] {
            display: flex !important;
            flex-direction: column !important;
            height: 100vh !important;
        }

        [data-testid="stSidebarUserContent"] {
            display: flex !important;
            flex-direction: column !important;
            flex: 1 1 auto !important;
            height: calc(100vh - 1rem) !important;
            padding-top: 1.25rem !important;
            padding-bottom: 1.25rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            box-sizing: border-box !important;
        }

        [data-testid="stSidebarUserContent"] > div[data-testid="stVerticalBlock"],
        [data-testid="stSidebarUserContent"] > div {
            display: flex !important;
            flex-direction: column !important;
            flex: 1 1 auto !important;
            height: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        /* Hide native Streamlit navigation */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        /* Brand title */
        .sidebar-brand-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: #111827;
            letter-spacing: 0.5px;
            margin-top: 4px;
            margin-bottom: 12px;
            padding: 0;
        }

        /* Left-aligned horizontal profile section */
        .profile-section-side {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 4px 0;
            margin-top: 4px;
            margin-bottom: 16px;
        }

        /* Avatar container with crisp border and subtle background */
        .profile-avatar-container {
            width: 46px;
            height: 46px;
            border-radius: 10px;
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .profile-info-side {
            display: flex;
            flex-direction: column;
            text-align: left;
        }

        .profile-name-side {
            font-size: 0.875rem;
            font-weight: 700;
            color: #0F172A;
            line-height: 1.2;
            margin: 0;
        }

        .profile-role-badge {
            display: inline-block;
            background-color: #F3F4F6;
            color: #111827;
            border: 1px solid #E5E7EB;
            border-radius: 4px;
            padding: 1px 6px;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            margin-top: 3px;
            text-align: center;
            width: fit-content;
            text-transform: uppercase;
        }

        /* Unified 100% width button rules in sidebar wrapper */
        [data-testid="stSidebar"] div[data-testid="stElementContainer"],
        [data-testid="stSidebar"] div.stElementContainer,
        [data-testid="stSidebar"] div.stButton {
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
            box-sizing: border-box !important;
        }

        [data-testid="stSidebar"] div.stButton > button {
            justify-content: flex-start !important;
            text-align: left !important;
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            border-radius: 6px !important;
            padding: 8px 12px !important;
            margin-bottom: 2px !important;
            width: 100% !important;
            box-sizing: border-box !important;
        }

        [data-testid="stSidebar"] div.stButton > button *,
        [data-testid="stSidebar"] div.stButton > button [data-testid="stMarkdownContainer"] p {
            justify-content: flex-start !important;
            text-align: left !important;
        }

        /* Active navigation button: light gray background #F3F4F6, dark text #111827 */
        [data-testid="stSidebar"] div.stButton > button[data-testid="stBaseButton-primary"],
        [data-testid="stSidebar"] div.stButton > button[kind="primary"] {
            background-color: #F3F4F6 !important;
            color: #111827 !important;
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }

        [data-testid="stSidebar"] div.stButton > button[data-testid="stBaseButton-primary"] *,
        [data-testid="stSidebar"] div.stButton > button[kind="primary"] * {
            color: #111827 !important;
            fill: #111827 !important;
            font-weight: 600 !important;
        }

        /* Inactive buttons: transparent background */
        [data-testid="stSidebar"] div.stButton > button[data-testid="stBaseButton-secondary"],
        [data-testid="stSidebar"] div.stButton > button[kind="secondary"] {
            background-color: transparent !important;
            color: #475569 !important;
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }

        [data-testid="stSidebar"] div.stButton > button[data-testid="stBaseButton-secondary"] *,
        [data-testid="stSidebar"] div.stButton > button[kind="secondary"] * {
            color: #475569 !important;
            fill: #475569 !important;
            font-weight: 400 !important;
        }

        [data-testid="stSidebar"] div.stButton > button[data-testid="stBaseButton-secondary"]:hover {
            background-color: #F9FAFB !important;
            color: #111827 !important;
        }

        [data-testid="stSidebar"] div.stButton > button[data-testid="stBaseButton-secondary"]:hover * {
            color: #111827 !important;
            fill: #111827 !important;
        }

        /* Preserve native Streamlit Material Symbols icon font */
        [data-testid="stSidebar"] [data-testid="stIcon"],
        [data-testid="stSidebar"] [data-testid="stIcon"] *,
        [data-testid="stSidebar"] span[data-testid="stIcon"] {
            font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
            font-weight: normal !important;
            font-style: normal !important;
        }

        /* Anchor logout button to bottom within the same stVerticalBlock wrapper */
        [data-testid="stSidebarUserContent"] > div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"]:last-child,
        [data-testid="stSidebarUserContent"] > div[data-testid="stVerticalBlock"] > div.stElementContainer:last-child {
            margin-top: auto !important;
            padding-top: 1rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 1. Sidebar Header Title
    st.sidebar.markdown("<div class='sidebar-brand-title'>AGROLAB</div>", unsafe_allow_html=True)

    # 2. Profile Section: Left-aligned with framed avatar container and role badge
    full_name = str(user.get("full_name") or user.get("username") or "Usuario")
    role_display = str(user.get("role") or "operador").upper()
    st.sidebar.markdown(
        f"""
        <div class="profile-section-side">
            <div class="profile-avatar-container">
                <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#111827" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                </svg>
            </div>
            <div class="profile-info-side">
                <div class="profile-name-side">{full_name}</div>
                <div class="profile-role-badge">{role_display}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 3. Navigation Modules list with RBAC Filtering
    all_modules = [
        {
            "id": "frequent_clients_churn",
            "label": "Clientes y Churn",
            "icon": ":material/group:",
            "roles": ["admin", "responsable_laboratorio", "responsable_rrii"],
        },
        {
            "id": "crop_capacity",
            "label": "Cultivos y Capacidad",
            "icon": ":material/show_chart:",
            "roles": ["admin", "responsable_laboratorio", "analista_laboratorio"],
        },
        {
            "id": "rfm_segmentation",
            "label": "Segmentación RFM",
            "icon": ":material/analytics:",
            "roles": ["admin", "responsable_rrii", "comercial"],
        },
    ]

    modules = [m for m in all_modules if has_permission(m["roles"])]

    if not modules:
        st.sidebar.warning("No tienes módulos asignados para tu rol.")
        if st.sidebar.button("Cerrar Sesión", key="sidebar_logout_btn_empty", icon=":material/logout:"):
            logout()
        return ""

    # Initialize active module state to the first authorized module if current selection is invalid
    allowed_ids = [m["id"] for m in modules]
    if "active_module_id" not in st.session_state or st.session_state["active_module_id"] not in allowed_ids:
        st.session_state["active_module_id"] = allowed_ids[0]

    # Render vertical module navigation buttons
    for mod in modules:
        is_active = (st.session_state["active_module_id"] == mod["id"])
        btn_type = "primary" if is_active else "secondary"
        
        if st.sidebar.button(
            mod["label"],
            key=f"side_btn_{mod['id']}",
            type=btn_type,
            icon=mod["icon"]
        ):
            st.session_state["active_module_id"] = mod["id"]
            st.rerun()

    # 4. Logout button anchored to bottom
    if st.sidebar.button("Cerrar Sesión", key="sidebar_logout_btn", icon=":material/logout:"):
        logout()

    return st.session_state["active_module_id"]
