import streamlit as st
from src.components.theme import render_header
from src.config.settings import load_agronomic_data
from src.modules.frequent_clients_churn import (
    calcular_volumen_por_cliente,
    calcular_alerta_churn_estacional,
)


def render_frequent_clients_churn_view():
    """Renders the Clientes Frecuentes y Churn Estacional view layout."""
    render_header(
        "Clientes Frecuentes y Churn Estacional",
        "Identificación de cuentas clave por volumen de muestras y alertas de recencia estacional."
    )

    df = load_agronomic_data()
    if df.empty:
        st.warning("No se encontraron muestras para el período seleccionado.")
        return

    # --- Filtros dinámicos: rango de fechas y especie de cultivo ---
    fecha_min = df["fecha_ing_muestra"].min().date()
    fecha_max = df["fecha_ing_muestra"].max().date()

    col_fecha, col_especie = st.columns([2, 1])
    with col_fecha:
        rango_fechas = st.date_input(
            "Rango de fechas",
            value=(fecha_min, fecha_max),
            min_value=fecha_min,
            max_value=fecha_max,
        )
    with col_especie:
        especies_disponibles = ["Todas"] + sorted(df["especies"].dropna().unique().tolist())
        especie_seleccionada = st.selectbox("Especie de cultivo", especies_disponibles)

    if len(rango_fechas) != 2:
        st.info("Seleccioná un rango de fechas completo (desde / hasta).")
        return

    fecha_inicio, fecha_fin = rango_fechas
    especie_filtro = None if especie_seleccionada == "Todas" else especie_seleccionada

    volumen = calcular_volumen_por_cliente(
        df,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        especie=especie_filtro,
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

    # --- Alerta de Churn Estacional ---
    st.markdown("#### Alerta de Churn Estacional")
    st.caption(
        "Clientes cuyo volumen de envío en el mes actual es 0% respecto a su promedio "
        "histórico para la misma época del año."
    )

    alertas = calcular_alerta_churn_estacional(df)
    clientes_en_alerta = alertas[alertas["alerta_churn_estacional"]]

    if clientes_en_alerta.empty:
        st.success("No hay clientes en alerta de churn estacional para el mes actual.")
    else:
        st.warning(f"{clientes_en_alerta.shape[0]} cliente(s) en alerta de churn estacional.")
        st.dataframe(
            clientes_en_alerta[["id_cliente", "volumen_actual", "promedio_historico_mismo_mes"]],
            use_container_width=True,
            hide_index=True,
        )
