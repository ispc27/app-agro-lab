import streamlit as st
from src.components.period_filter import render_period_filter
from src.components.theme import render_header
from src.config.settings import load_agronomic_data
from src.modules.frequent_clients_churn import calcular_volumen_por_cliente


def render_frequent_clients_churn_view():
    """Renders the Clientes Frecuentes view layout."""
    render_header(
        "Clientes Frecuentes",
        "Identificación de cuentas clave por volumen de muestras enviadas en el período."
    )

    df = load_agronomic_data()
    if df.empty:
        st.warning("No se encontraron muestras para el período seleccionado.")
        return

    filtros = render_period_filter(df, key_prefix="clientes_frecuentes", con_especie=True)
    if filtros is None:
        return
    fecha_inicio, fecha_fin, especie = filtros

    volumen = calcular_volumen_por_cliente(
        df,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        especie=especie,
    )

    if volumen.empty:
        st.info("No se encontraron muestras para el período y/o especie seleccionados.")
        return

    # --- KPIs resumen ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Clientes con envíos", f"{volumen.shape[0]:,}".replace(",", "."))
    col2.metric("Total de muestras", f"{volumen['total_muestras'].sum():,}".replace(",", "."))
    col3.metric("Cliente líder (Id)", str(volumen.iloc[0]["id_cliente"]))

    st.markdown("#### Clientes ordenados por volumen de muestras")
    st.dataframe(volumen, use_container_width=True, hide_index=True)
