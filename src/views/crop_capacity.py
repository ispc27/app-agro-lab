import streamlit as st
from src.components.theme import render_header

def render_crop_capacity_view():
    """Renders the Cultivos y Capacidad Operativa view layout."""
    render_header(
        "Cultivos y Capacidad Operativa",
        "Distribución por especie, evolución del volumen y alertas de saturación de laboratorio."
    )
