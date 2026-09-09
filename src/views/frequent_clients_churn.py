import streamlit as st
from src.components.theme import render_header

def render_frequent_clients_churn_view():
    """Renders the Clientes Frecuentes y Churn Estacional view layout."""
    render_header(
        "Clientes Frecuentes y Churn Estacional",
        "Identificación de cuentas clave por volumen de muestras y alertas de recencia estacional."
    )
