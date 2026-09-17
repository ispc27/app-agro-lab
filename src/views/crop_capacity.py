import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src.components.period_filter import render_period_filter
from src.components.theme import render_header
from src.config.settings import load_agronomic_data
from src.modules.common import filtrar_por_periodo
from src.modules.crop_capacity import (
    calcular_distribucion_especies,
    calcular_evolucion_mensual,
    calcular_alerta_capacidad,
    ESPECIES_EVOLUCION,
    UMBRAL_ALERTA_OPERATIVA,
    UMBRAL_CUELLO_BOTELLA,
)

COLOR_ESTADO = {
    "Normal": "#16A34A",
    "Alerta operativa": "#F59E0B",
    "Cuello de botella": "#DC2626",
}


def render_crop_capacity_view():
    """Renders the Cultivos y Capacidad Operativa view layout."""
    render_header(
        "Cultivos y Capacidad Operativa",
        "Distribución por especie, evolución del volumen y alertas de capacidad del laboratorio."
    )

    df = load_agronomic_data()
    if df.empty:
        st.warning("No se encontraron muestras para el período seleccionado.")
        return

    filtros = render_period_filter(df, key_prefix="cultivos_capacidad")
    if filtros is None:
        return
    fecha_inicio, fecha_fin, _ = filtros

    df = filtrar_por_periodo(df, fecha_inicio, fecha_fin)
    if df.empty:
        st.info("No se encontraron muestras para el período seleccionado.")
        return

    # --- KPI + distribución por especie (Top 10 + "Otras") ---
    distribucion = calcular_distribucion_especies(df, top_n=10)

    st.metric("Total de muestras acumuladas", f"{distribucion['total_muestras'].sum():,}".replace(",", "."))

    st.markdown("#### Distribución por especie (Top 10 + Otras)")
    fig_dist = px.bar(
        distribucion,
        x="especies",
        y="total_muestras",
        text="porcentaje",
        color_discrete_sequence=["#111827"],
    )
    fig_dist.update_traces(texttemplate="%{text}%", textposition="outside")
    fig_dist.update_layout(xaxis_title="", yaxis_title="Muestras", margin=dict(t=10))
    st.plotly_chart(fig_dist, use_container_width=True)

    # --- Alerta de capacidad operativa sobre el volumen total ---
    st.markdown("#### Capacidad operativa mensual (todas las especies)")
    st.caption(
        f"Alerta operativa a partir de {UMBRAL_ALERTA_OPERATIVA} muestras por mes y cuello de "
        f"botella a partir de {UMBRAL_CUELLO_BOTELLA} muestras por mes."
    )

    capacidad = calcular_alerta_capacidad(df)
    mes_actual = capacidad.iloc[-1]
    col1, col2 = st.columns(2)
    col1.metric("Muestras último mes", int(mes_actual["total_muestras"]))
    col2.metric("Estado último mes", mes_actual["estado"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=capacidad["fecha"],
        y=capacidad["total_muestras"],
        mode="lines+markers",
        line=dict(color="#111827"),
        marker=dict(color=[COLOR_ESTADO[e] for e in capacidad["estado"]], size=7),
        name="Total",
    ))
    fig.add_hline(
        y=UMBRAL_ALERTA_OPERATIVA, line_dash="dash", line_color="#F59E0B",
        annotation_text=f"{UMBRAL_ALERTA_OPERATIVA} - Alerta operativa",
    )
    fig.add_hline(
        y=UMBRAL_CUELLO_BOTELLA, line_dash="dash", line_color="#DC2626",
        annotation_text=f"{UMBRAL_CUELLO_BOTELLA} - Cuello de botella",
    )
    fig.update_layout(xaxis_title="", yaxis_title="Muestras/mes", margin=dict(t=10), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    meses_en_alerta = capacidad[capacidad["estado"] != "Normal"]
    if meses_en_alerta.empty:
        st.success("Ningún mes del período alcanzó los umbrales de capacidad operativa.")
    else:
        st.warning(f"{meses_en_alerta.shape[0]} mes(es) en alerta operativa o cuello de botella.")
        st.dataframe(
            meses_en_alerta.assign(fecha=meses_en_alerta["fecha"].dt.strftime("%m/%Y")).rename(columns={
                "fecha": "Mes",
                "total_muestras": "Muestras",
                "estado": "Estado",
            }),
            use_container_width=True,
            hide_index=True,
        )

    # --- Evolución mensual de especies principales ---
    st.markdown("#### Evolución mensual (Soja y Trigo)")
    tabs = st.tabs(ESPECIES_EVOLUCION)
    for tab, especie in zip(tabs, ESPECIES_EVOLUCION):
        with tab:
            evolucion = calcular_evolucion_mensual(df, especie)
            fig_especie = px.line(
                evolucion, x="fecha", y="total_muestras", markers=True,
                color_discrete_sequence=["#111827"],
            )
            fig_especie.update_layout(xaxis_title="", yaxis_title="Muestras/mes", margin=dict(t=10))
            st.plotly_chart(fig_especie, use_container_width=True)
