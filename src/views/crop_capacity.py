import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from src.components.theme import render_header
from src.config.settings import load_agronomic_data
from src.modules.crop_capacity import (
    CRITICAL_CROPS,
    assess_capacity_alerts,
    compute_crop_distribution,
    compute_monthly_evolution,
    compute_critical_intervals,
)

STATUS_COLOR_MAP = {
    "Normal": "#10B981",
    "Advertencia": "#F59E0B",
    "Saturación": "#DC2626",
}

MONTH_NAMES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}


def format_month_year_es(dt: pd.Timestamp) -> str:
    """Formats timestamp into Spanish Month Year (e.g. Julio 2020)."""
    return f"{MONTH_NAMES_ES[dt.month]} {dt.year}"


def render_metric_card(label: str, value: str, badge_text: str | None = None, badge_bg: str = "#EFF6FF", badge_color: str = "#1E40AF") -> str:
    badge_html = f'<span style="background-color: {badge_bg}; color: {badge_color}; font-size: 0.72rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; white-space: nowrap;">{badge_text}</span>' if badge_text else ""
    return f'<div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px 18px; min-height: 98px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02);"><div style="color: #64748B; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">{label}</div><div style="display: flex; align-items: baseline; gap: 8px; flex-wrap: nowrap;"><span style="color: #111827; font-size: 1.55rem; font-weight: 700; line-height: 1.2;">{value}</span>{badge_html}</div></div>'


