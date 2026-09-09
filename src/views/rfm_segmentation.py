import streamlit as st
from src.components.theme import render_header

def render_rfm_segmentation_view():
    """Renders the Segmentación RFM y Alerta de Fuga view layout."""
    render_header(
        "Segmentación RFM y Alerta de Fuga",
        "Pipeline de scoring RFM de cuentas y listado prioritario de clientes en riesgo para gestión comercial."
    )
