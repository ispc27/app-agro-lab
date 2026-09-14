import os
import sys
import streamlit as st

# Allow imports from project root directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.auth import render_login_form, has_permission
from src.components.sidebar import render_sidebar
from src.components.theme import apply_enterprise_theme
from src.views.frequent_clients_churn import render_frequent_clients_churn_view
from src.views.crop_capacity import render_crop_capacity_view
from src.views.rfm_segmentation import render_rfm_segmentation_view

st.set_page_config(
    page_title="AgroLab Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global enterprise theme & Poppins typography
apply_enterprise_theme()

# Flow Control: Login vs Corporate Dashboard Sidebar
if not st.session_state.get("authenticated"):
    render_login_form()
else:
    # Render Corporate Sidebar & get active module selection
    selected_page_id = render_sidebar()

    # Dynamic routing according to selected module & role permissions
    if selected_page_id == "frequent_clients_churn":
        if has_permission(["admin", "responsable_laboratorio", "responsable_rrii"]):
            render_frequent_clients_churn_view()
        else:
            st.error("No tienes permisos suficientes para acceder al módulo de Clientes y Churn.")
    elif selected_page_id == "crop_capacity":
        if has_permission(["admin", "responsable_laboratorio", "analista_laboratorio"]):
            render_crop_capacity_view()
        else:
            st.error("No tienes permisos suficientes para acceder al módulo de Cultivos y Capacidad.")
    elif selected_page_id == "rfm_segmentation":
        if has_permission(["admin", "responsable_rrii", "comercial"]):
            render_rfm_segmentation_view()
        else:
            st.error("No tienes permisos suficientes para acceder al módulo de Segmentación RFM.")
    else:
        st.info("Seleccione un módulo válido desde la barra lateral.")
