import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src.components.theme import render_header
from src.config.settings import load_agronomic_data
from src.modules.crop_capacity import (
    CRITICAL_CROPS,
    assess_capacity_alerts,
    compute_crop_distribution,
    compute_monthly_evolution,
)

STATUS_COLOR_MAP = {
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

    total_dataset_samples = df["id_muestra"].nunique()

    # --- KPI + Crop Species Distribution (Top 10 + "Otras") ---
    distribution_df = compute_crop_distribution(df, top_n=10)
    sum_table_samples = distribution_df["total_muestras"].sum()

    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Total Muestras Acumuladas", f"{sum_table_samples:,}".replace(",", "."))
    col_kpi2.metric("Especies Registradas", f"{df['especies'].nunique():,}".replace(",", "."))
    
    top_crop_name = distribution_df.iloc[0]["especies"]
    top_crop_pct = distribution_df.iloc[0]["porcentaje"]
    col_kpi3.metric("Cultivo Predominante", f"{top_crop_name}", delta=f"{top_crop_pct:.1f}% del total", delta_color="off")

    st.markdown("---")
    
    col_header, col_toggle = st.columns([3, 1])
    with col_header:
        st.markdown("#### Distribución por Especie de Cultivo (Top 10 + Otras)")
    with col_toggle:
        chart_type = st.radio(
            "Tipo de Gráfico",
            options=["Barras", "Torta (Dona)"],
            horizontal=True,
            label_visibility="collapsed",
        )

    if chart_type == "Barras":
        fig_dist = px.bar(
            distribution_df,
            x="especies",
            y="total_muestras",
            text="porcentaje",
            color_discrete_sequence=["#111827"],
            labels={"especies": "Especie de Cultivo", "total_muestras": "Total Muestras"},
        )
        fig_dist.update_traces(texttemplate="%{text}%", textposition="outside")
        fig_dist.update_layout(
            font=dict(family="Poppins"),
            xaxis_title=None,
            yaxis_title="Cantidad de Muestras",
            margin=dict(t=20, b=20),
            height=380,
        )
        st.plotly_chart(fig_dist, use_container_width=True)
    else:
        fig_pie = px.pie(
            distribution_df,
            names="especies",
            values="total_muestras",
            hole=0.4,
            color_discrete_sequence=[
                "#111827", "#1F2937", "#374151", "#4B5563", "#6B7280",
                "#9CA3AF", "#D1D5DB", "#E5E7EB", "#94A3B8", "#CBD5E1", "#64748B"
            ],
        )
        fig_pie.update_traces(textinfo="percent+label")
        fig_pie.update_layout(font=dict(family="Poppins"), height=400, margin=dict(t=20, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    with st.expander("Ver Tabla Detallada de Distribución de Especies"):
        st.dataframe(
            distribution_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "especies": st.column_config.TextColumn("Especie de Cultivo"),
                "total_muestras": st.column_config.NumberColumn("Total Muestras", format="%d"),
                "porcentaje": st.column_config.NumberColumn("% Participación", format="%.1f %%"),
            },
        )

    st.markdown("---")

    # --- Monthly Evolution & Capacity Alerts for Critical Crops ---
    st.markdown("#### Evolución Mensual y Alertas de Capacidad (Soja y Trigo)")
    st.caption(
        "Línea de tendencia continua mensual sin huecos temporales. "
        "Umbrales operativos: Advertencia al 75% del volumen crítico y Saturación al 90%."
    )

    tabs = st.tabs(CRITICAL_CROPS + ["Vista Comparativa Soja vs Trigo"])
    
    # Render individual tabs for Soja and Trigo
    for tab, crop_species in zip(tabs[:2], CRITICAL_CROPS):
        with tab:
            base_evolution, max_hist_capacity = assess_capacity_alerts(df, crop_species)
            
            # Interactive What-If Simulator for Critical Capacity
            col_sim1, col_sim2 = st.columns([2, 2])
            with col_sim1:
                custom_capacity = st.number_input(
                    f"Capacidad Crítica Mensual de Referencia ({crop_species})",
                    min_value=1.0,
                    value=float(max_hist_capacity),
                    step=10.0,
                    help="Ajuste este valor para simular escenarios de sobrecarga u optimización operativa.",
                    key=f"cap_input_{crop_species}",
                )
            
            evolution_df, critical_capacity = assess_capacity_alerts(
                df, crop_species, critical_capacity=custom_capacity
            )

            latest_month = evolution_df.iloc[-1]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Muestras Último Mes", int(latest_month["total_muestras"]))
            c2.metric("Capacidad Crítica Ref.", f"{int(critical_capacity)} / mes")
            c3.metric(
                "Uso de Capacidad Último Mes",
                f"{latest_month['porcentaje_capacidad']:.1f}%",
            )
            c4.metric(
                "Estado Operativo",
                latest_month["estado"],
            )

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=evolution_df["fecha"],
                y=evolution_df["total_muestras"],
                mode="lines+markers",
                line=dict(color="#111827", width=2),
                marker=dict(
                    color=[STATUS_COLOR_MAP[e] for e in evolution_df["estado"]],
                    size=8,
                ),
                name=crop_species,
                hovertemplate="Fecha: %{x|%b %Y}<br>Muestras: %{y}<extra></extra>",
            ))
            
            # 75% Warning threshold line
            fig.add_hline(
                y=critical_capacity * 0.75,
                line_dash="dash",
                line_color="#F59E0B",
                annotation_text=f"75% Advertencia ({critical_capacity * 0.75:.0f} m.)",
                annotation_position="top left",
            )
            
            # 90% Saturation threshold line
            fig.add_hline(
                y=critical_capacity * 0.90,
                line_dash="dash",
                line_color="#DC2626",
                annotation_text=f"90% Saturación ({critical_capacity * 0.90:.0f} m.)",
                annotation_position="top left",
            )
            
            fig.update_layout(
                font=dict(family="Poppins"),
                xaxis_title="Fecha",
                yaxis_title="Muestras / Mes",
                margin=dict(t=30, b=20),
                showlegend=False,
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

            alert_months = evolution_df[evolution_df["estado"] != "Normal"].copy()
            if not alert_months.empty:
                st.warning(f"{alert_months.shape[0]} mes(es) registrado(s) en estado de Advertencia o Saturación para {crop_species}.")
                
                alert_months["fecha_str"] = alert_months["fecha"].dt.strftime("%B %Y")
                
                st.dataframe(
                    alert_months[["fecha_str", "total_muestras", "porcentaje_capacidad", "estado"]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "fecha_str": st.column_config.TextColumn("Mes / Año"),
                        "total_muestras": st.column_config.NumberColumn("Muestras Ingresadas", format="%d"),
                        "porcentaje_capacidad": st.column_config.NumberColumn("% Capacidad Usada", format="%.1f %%"),
                        "estado": st.column_config.TextColumn("Estado Operativo"),
                    },
                )
            else:
                st.success(f"No se registraron meses con sobrecarga de capacidad para {crop_species} bajo la capacidad seleccionada.")

    # Comparative view tab
    with tabs[2]:
        st.markdown("##### Comparativa Temporal Continuada — Soja vs Trigo")
        soja_evo = compute_monthly_evolution(df, "Soja")
        trigo_evo = compute_monthly_evolution(df, "Trigo")
        
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Scatter(
            x=soja_evo["fecha"],
            y=soja_evo["total_muestras"],
            mode="lines",
            name="Soja",
            line=dict(color="#111827", width=2),
        ))
        fig_comp.add_trace(go.Scatter(
            x=trigo_evo["fecha"],
            y=trigo_evo["total_muestras"],
            mode="lines",
            name="Trigo",
            line=dict(color="#6B7280", width=2, dash="dash"),
        ))
        fig_comp.update_layout(
            font=dict(family="Poppins"),
            xaxis_title="Fecha",
            yaxis_title="Muestras / Mes",
            height=380,
            margin=dict(t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_comp, use_container_width=True)
