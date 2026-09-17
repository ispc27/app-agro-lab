from datetime import date

import pandas as pd
import streamlit as st
from src.modules.common import calcular_rango_predefinido

RANGOS_PREDEFINIDOS = {
    "Últimos 3 meses": 3,
    "Últimos 6 meses": 6,
    "Último año": 12,
    "Todo el período": None,
}


def _aplicar_rango_predefinido(key_prefix: str, fecha_min: date, fecha_max: date):
    """Carga en Desde/Hasta el rango del acceso rápido seleccionado."""
    rango = st.session_state.get(f"{key_prefix}_rango")
    if rango is None:
        return
    desde, hasta = calcular_rango_predefinido(fecha_min, fecha_max, RANGOS_PREDEFINIDOS[rango])
    st.session_state[f"{key_prefix}_desde"] = desde
    st.session_state[f"{key_prefix}_hasta"] = hasta


def _desmarcar_rango_si_cambio(key_prefix: str, fecha_min: date, fecha_max: date):
    """Quita la selección del acceso rápido si las fechas aplicadas ya no coinciden con él."""
    key_rango = f"{key_prefix}_rango"
    rango = st.session_state.get(key_rango)
    if rango is None:
        return
    esperado = calcular_rango_predefinido(fecha_min, fecha_max, RANGOS_PREDEFINIDOS[rango])
    actual = (st.session_state[f"{key_prefix}_desde"], st.session_state[f"{key_prefix}_hasta"])
    if actual != esperado:
        st.session_state[key_rango] = None


def render_period_filter(
    df: pd.DataFrame,
    key_prefix: str,
    rango_inicial: str = "Todo el período",
    con_especie: bool = False,
) -> tuple[date, date, str | None] | None:
    """Renderiza los accesos rápidos de período y el formulario Desde / Hasta (y especie opcional).

    Args:
        df: DataFrame limpio con columnas fecha_ing_muestra y especies.
        key_prefix: prefijo único por vista para las claves de session_state.
        rango_inicial: acceso rápido seleccionado la primera vez que se abre la vista.
        con_especie: si True, agrega un selector de especie de cultivo al formulario.

    Returns:
        Tupla (desde, hasta, especie) — especie es None si no se filtra por especie —,
        o None si el rango ingresado es inválido (ya se mostró el error).
    """
    fecha_min = df["fecha_ing_muestra"].min().date()
    fecha_max = df["fecha_ing_muestra"].max().date()
    key_rango, key_desde, key_hasta = f"{key_prefix}_rango", f"{key_prefix}_desde", f"{key_prefix}_hasta"

    if key_rango not in st.session_state:
        st.session_state[key_rango] = rango_inicial
        desde, hasta = calcular_rango_predefinido(fecha_min, fecha_max, RANGOS_PREDEFINIDOS[rango_inicial])
        st.session_state[key_desde] = desde
        st.session_state[key_hasta] = hasta

    st.segmented_control(
        "Período",
        options=list(RANGOS_PREDEFINIDOS),
        key=key_rango,
        on_change=_aplicar_rango_predefinido,
        args=(key_prefix, fecha_min, fecha_max),
        help=f"Los rangos se calculan hasta el último ingreso registrado ({fecha_max:%d/%m/%Y}).",
    )

    especie_seleccionada = "Todas"
    with st.form(f"{key_prefix}_filtros"):
        columnas = st.columns(3 if con_especie else 2)
        with columnas[0]:
            fecha_inicio = st.date_input(
                "Desde", key=key_desde, min_value=fecha_min, max_value=fecha_max, format="DD/MM/YYYY",
            )
        with columnas[1]:
            fecha_fin = st.date_input(
                "Hasta", key=key_hasta, min_value=fecha_min, max_value=fecha_max, format="DD/MM/YYYY",
            )
        if con_especie:
            especies_disponibles = ["Todas"] + sorted(df["especies"].dropna().unique().tolist())
            with columnas[2]:
                especie_seleccionada = st.selectbox(
                    "Especie de cultivo", especies_disponibles, key=f"{key_prefix}_especie",
                )
        st.form_submit_button(
            "Aplicar filtros",
            icon=":material/filter_alt:",
            on_click=_desmarcar_rango_si_cambio,
            args=(key_prefix, fecha_min, fecha_max),
        )

    if fecha_inicio > fecha_fin:
        st.error("La fecha Desde no puede ser posterior a la fecha Hasta.")
        return None

    especie = None if especie_seleccionada == "Todas" else especie_seleccionada
    return fecha_inicio, fecha_fin, especie
