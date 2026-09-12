import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src.components.theme import render_header
from src.config.settings import load_agronomic_data
from src.modules.crop_capacity import (
    calcular_distribucion_especies,
    calcular_evolucion_mensual,
    calcular_alerta_capacidad,
    ESPECIES_CRITICAS,
)

COLOR_ESTADO = {
    "Normal": "#16A34A",
    "Advertencia": "#F59E0B",
    "Saturación": "#DC2626",
}


def render_crop_capacity_view():
    """Renders the Cultivos y Capacidad Operativa view layout."""
    render_header(
        "Cultivos y Capacidad Operativa",
        "Distribución por especie, evolución del volumen y alertas de saturación de laboratorio."
    )

    df = load_agronomic_data()
    if df.empty:
        st.warning("No se encontraron muestras para el período seleccionado.")
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

    # --- Evolución mensual y alerta de capacidad para especies críticas ---
    st.markdown("#### Evolución mensual y capacidad operativa (Soja y Trigo)")
    st.caption(
        "La capacidad crítica de referencia (100%) es el máximo histórico mensual de cada "
        "especie. Advertencia a partir del 75%, saturación a partir del 90%."
    )

    tabs = st.tabs(ESPECIES_CRITICAS)
    for tab, especie in zip(tabs, ESPECIES_CRITICAS):
        with tab:
            evolucion, capacidad_critica = calcular_alerta_capacidad(df, especie)

            mes_actual = evolucion.iloc[-1]
            col1, col2, col3 = st.columns(3)
            col1.metric("Muestras último mes", int(mes_actual["total_muestras"]))
            col2.metric("Capacidad crítica (ref.)", int(capacidad_critica))
            col3.metric(
                "Estado último mes",
                mes_actual["estado"],
                delta=f"{mes_actual['porcentaje_capacidad']:.0f}% de capacidad",
                delta_color="off",
            )

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=evolucion["fecha"],
                y=evolucion["total_muestras"],
                mode="lines+markers",
                line=dict(color="#111827"),
                marker=dict(
                    color=[COLOR_ESTADO[e] for e in evolucion["estado"]],
                    size=7,
                ),
                name=especie,
            ))
            fig.add_hline(
                y=capacidad_critica * 0.75, line_dash="dash", line_color="#F59E0B",
                annotation_text="75% - Advertencia",
            )
            fig.add_hline(
                y=capacidad_critica * 0.90, line_dash="dash", line_color="#DC2626",
                annotation_text="90% - Saturación",
            )
            fig.update_layout(
                xaxis_title="", yaxis_title="Muestras/mes", margin=dict(t=10), showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

            meses_en_alerta = evolucion[evolucion["estado"] != "Normal"]
            if not meses_en_alerta.empty:
                st.warning(f"{meses_en_alerta.shape[0]} mes(es) en advertencia o saturación para {especie}.")
                st.dataframe(
                    meses_en_alerta[["fecha", "total_muestras", "porcentaje_capacidad", "estado"]],
                    use_container_width=True,
                    hide_index=True,
                )
