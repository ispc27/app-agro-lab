import streamlit as st

def get_current_user() -> dict:
    """Returns details for the currently logged in user from session_state."""
    is_auth = st.session_state.get("authenticated", False)
    return {
        "username": st.session_state.get("username", "") if is_auth else "",
        "full_name": st.session_state.get("full_name", "Guest") if is_auth else "Guest",
        "email": st.session_state.get("email", "") if is_auth else "",
        "role": st.session_state.get("role", "") if is_auth else "",
        "authenticated": is_auth
    }

def logout():
    """Logs out the active user and clears authentication session_state keys."""
    for key in ["authenticated", "username", "full_name", "role", "email", "active_module_id"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()
