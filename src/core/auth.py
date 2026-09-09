import bcrypt
import streamlit as st
from src.config.settings import load_settings

def authenticate_user(username_input: str | None, password_input: str | None) -> dict | None:
    """Verifies username and password against credentials stored in config.yaml.
    
    Args:
        username_input (str | None): The provided username.
        password_input (str | None): The provided plain password.

    Returns:
        dict | None: User details if authenticated successfully, otherwise None.
    """
    if not username_input or not password_input:
        return None
        
    clean_username = str(username_input).strip().lower()
    clean_password = str(password_input)

    settings = load_settings()
    usernames = settings.get("credentials", {}).get("usernames", {})
    
    # Case-insensitive key lookup for usernames dictionary
    user_info = None
    for key, val in usernames.items():
        if str(key).strip().lower() == clean_username and isinstance(val, dict):
            user_info = val
            break
            
    if not user_info:
        return None
        
    stored_hash = str(user_info.get("password", ""))
    try:
        if bcrypt.checkpw(clean_password.encode('utf-8'), stored_hash.encode('utf-8')):
            full_name = user_info.get("full_name") or clean_username
            return {
                "username": clean_username,
                "full_name": full_name,
                "email": user_info.get("email", ""),
                "role": str(user_info.get("role", "operador")).strip().lower()
            }
    except (ValueError, TypeError):
        return None
        
    return None

def render_login_form():
    """Renders the centered enterprise login screen."""
    st.markdown("""
        <style>
        /* Hide sidebar and controls during login */
        [data-testid="stSidebar"], [data-testid="stSidebarNav"], [data-testid="collapsedControl"] {
            display: none !important;
            width: 0px !important;
        }

        .stApp {
            background-color: #FFFFFF !important;
        }

        [data-testid="stForm"] {
            border: 1px solid #E5E7EB !important;
            border-radius: 10px !important;
            padding: 36px 32px !important;
            background-color: #FFFFFF !important;
            box-shadow: none !important;
        }

        /* Single-layer border on text inputs in resting state */
        div[data-testid="stTextInput"] div[data-baseweb="input"],
        div[data-baseweb="input"] {
            border: 1px solid #D1D5DB !important;
            border-radius: 6px !important;
            background-color: #FFFFFF !important;
            box-shadow: none !important;
        }

        /* Clear internal nested container borders */
        div[data-baseweb="base-input"] {
            border: none !important;
            background-color: transparent !important;
            box-shadow: none !important;
        }

        /* Hover state */
        div[data-testid="stTextInput"] div[data-baseweb="input"]:hover,
        div[data-baseweb="input"]:hover {
            border-color: #9CA3AF !important;
        }

        /* Active focus state */
        div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
        div[data-baseweb="input"]:focus-within {
            border: 2px solid #111827 !important;
            box-shadow: none !important;
        }

        div[data-baseweb="input"] input,
        div[data-testid="stTextInput"] input {
            color: #0F172A !important;
            font-size: 0.95rem !important;
            padding: 8px 12px !important;
            background-color: transparent !important;
            border: none !important;
            outline: none !important;
        }

        [data-testid="stWidgetLabel"] label {
            color: #111827 !important;
            font-weight: 600 !important;
            font-size: 0.875rem !important;
            margin-bottom: 4px !important;
        }

        /* 100% Full width Submit button */
        div[data-testid="stFormSubmitButton"],
        div.stFormSubmitButton {
            width: 100% !important;
            margin-top: 10px !important;
        }

        [data-testid="stFormSubmitButton"] button,
        button[data-testid="stBaseButton-secondaryFormSubmit"],
        button[data-testid="stBaseButton-primaryFormSubmit"],
        div.stFormSubmitButton > button {
            width: 100% !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            background-color: #111827 !important;
            color: #FFFFFF !important;
            border: 1px solid #111827 !important;
            border-radius: 6px !important;
            padding: 0.6rem 1rem !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            box-sizing: border-box !important;
        }

        [data-testid="stFormSubmitButton"] button *,
        div.stFormSubmitButton > button p,
        div.stFormSubmitButton > button span {
            color: #FFFFFF !important;
            fill: #FFFFFF !important;
            font-weight: 600 !important;
            text-align: center !important;
            width: 100% !important;
        }

        [data-testid="stFormSubmitButton"] button:hover,
        div.stFormSubmitButton > button:hover {
            background-color: #374151 !important;
            border-color: #374151 !important;
            color: #FFFFFF !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 1rem;">
                <h1 style="font-size: 2rem; font-weight: 800; color: #111827; letter-spacing: 2px; margin: 0; padding: 0;">AGROLAB</h1>
                <p style="font-size: 0.8rem; color: #64748B; font-weight: 500; letter-spacing: 1px; margin-top: 2px; margin-bottom: 0; text-transform: uppercase;">Sistema de Análisis Agronómico</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.form("login_form", clear_on_submit=False):
            st.markdown("<h3 style='margin-bottom: 2px; text-align: left;'>Iniciar Sesión</h3>", unsafe_allow_html=True)
            st.caption("Acceso al sistema corporativo de analítica")
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            
            username_input = st.text_input("Usuario", placeholder="Ingresa tu usuario")
            password_input = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
            submit_button = st.form_submit_button("Ingresar", use_container_width=True)

            if submit_button:
                if not username_input or not password_input:
                    st.error("Por favor completa todos los campos.")
                else:
                    user_data = authenticate_user(username_input, password_input)
                    if user_data:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = user_data["username"]
                        st.session_state["full_name"] = user_data["full_name"]
                        st.session_state["role"] = user_data["role"]
                        st.session_state["email"] = user_data["email"]
                        st.success(f"Bienvenido, {user_data['full_name']}")
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")

def has_permission(required_roles: list[str] | str) -> bool:
    """Checks if the logged-in user possesses any of the required roles."""
    if not st.session_state.get("authenticated", False):
        return False
        
    if isinstance(required_roles, str):
        required_roles = [required_roles]
        
    user_role = str(st.session_state.get("role", "")).strip().lower()
    allowed_roles = [str(r).strip().lower() for r in required_roles]
    
    return user_role == "admin" or user_role in allowed_roles
