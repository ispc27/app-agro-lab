import streamlit as st
from src.components.theme import render_header
from src.config.settings import load_agronomic_data
from src.modules.frequent_clients_churn import (
    calcular_volumen_por_cliente,
    calcular_alerta_churn_estacional,
    calcular_rango_predefinido,
)

RANGOS_PREDEFINIDOS = {
    "Últimos 3 meses": 3,
    "Últimos 6 meses": 6,
    "Último año": 12,
    "Todo el período": None,
}
KEY_RANGO = "clientes_frecuentes_rango"
KEY_DESDE = "clientes_frecuentes_desde"
KEY_HASTA = "clientes_frecuentes_hasta"


def _aplicar_rango_predefinido(fecha_min, fecha_max):
    """Carga en Desde/Hasta el rango del acceso rápido seleccionado."""
    rango = st.session_state.get(KEY_RANGO)
    if rango is None:
        return
    desde, hasta = calcular_rango_predefinido(fecha_min, fecha_max, RANGOS_PREDEFINIDOS[rango])
    st.session_state[KEY_DESDE] = desde
    st.session_state[KEY_HASTA] = hasta


def _desmarcar_rango_si_cambio(fecha_min, fecha_max):
    """Quita la selección del acceso rápido si las fechas aplicadas ya no coinciden con él."""
    rango = st.session_state.get(KEY_RANGO)
    if rango is None:
        return
    esperado = calcular_rango_predefinido(fecha_min, fecha_max, RANGOS_PREDEFINIDOS[rango])
    if (st.session_state[KEY_DESDE], st.session_state[KEY_HASTA]) != esperado:
        st.session_state[KEY_RANGO] = None


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

    # --- Filtros dinámicos: accesos rápidos de período, fecha desde / hasta y especie ---
    fecha_min = df["fecha_ing_muestra"].min().date()
    fecha_max = df["fecha_ing_muestra"].max().date()
    especies_disponibles = ["Todas"] + sorted(df["especies"].dropna().unique().tolist())

    st.session_state.setdefault(KEY_RANGO, "Todo el período")
    st.session_state.setdefault(KEY_DESDE, fecha_min)
    st.session_state.setdefault(KEY_HASTA, fecha_max)

    st.segmented_control(
        "Período",
        options=list(RANGOS_PREDEFINIDOS),
        key=KEY_RANGO,
        on_change=_aplicar_rango_predefinido,
        args=(fecha_min, fecha_max),
        help=f"Los rangos se calculan hasta el último ingreso registrado ({fecha_max:%d/%m/%Y}).",
    )

    with st.form("filtros_clientes_frecuentes"):
        col_desde, col_hasta, col_especie = st.columns(3)
        with col_desde:
            fecha_inicio = st.date_input(
                "Desde",
                key=KEY_DESDE,
                min_value=fecha_min,
                max_value=fecha_max,
                format="DD/MM/YYYY",
            )
        with col_hasta:
            fecha_fin = st.date_input(
                "Hasta",
                key=KEY_HASTA,
                min_value=fecha_min,
                max_value=fecha_max,
                format="DD/MM/YYYY",
            )
        with col_especie:
            especie_seleccionada = st.selectbox("Especie de cultivo", especies_disponibles)
        st.form_submit_button(
            "Aplicar filtros",
            icon=":material/filter_alt:",
            on_click=_desmarcar_rango_si_cambio,
            args=(fecha_min, fecha_max),
        )

    if fecha_inicio > fecha_fin:
        st.error("La fecha Desde no puede ser posterior a la fecha Hasta.")
        return

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
