import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from src.components.theme import render_header, render_metric_card, render_alert_box
from src.config.settings import load_agronomic_data
from src.modules.crop_capacity import (
    assess_capacity_alerts,
    compute_crop_distribution,
    compute_monthly_evolution,
)

STATUS_COLOR_MAP = {
    "Normal": "#10B981",
    "Alerta Operativa": "#F59E0B",
    "Cuello de Botella": "#DC2626",
}

MONTH_NAMES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}


def format_month_year_es(dt: pd.Timestamp) -> str:
    """Formats timestamp into Spanish Month Year (e.g. Julio 2020)."""
    return f"{MONTH_NAMES_ES[dt.month]} {dt.year}"


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
        dist_table_df = distribution_df.copy()
        dist_table_df.columns = ["Especie de Cultivo", "Total Muestras", "% de Participación"]
        styled_dist = dist_table_df.style.format({
            "Total Muestras": "{:,.0f}",
            "% de Participación": "{:.1f}%",
        })
        st.dataframe(
            styled_dist,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    # =========================================================================
    # --- SECTION 2: Operational Capacity & Lab Alerts (All Species) ---
    # =========================================================================
    st.markdown("#### Capacidad Operativa y Alertas del Laboratorio (Todas las Especies)")
    st.caption(
        "Monitoreo continuo de la carga operativa mensual del laboratorio consolidando todas las especies recibidas. "
        "Umbrales operativos fijos: Alerta Operativa en 142 muestras/mes (aviso preventivo) "
        "y Cuello de Botella en 191 muestras/mes (límite crítico de procesamiento)."
    )

    all_species_list = sorted(df["especies"].dropna().unique().tolist())

    col_ctrl_crops, col_ctrl_warn, col_ctrl_bottle = st.columns([3, 1, 1])

    with col_ctrl_crops:
        compare_crops = st.multiselect(
            "Especies Opcionales para Contrastar con el Total",
            options=all_species_list,
            default=[],
            placeholder="Seleccione especies si desea contrastar su curva individual con el total...",
            help="El estado operativo y las alertas siempre se evalúan sobre la suma total de muestras del laboratorio. Puede seleccionar especies para visualizar sus curvas individuales superpuestas.",
        )

    with col_ctrl_warn:
        warning_thresh = st.number_input(
            "Alerta Operativa (m./mes)",
            min_value=1.0,
            value=142.0,
            step=10.0,
            help="Umbral operativo que marca el inicio de sobrecarga operativa (color amarillo). Definido en 142 muestras por mes.",
            key="warning_thresh_input",
        )

    with col_ctrl_bottle:
        bottleneck_thresh = st.number_input(
            "Cuello de Botella (m./mes)",
            min_value=1.0,
            value=191.0,
            step=10.0,
            help="Umbral operativo crítico donde se generan demoras y saturación de analistas (color rojo). Definido en 191 muestras por mes.",
            key="bottleneck_thresh_input",
        )

    # Capacity alerts evaluated strictly on consolidated laboratory volume
    evolution_df, _ = assess_capacity_alerts(
        df,
        crop_species=None,
        warning_threshold=warning_thresh,
        bottleneck_threshold=bottleneck_thresh,
    )

    latest_month = (
        evolution_df.iloc[-1]
        if not evolution_df.empty
        else {"total_muestras": 0, "porcentaje_capacidad": 0.0, "estado": "Normal"}
    )
    latest_status = str(latest_month["estado"])

    status_bg = (
        "#DCFCE7"
        if latest_status == "Normal"
        else ("#FEF3C7" if latest_status == "Alerta Operativa" else "#FEE2E2")
    )
    status_fg = (
        "#166534"
        if latest_status == "Normal"
        else ("#92400E" if latest_status == "Alerta Operativa" else "#991B1B")
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            render_metric_card(
                "Muestras Último Mes",
                f"{int(latest_month['total_muestras']):,}".replace(",", "."),
            ),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            render_metric_card(
                "Alerta Operativa",
                f"{int(warning_thresh):,} / mes".replace(",", "."),
                badge_text="Preventivo",
                badge_bg="#FEF3C7",
                badge_color="#92400E",
            ),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            render_metric_card(
                "Cuello de Botella",
                f"{int(bottleneck_thresh):,} / mes".replace(",", "."),
                badge_text="Crítico",
                badge_bg="#FEE2E2",
                badge_color="#991B1B",
            ),
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            render_metric_card(
                "Estado Actual",
                latest_status,
                badge_text="Último Período",
                badge_bg=status_bg,
                badge_color=status_fg,
            ),
            unsafe_allow_html=True,
        )

    # Operational Capacity Chart (All Species Consolidated)
    fig_evo = go.Figure()

    # Total Consolidated trace
    total_evo = compute_monthly_evolution(df, None)
    total_evo["fecha_es"] = total_evo["fecha"].apply(format_month_year_es)
    fig_evo.add_trace(go.Scatter(
        x=total_evo["fecha"],
        y=total_evo["total_muestras"],
        customdata=total_evo["fecha_es"],
        mode="lines+markers",
        line=dict(color="#111827", width=3),
        marker=dict(size=5),
        name="Total Consolidado Laboratorio (Todas las Especies)",
        hovertemplate="<b>Total Consolidado</b><br>Fecha: %{customdata}<br>Muestras: %{y:,}<extra></extra>",
    ))

    # Optional comparison crops
    crop_palette = {
        "Soja": "#10B981",
        "Trigo": "#2563EB",
        "Maíz": "#F59E0B",
        "Girasol": "#8B5CF6",
        "Cebada": "#EC4899",
        "Sorgo": "#06B6D4",
    }
    fallback_colors = ["#64748B", "#84CC16", "#D97706", "#0D9488", "#6366F1", "#A855F7"]

    for idx, crop_name in enumerate(compare_crops):
        crop_evo = compute_monthly_evolution(df, crop_name)
        crop_evo["fecha_es"] = crop_evo["fecha"].apply(format_month_year_es)
        line_color = crop_palette.get(crop_name, fallback_colors[idx % len(fallback_colors)])

        fig_evo.add_trace(go.Scatter(
            x=crop_evo["fecha"],
            y=crop_evo["total_muestras"],
            customdata=crop_evo["fecha_es"],
            mode="lines+markers",
            line=dict(color=line_color, width=2, dash="dot"),
            marker=dict(size=5),
            name=f"{crop_name} (Individual)",
            hovertemplate=f"<b>{crop_name}</b><br>Fecha: %{{customdata}}<br>Muestras: %{{y:,}}<extra></extra>",
        ))

    # Warning threshold line (142 m.)
    fig_evo.add_hline(
        y=warning_thresh,
        line_dash="dash",
        line_color="#F59E0B",
        line_width=2,
        annotation_text=f"Alerta Operativa ({int(warning_thresh)} m.)",
        annotation_position="top left",
    )

    # Bottleneck threshold line (191 m.)
    fig_evo.add_hline(
        y=bottleneck_thresh,
        line_dash="dash",
        line_color="#DC2626",
        line_width=2,
        annotation_text=f"Cuello de Botella ({int(bottleneck_thresh)} m.)",
        annotation_position="top left",
    )

    fig_evo.update_layout(
        font=dict(family="Poppins"),
        xaxis_title="Fecha",
        yaxis_title="Muestras / Mes",
        margin=dict(t=30, b=20),
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_evo, use_container_width=True)

    # Historical Alert Months Audit Table
    alert_months = evolution_df[evolution_df["estado"] != "Normal"].copy()
    if not alert_months.empty:
        has_bottleneck = (alert_months["estado"] == "Cuello de Botella").any()
        alert_type = "danger" if has_bottleneck else "warning"
        alert_title = (
            f"Alerta Operativa: {alert_months.shape[0]} Meses en Cuello de Botella / Sobrecarga"
            if has_bottleneck
            else f"Alerta Operativa: {alert_months.shape[0]} Meses en Umbral Preventivo"
        )
        alert_msg = (
            f"Se registraron <strong>{alert_months.shape[0]} meses históricos en estado de sobrecarga operativa</strong> "
            f"(Alerta Operativa ≥ {int(warning_thresh)} m. o Cuello de Botella ≥ {int(bottleneck_thresh)} m.) "
            f"considerando el volumen consolidado del laboratorio. "
            f"Se recomienda planificar refuerzo de capacidad técnica y turnos de guardia durante dichos períodos."
        )
        st.markdown(render_alert_box(alert_title, alert_msg, alert_type=alert_type), unsafe_allow_html=True)

        alert_months["fecha_str"] = alert_months["fecha"].apply(format_month_year_es)
        alert_display_df = alert_months[["fecha_str", "total_muestras", "porcentaje_capacidad", "estado"]].copy()
        alert_display_df.columns = ["Mes / Año", "Muestras Totales", "% Capacidad Cuello de Botella", "Estado Operativo"]

        def highlight_alert_months(row):
            st_val = str(row["Estado Operativo"])
            if st_val == "Cuello de Botella":
                return ["background-color: #FEE2E2; color: #991B1B; font-weight: 600;"] * len(row)
            elif st_val == "Alerta Operativa":
                return ["background-color: #FEF3C7; color: #92400E; font-weight: 500;"] * len(row)
            return [""] * len(row)

        styled_alert_months = alert_display_df.style.apply(highlight_alert_months, axis=1).format({
            "Muestras Totales": "{:,.0f}",
            "% Capacidad Cuello de Botella": "{:.1f}%",
        })

        with st.expander("Ver Auditoría Detallada de Meses en Alerta Operativa", expanded=False):
            st.dataframe(
                styled_alert_months,
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.markdown(
            render_alert_box(
                "Capacidad Operativa Normal",
                f"No se registraron meses con sobrecarga de capacidad bajo los umbrales configurados "
                f"({int(warning_thresh)} m. alerta operativa / {int(bottleneck_thresh)} m. cuello de botella).",
                alert_type="success",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # =========================================================================
    # --- SECTION 3: Seasonality Pattern: Wheat & Soybean (NO ALERTS) ---
    # =========================================================================
    st.markdown("#### Patrón de Estacionalidad: Trigo y Soja")
    st.caption(
        "Visualización de los ciclos agronómicos continuos de Trigo y Soja (zafras, baches y picos de demanda). "
        "Estos dos cultivos concentran el 72.0% del volumen total del laboratorio. "
        "Este análisis no incluye líneas de alerta operativa, ya que los límites corresponden a la capacidad global del laboratorio."
    )

    col_seas_sel, _ = st.columns([2, 2])
    with col_seas_sel:
        selected_seas_crops = st.multiselect(
            "Cultivos en Análisis de Estacionalidad",
            options=["Soja", "Trigo"],
            default=["Soja", "Trigo"],
            placeholder="Seleccione Soja, Trigo o ambos...",
            help="Seleccione ambos cultivos para observar la alternancia semestral de zafras (fina vs. gruesa).",
        )

    # Seasonality Plot WITHOUT ALERTS
    if selected_seas_crops:
        fig_seas = go.Figure()
        seas_colors = {
            "Soja": "#10B981",  # Verde esmeralda
            "Trigo": "#2563EB",  # Azul corporativo
        }

        for crop_name in selected_seas_crops:
            crop_evo = compute_monthly_evolution(df, crop_name)
            crop_evo["fecha_es"] = crop_evo["fecha"].apply(format_month_year_es)
            line_color = seas_colors.get(crop_name, "#111827")
            line_dash = "solid" if crop_name == "Soja" else "dash"

            fig_seas.add_trace(go.Scatter(
                x=crop_evo["fecha"],
                y=crop_evo["total_muestras"],
                customdata=crop_evo["fecha_es"],
                mode="lines+markers",
                line=dict(color=line_color, width=2.5, dash=line_dash),
                marker=dict(size=6),
                name=f"Evolución {crop_name}",
                hovertemplate=f"<b>{crop_name}</b><br>Mes: %{{customdata}}<br>Muestras: %{{y:,}}<extra></extra>",
            ))

        fig_seas.update_layout(
            font=dict(family="Poppins"),
            xaxis_title="Fecha",
            yaxis_title="Cantidad de Muestras",
            margin=dict(t=30, b=20),
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_seas, use_container_width=True)
    else:
        st.info("Seleccione al menos un cultivo (Soja o Trigo) para visualizar la curva de estacionalidad.")