def render_crop_capacity_view():
    """Renders the Cultivos y Capacidad Operativa view layout."""
    render_header(
        "Cultivos y Capacidad Operativa",
        "Distribución por especie, evolución del volumen mensual continuo y alertas de capacidad operativa del laboratorio."
    )

    df_raw = load_agronomic_data()
    if df_raw.empty:
        st.warning("No se encontraron muestras en el conjunto de datos.")
        return

    # --- Global Date Filter for Entire Module ---
    min_date = df_raw["fecha_ing_muestra"].min().date()
    max_date = df_raw["fecha_ing_muestra"].max().date()

    col_filter_preset, col_filter_start, col_filter_end = st.columns([2, 1, 1])

    with col_filter_preset:
        preset = st.selectbox(
            "Filtro por Período de Tiempo",
            options=["Todo el Histórico", "Ciclo 25/26", "Último Año", "Últimos 6 Meses", "Personalizado"],
            index=0,
            help="Seleccione un rango rápido de fechas para filtrar todas las visualizaciones del módulo.",
        )

    if preset == "Ciclo 25/26":
        start_val = pd.Timestamp("2025-07-01").date()
        end_val = max_date
    elif preset == "Último Año":
        start_val = (pd.Timestamp(max_date) - pd.DateOffset(years=1)).date()
        end_val = max_date
    elif preset == "Últimos 6 Meses":
        start_val = (pd.Timestamp(max_date) - pd.DateOffset(months=6)).date()
        end_val = max_date
    elif preset == "Personalizado":
        start_val = min_date
        end_val = max_date
    else:  # Todo el Histórico
        start_val = min_date
        end_val = max_date

    with col_filter_start:
        start_date = st.date_input(
            "Fecha Desde",
            value=start_val,
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY",
            disabled=(preset != "Personalizado"),
        )
    with col_filter_end:
        end_date = st.date_input(
            "Fecha Hasta",
            value=end_val,
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY",
            disabled=(preset != "Personalizado"),
        )

    if start_date > end_date:
        st.error("La fecha Desde no puede ser posterior a la fecha Hasta.")
        return

    # Filter dataframe globally for this view
    df = df_raw[
        (df_raw["fecha_ing_muestra"].dt.date >= start_date)
        & (df_raw["fecha_ing_muestra"].dt.date <= end_date)
    ].copy()

    if df.empty:
        st.warning("No existen muestras registradas en el rango de fechas seleccionado.")
        return

    # --- KPI + Crop Species Distribution (Top 10 + "Otras") ---
    distribution_df = compute_crop_distribution(df, top_n=10)
    sum_table_samples = distribution_df["total_muestras"].sum()

    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        st.markdown(
            render_metric_card(
                "Total Muestras Acumuladas",
                f"{sum_table_samples:,}".replace(",", "."),
            ),
            unsafe_allow_html=True,
        )
    with col_kpi2:
        st.markdown(
            render_metric_card(
                "Especies Registradas",
                f"{df['especies'].nunique():,}".replace(",", "."),
            ),
            unsafe_allow_html=True,
        )
    with col_kpi3:
        if not distribution_df.empty and distribution_df.iloc[0]["total_muestras"] > 0:
            top_crop_name = distribution_df.iloc[0]["especies"]
            top_crop_pct = distribution_df.iloc[0]["porcentaje"]
            st.markdown(
                render_metric_card(
                    "Cultivo Predominante",
                    f"{top_crop_name}",
                    badge_text=f"{top_crop_pct:.1f}% del total",
                    badge_bg="#EFF6FF",
                    badge_color="#1E40AF",
                ),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                render_metric_card("Cultivo Predominante", "Sin datos"),
                unsafe_allow_html=True,
            )

    st.markdown("---")
    col_dist_title, col_dist_toggle = st.columns([3, 1])
    with col_dist_title:
        st.markdown("#### Distribución por Especie de Cultivo (Top 10 y Otras)")
        st.caption(
            "Resumen del volumen total acumulado por especie de cultivo en el período seleccionado, "
            "mostrando las 10 principales y agrupando el resto en 'Otras'."
        )
    with col_dist_toggle:
        chart_type = st.radio(
            "Tipo de Gráfico",
            options=["Barras", "Torta (Dona)"],
            horizontal=True,
            label_visibility="collapsed",
            key="crop_dist_chart_type",
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
            hole=0.48,
            color_discrete_sequence=[
                "#111827", "#1E293B", "#334155", "#475569", "#64748B",
                "#94A3B8", "#CBD5E1", "#E2E8F0", "#F1F5F9"
            ],
        )
        fig_pie.update_traces(textinfo="percent+label")
        fig_pie.update_layout(font=dict(family="Poppins"), height=400, margin=dict(t=20, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    with st.expander("Ver Tabla Detallada de Distribución de Especies"):
        styled_dist = distribution_df.style.format({
            "total_muestras": "{:,.0f}",
            "porcentaje": "{:.1f}%",
        })
        st.dataframe(
            styled_dist,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    # --- Monthly Evolution & Operational Capacity Alerts ---
    st.markdown("#### Evolución Mensual y Alertas de Capacidad Operativa")
    st.caption(
        "Línea de tendencia mensual continua sin saltos de tiempo. "
        "Umbrales operativos de laboratorio: Advertencia al 75% del volumen crítico y Saturación al 90%. "
        "Soja y Trigo se encuentran anclados por defecto como cultivos principales; puede seleccionar cualquier otra especie para incorporar al análisis."
    )

    all_species_list = sorted(df["especies"].dropna().unique().tolist())
    default_crops = [s for s in ["Soja", "Trigo"] if s in all_species_list]

    col_ctrl_crops, col_ctrl_cap = st.columns([3, 2])

    with col_ctrl_crops:
        selected_crops = st.multiselect(
            "Cultivos a Visualizar",
            options=all_species_list,
            default=default_crops,
            placeholder="Seleccione uno o varios cultivos...",
            help="Soja y Trigo se encuentran preseleccionados por defecto. Puede agregar o remover cultivos según su análisis.",
        )
        show_consolidated = st.checkbox(
            "Superponer Total Consolidado del Laboratorio",
            value=True,
            help="Muestra la curva con la sumatoria de todas las especies procesadas en el laboratorio.",
        )

    # Reference data for capacity alert assessment
    # If consolidated is checked, base alerts on full lab volume; otherwise on the selected crops
    active_crop_selection = None if show_consolidated else (selected_crops if selected_crops else None)
    base_evo, max_hist_capacity = assess_capacity_alerts(df, active_crop_selection)

    with col_ctrl_cap:
        custom_capacity = st.number_input(
            "Capacidad Crítica Mensual (Ref. 100%)",
            min_value=1.0,
            value=float(max_hist_capacity),
            step=50.0,
            help="Volumen mensual límite (100%) para el cálculo de alertas operativas. Modifique este valor para simular escenarios de sobrecarga.",
            key="cap_input_unified",
        )
        scope_label = "Total Consolidado Laboratorio" if show_consolidated else ("Cultivos Seleccionados" if selected_crops else "Total Laboratorio")
        st.caption(
            f"**Referencia ({scope_label}):** {int(max_hist_capacity):,} muestras/mes "
            f"(máximo histórico registrado en el período)."
        )

    evolution_df, critical_capacity = assess_capacity_alerts(
        df, active_crop_selection, critical_capacity=custom_capacity
    )

    latest_month = evolution_df.iloc[-1] if not evolution_df.empty else {"total_muestras": 0, "porcentaje_capacidad": 0.0, "estado": "Normal"}
    latest_status = str(latest_month["estado"])

    status_bg = "#DCFCE7" if latest_status == "Normal" else ("#FEF3C7" if latest_status == "Advertencia" else "#FEE2E2")
    status_fg = "#166534" if latest_status == "Normal" else ("#92400E" if latest_status == "Advertencia" else "#991B1B")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(render_metric_card("Muestras Último Mes", f"{int(latest_month['total_muestras']):,}"), unsafe_allow_html=True)
    with c2:
        st.markdown(render_metric_card("Capacidad Crítica Ref.", f"{int(critical_capacity):,} / mes"), unsafe_allow_html=True)
    with c3:
        st.markdown(render_metric_card("Uso de Capacidad", f"{latest_month['porcentaje_capacidad']:.1f}%"), unsafe_allow_html=True)
    with c4:
        st.markdown(render_metric_card("Estado Operativo", latest_status, badge_text="Actual", badge_bg=status_bg, badge_color=status_fg), unsafe_allow_html=True)

    # Unified Evolution Chart
    fig_evo = go.Figure()

    if show_consolidated:
        total_evo = compute_monthly_evolution(df, None)
        total_evo["fecha_es"] = total_evo["fecha"].apply(format_month_year_es)
        fig_evo.add_trace(go.Scatter(
            x=total_evo["fecha"],
            y=total_evo["total_muestras"],
            customdata=total_evo["fecha_es"],
            mode="lines+markers",
            line=dict(color="#111827", width=3),
            marker=dict(size=5),
            name="Total Consolidado Laboratorio",
            hovertemplate="<b>Total Consolidado</b><br>Fecha: %{customdata}<br>Muestras: %{y:,}<extra></extra>",
        ))

    crop_palette = {
        "Soja": "#10B981",
        "Trigo": "#2563EB",
        "Maíz": "#F59E0B",
        "Girasol": "#8B5CF6",
        "Cebada": "#EC4899",
        "Sorgo": "#06B6D4",
    }
    fallback_colors = ["#64748B", "#84CC16", "#D97706", "#0D9488", "#6366F1", "#A855F7"]

    for idx, crop_name in enumerate(selected_crops):
        crop_evo = compute_monthly_evolution(df, crop_name)
        crop_evo["fecha_es"] = crop_evo["fecha"].apply(format_month_year_es)
        line_color = crop_palette.get(crop_name, fallback_colors[idx % len(fallback_colors)])
        line_dash = "dash" if crop_name == "Trigo" else "solid"

        fig_evo.add_trace(go.Scatter(
            x=crop_evo["fecha"],
            y=crop_evo["total_muestras"],
            customdata=crop_evo["fecha_es"],
            mode="lines+markers",
            line=dict(color=line_color, width=2, dash=line_dash),
            marker=dict(size=6),
            name=crop_name,
            hovertemplate=f"<b>{crop_name}</b><br>Fecha: %{{customdata}}<br>Muestras: %{{y:,}}<extra></extra>",
        ))

    # 75% Warning threshold line
    fig_evo.add_hline(
        y=critical_capacity * 0.75,
        line_dash="dash",
        line_color="#F59E0B",
        annotation_text=f"75% Advertencia ({critical_capacity * 0.75:.0f} m.)",
        annotation_position="top left",
    )

    # 90% Saturation threshold line
    fig_evo.add_hline(
        y=critical_capacity * 0.90,
        line_dash="dash",
        line_color="#DC2626",
        annotation_text=f"90% Saturación ({critical_capacity * 0.90:.0f} m.)",
        annotation_position="top left",
    )

    if not show_consolidated and not selected_crops:
        st.info("Seleccione al menos un cultivo o active el Total Consolidado para visualizar la serie temporal.")

    fig_evo.update_layout(
        font=dict(family="Poppins"),
        xaxis_title="Fecha",
        yaxis_title="Muestras / Mes",
        margin=dict(t=30, b=20),
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_evo, use_container_width=True)

    alert_months = evolution_df[evolution_df["estado"] != "Normal"].copy()
    if not alert_months.empty:
        st.info(f"Se registraron {alert_months.shape[0]} mes(es) en estado de Advertencia o Saturación para el volumen evaluado.")

        alert_months["fecha_str"] = alert_months["fecha"].apply(format_month_year_es)
        alert_display_df = alert_months[["fecha_str", "total_muestras", "porcentaje_capacidad", "estado"]].copy()
        alert_display_df.columns = ["Mes / Año", "Muestras Ingresadas", "% Capacidad Usada", "Estado Operativo"]

        def highlight_alert_months(row):
            st_val = str(row["Estado Operativo"])
            if st_val == "Saturación":
                return ["background-color: #FEE2E2; color: #991B1B; font-weight: 600;"] * len(row)
            elif st_val == "Advertencia":
                return ["background-color: #FEF3C7; color: #92400E; font-weight: 500;"] * len(row)
            return [""] * len(row)

        styled_alert_months = alert_display_df.style.apply(highlight_alert_months, axis=1).format({
            "Muestras Ingresadas": "{:,.0f}",
            "% Capacidad Usada": "{:.1f}%",
        })

        st.dataframe(
            styled_alert_months,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("No se registraron meses con sobrecarga de capacidad bajo el límite configurado.")

    st.markdown("---")
    st.markdown("#### Intervalos Críticos de Demanda por Cultivo y Tipo de Ensayo")
    st.caption(
        "Identificación de las determinaciones analíticas de mayor demanda para optimizar la dotación de personal, "
        "turnos de guardia y stock de insumos del laboratorio."
    )

    # Use selected crops if any are selected, otherwise standard critical crops (Soja y Trigo)
    interval_crops = [c for c in selected_crops if c in ["Soja", "Trigo"]] if any(c in ["Soja", "Trigo"] for c in selected_crops) else (selected_crops[:2] if selected_crops else CRITICAL_CROPS)
    if not interval_crops:
        interval_crops = CRITICAL_CROPS

    intervals_df = compute_critical_intervals(df, interval_crops)

    col_int_list = st.columns(len(interval_crops))
    for idx, crop in enumerate(interval_crops):
        col_target = col_int_list[idx]
        with col_target:
            st.markdown(f"##### Ensayos Críticos — {crop}")
            crop_int = intervals_df[intervals_df["especies"] == crop].head(6).copy()

            if not crop_int.empty:
                crop_color = crop_palette.get(crop, "#111827")
                fig_crop_int = px.bar(
                    crop_int,
                    x="total_muestras",
                    y="tipo_analisis",
                    orientation="h",
                    text="porcentaje_cultivo",
                    color_discrete_sequence=[crop_color],
                    labels={"total_muestras": "Muestras", "tipo_analisis": "Tipo de Ensayo"},
                )
                fig_crop_int.update_traces(texttemplate="%{text}%", textposition="outside")
                fig_crop_int.update_layout(
                    font=dict(family="Poppins"),
                    xaxis_title="Cantidad de Muestras",
                    yaxis_title=None,
                    yaxis=dict(autorange="reversed"),
                    height=300,
                    margin=dict(l=10, r=40, t=10, b=20),
                )
                st.plotly_chart(fig_crop_int, use_container_width=True)

                styled_crop_int = crop_int[["tipo_analisis", "total_muestras", "porcentaje_cultivo"]].copy()
                styled_crop_int.columns = ["Tipo de Ensayo", "Muestras", "% Demanda Cultivo"]
                styled_crop_int_display = styled_crop_int.style.format({
                    "Muestras": "{:,.0f}",
                    "% Demanda Cultivo": "{:.1f}%",
                })

                st.dataframe(
                    styled_crop_int_display,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info(f"No hay muestras registradas para {crop} en el período seleccionado.")


