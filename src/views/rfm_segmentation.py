import pandas as pd
import plotly.express as px
import streamlit as st
from src.components.theme import render_header, render_metric_card, render_alert_box
from src.config.settings import load_agronomic_data
from src.modules.rfm_segmentation import compute_rfm_score


def render_rfm_segmentation_view():
    """Renders the Segmentación RFM y Alerta de Fuga view layout."""
    render_header(
        "Segmentación RFM y Alerta de Fuga",
        "Clasificación de cuentas por Recencia, Frecuencia y Valor Monetario (Ciclo 25/26) y gestión de clientes en riesgo comercial."
    )

    df = load_agronomic_data()
    if df.empty:
        st.warning("No se encontraron muestras para el período seleccionado.")
        return

    min_dataset_date = df["fecha_ing_muestra"].min().date()
    max_dataset_date = df["fecha_ing_muestra"].max().date()

    col_filter1, col_filter2, col_filter3 = st.columns([2, 1, 1])

    with col_filter1:
        period_mode = st.selectbox(
            "Período de Análisis RFM",
            options=[
                "Ciclo 25/26 (Campaña Actual)",
                "Último Año (12 Meses)",
                "Últimos 6 Meses",
                "Histórico Completo",
                "Rango Personalizado",
            ],
            index=0,
            help="Prioriza la cartera de clientes para retención comercial proactiva. Al delimitar el rango de fechas, se evalúan exclusivamente las cuentas que enviaron muestras en dicho período.",
        )

    if period_mode == "Ciclo 25/26 (Campaña Actual)":
        default_start = pd.Timestamp("2025-07-01").date()
        default_end = max_dataset_date
    elif period_mode == "Último Año (12 Meses)":
        default_start = (max_dataset_date - pd.DateOffset(months=12)).date()
        default_end = max_dataset_date
    elif period_mode == "Últimos 6 Meses":
        default_start = (max_dataset_date - pd.DateOffset(months=6)).date()
        default_end = max_dataset_date
    elif period_mode == "Histórico Completo":
        default_start = min_dataset_date
        default_end = max_dataset_date
    else:
        default_start = pd.Timestamp("2025-07-01").date()
        default_end = max_dataset_date

    with col_filter2:
        start_date_input = st.date_input(
            "Desde",
            value=default_start,
            min_value=min_dataset_date,
            max_value=max_dataset_date,
            format="DD/MM/YYYY",
            disabled=(period_mode != "Rango Personalizado"),
        )
    with col_filter3:
        end_date_input = st.date_input(
            "Hasta",
            value=default_end,
            min_value=min_dataset_date,
            max_value=max_dataset_date,
            format="DD/MM/YYYY",
            disabled=(period_mode != "Rango Personalizado"),
        )

    if start_date_input > end_date_input:
        st.error("La fecha Desde no puede ser posterior a la fecha Hasta.")
        return

    start_filter = start_date_input if period_mode != "Histórico Completo" else None
    end_filter = end_date_input if period_mode != "Histórico Completo" else None

    # Compute RFM scoring across all clients
    rfm_df = compute_rfm_score(
        df,
        start_date=start_filter,
        end_date=end_filter,
        exclude_agreements=False,
    )

    if rfm_df.empty:
        st.info("No se encontraron clientes para los filtros seleccionados.")
        return

    # --- Summary KPIs & Commercial Risk Banner ---
    at_risk_df = rfm_df[rfm_df["en_riesgo"]].copy()
    at_risk_count = int(len(at_risk_df))
    at_risk_value = float(at_risk_df["valor_monetario"].sum())
    total_value = float(rfm_df["valor_monetario"].sum())
    risk_pct_value = (at_risk_value / total_value * 100) if total_value > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(render_metric_card("Clientes Segmentados", f"{rfm_df.shape[0]:,}".replace(",", ".")), unsafe_allow_html=True)
    with col2:
        st.markdown(render_metric_card("Clientes en Riesgo", f"{at_risk_count:,}".replace(",", "."), badge_text=f"{at_risk_count / len(rfm_df) * 100:.1f}% cartera", badge_bg="#FEE2E2", badge_color="#991B1B"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_metric_card("Capital en Riesgo", f"${at_risk_value:,.0f}".replace(",", "."), badge_text=f"{risk_pct_value:.1f}% facturación", badge_bg="#FEE2E2", badge_color="#991B1B"), unsafe_allow_html=True)
    with col4:
        st.markdown(render_metric_card("Facturación Total Cartera", f"${total_value:,.0f}".replace(",", ".")), unsafe_allow_html=True)

    # Clean corporate alert container without left border or emojis
    if at_risk_count > 0:
        avg_risk_inactivity = int(at_risk_df["recencia"].mean())
        alert_title = f"Alerta Comercial: {at_risk_count} Cuentas Estratégicas en Riesgo de Fuga"
        alert_msg = (
            f"Se identificaron <strong>{at_risk_count} cuentas de alto valor histórico o alta frecuencia</strong> que presentan "
            f"más de <strong>{avg_risk_inactivity} días promedio de inactividad</strong> (Recencia R ≤ 2). "
            f"El capital acumulado expuesto asciende a <strong>${at_risk_value:,.0f}</strong> ({risk_pct_value:.1f}% de la facturación del período). "
            f"Se recomienda priorizar estas cuentas para gestiones inmediatas de retención comercial."
        )
        st.markdown(render_alert_box(alert_title, alert_msg, alert_type="danger"), unsafe_allow_html=True)

    st.markdown("---")

    # =========================================================================
    # --- SECTION: Visual Portfolio Segmentation (5 Official Categories) ---
    # =========================================================================
    st.markdown("#### Segmentación de Cartera por Categorías de Negocio")
    st.caption(
        "Distribución visual de los clientes en las 5 categorías estratégicas: "
        "Campeones, Fieles / Alto Valor, Potenciales, En Riesgo y Perdidos. "
        "Permite analizar la fracción de la cartera y la contribución económica de cada segmento."
    )

    SEGMENT_ORDER = [
        "Campeones",
        "Fieles / Alto Valor",
        "Potenciales",
        "En Riesgo",
        "Perdidos",
    ]
    COLOR_PALETTE = {
        "Campeones": "#0F172A",          # Carbón profundo (máximo engagement/valor)
        "Fieles / Alto Valor": "#334155", # Pizarra oscuro (cuentas sólidas y recurrentes)
        "Potenciales": "#64748B",        # Pizarra medio (cuentas recientes en desarrollo)
        "Perdidos": "#94A3B8",           # Pizarra claro (baja actividad histórica)
        "En Riesgo": "#DC2626",          # Rojo alerta semántico (fuga de capital crítica)
    }

    tab_distrib, tab_matrix = st.tabs([
        "Distribución por Fracciones de Cartera",
        "Matriz RFM 2D (Recencia vs. Frecuencia)",
    ])

    with tab_distrib:
        col_m1, col_m2 = st.columns([1, 1])
        with col_m1:
            view_metric = st.radio(
                "Métrica de Visualización",
                options=["Facturación Acumulada ($)", "Cantidad de Clientes"],
                horizontal=True,
                key="rfm_segment_metric_toggle",
            )
        with col_m2:
            chart_kind = st.radio(
                "Tipo de Gráfico",
                options=["Barras Horizontales", "Torta (Dona)"],
                horizontal=True,
                key="rfm_segment_chart_kind",
            )

        segment_summary = rfm_df.groupby("segmento", observed=False).agg(
            clientes=("id_cliente", "count"),
            facturacion=("valor_monetario", "sum"),
        ).reindex(SEGMENT_ORDER).fillna(0).reset_index()

        segment_summary["pct_facturacion"] = (
            segment_summary["facturacion"] / total_value * 100
        ).round(1) if total_value > 0 else 0.0
        segment_summary["pct_clientes"] = (
            segment_summary["clientes"] / len(rfm_df) * 100
        ).round(1)

        val_col = "facturacion" if view_metric == "Facturación Acumulada ($)" else "clientes"
        segment_summary["text_display"] = segment_summary.apply(
            lambda r: f"${r['facturacion']:,.0f} ({r['pct_facturacion']:.1f}%)"
            if val_col == "facturacion"
            else f"{int(r['clientes']):,} ({r['pct_clientes']:.1f}%)",
            axis=1,
        )

        if chart_kind == "Barras Horizontales":
            fig_bar = px.bar(
                segment_summary,
                x=val_col,
                y="segmento",
                orientation="h",
                color="segmento",
                color_discrete_map=COLOR_PALETTE,
                text="text_display",
                labels={val_col: "Valor", "segmento": "Categoría Oficial"},
            )
            fig_bar.update_traces(textposition="outside")
            fig_bar.update_layout(
                font=dict(family="Poppins"),
                xaxis_title="Facturación Histórica Acumulada ($)" if val_col == "facturacion" else "Cantidad de Clientes",
                yaxis_title=None,
                yaxis=dict(autorange="reversed"),
                margin=dict(t=10, b=20, l=10, r=80),
                height=380,
                showlegend=False,
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            hover_tmpl = "%{label}<br>Facturación: $%{value:,.0f} (%{percent})" if val_col == "facturacion" else "%{label}<br>Clientes: %{value} (%{percent})"
            fig_donut = px.pie(
                segment_summary,
                names="segmento",
                values=val_col,
                color="segmento",
                color_discrete_map=COLOR_PALETTE,
                hole=0.48,
            )
            fig_donut.update_traces(
                textinfo="percent+label",
                hovertemplate=hover_tmpl,
            )
            fig_donut.update_layout(
                font=dict(family="Poppins"),
                margin=dict(t=20, b=20, l=20, r=20),
                height=380,
                showlegend=True,
            )
            st.plotly_chart(fig_donut, use_container_width=True)

    with tab_matrix:
        st.caption(
            "Mapeo de la cartera en la cuadrícula de Recencia (R1 = mayor inactividad, R5 = más reciente) "
            "frente a Frecuencia (F1 = menor demanda, F5 = mayor demanda). "
            "El color representa la categoría asignada y el tamaño del punto su volumen de facturación."
        )

        matrix_df = rfm_df.copy()
        import numpy as np
        np.random.seed(42)
        matrix_df["R_plot"] = matrix_df["R"] + np.random.uniform(-0.16, 0.16, size=len(matrix_df))
        matrix_df["F_plot"] = matrix_df["F"] + np.random.uniform(-0.16, 0.16, size=len(matrix_df))
        matrix_df["marker_size"] = matrix_df["valor_monetario"].clip(lower=2000, upper=300000)

        fig_matrix = px.scatter(
            matrix_df,
            x="R_plot",
            y="F_plot",
            color="segmento",
            color_discrete_map=COLOR_PALETTE,
            size="marker_size",
            hover_name="id_cliente",
            hover_data={
                "id_cliente": True,
                "segmento": True,
                "recencia": ":.0f días",
                "frecuencia": ":.0f muestras",
                "valor_monetario": ":$,.0f",
                "rfm_score": True,
                "R_plot": False,
                "F_plot": False,
                "marker_size": False,
            },
            labels={
                "R_plot": "Quintil de Recencia (R)",
                "F_plot": "Quintil de Frecuencia (F)",
                "segmento": "Categoría",
            },
        )
        fig_matrix.update_layout(
            font=dict(family="Poppins"),
            xaxis=dict(
                tickvals=[1, 2, 3, 4, 5],
                ticktext=["R1 (Inactivo)", "R2", "R3", "R4", "R5 (Reciente)"],
                title="Recencia",
            ),
            yaxis=dict(
                tickvals=[1, 2, 3, 4, 5],
                ticktext=["F1 (Baja)", "F2", "F3", "F4", "F5 (Alta Demanda)"],
                title="Frecuencia",
            ),
            height=430,
            margin=dict(t=20, b=20, l=40, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_matrix, use_container_width=True)

    st.markdown("---")

    # =========================================================================
    # --- SECTION: Urgent Contact List (At-Risk Accounts) ---
    # =========================================================================
    st.markdown("#### Listado de Contactos Urgentes — Cuentas en Riesgo de Fuga")
    st.caption(
        "Cuentas históricas de alto valor o alta frecuencia que presentan inactividad prolongada (Recencia R ≤ 2 con F o M ≥ 4). "
        "Listado priorizado para contacto comercial urgente o futuro disparo automatizado de alertas por correo."
    )

    if at_risk_df.empty:
        st.markdown(
            render_alert_box(
                "Cartera en Estado Óptimo",
                "No se registran clientes en alerta de fuga con los parámetros actuales.",
                alert_type="success",
            ),
            unsafe_allow_html=True,
        )
    else:
        at_risk_df["contribucion_riesgo"] = (
            at_risk_df["valor_monetario"] / at_risk_value * 100
        ).round(1) if at_risk_value > 0 else 0.0

        risk_display_cols = [
            "id_cliente",
            "nivel_alerta",
            "recencia",
            "frecuencia",
            "valor_monetario",
            "contribucion_riesgo",
            "rfm_score",
            "accion_recomendada",
        ]
        risk_table_df = at_risk_df[risk_display_cols].copy()
        risk_table_df["id_cliente"] = risk_table_df["id_cliente"].apply(lambda cid: f"Cliente #{cid}")
        risk_table_df.columns = [
            "ID Cliente",
            "Nivel de Prioridad",
            "Días sin Enviar",
            "Muestras Históricas",
            "Facturación ($)",
            "% del Riesgo Total",
            "Score RFM",
            "Acción Sugerida",
        ]

        def highlight_at_risk_rows(row):
            if "Crítico" in str(row["Nivel de Prioridad"]):
                return ["background-color: #FEE2E2; color: #991B1B; font-weight: 600;"] * len(row)
            return ["background-color: #FFF1F2; color: #9F1239; font-weight: 500;"] * len(row)

        styled_risk = risk_table_df.style.apply(highlight_at_risk_rows, axis=1).format({
            "Facturación ($)": "${:,.0f}",
            "Días sin Enviar": "{:,.0f} días",
            "Muestras Históricas": "{:,.0f}",
            "% del Riesgo Total": "{:.1f}%",
        })

        st.dataframe(
            styled_risk,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    # =========================================================================
    # --- SECTION: Full RFM Table (Colored & Styled by Segment) ---
    # =========================================================================
    with st.expander("Ver Segmentación RFM Completa de la Cartera (Todos los Clientes)"):
        col_f1, col_f2 = st.columns([2, 2])
        with col_f1:
            selected_segments = st.multiselect(
                "Filtrar por Categoría(s) de Negocio",
                options=SEGMENT_ORDER,
                default=[],
                placeholder="Todas las categorías...",
                help="Seleccione una o varias categorías para filtrar la tabla.",
            )
        with col_f2:
            search_query = st.text_input("Buscar por ID de Cliente", placeholder="Ej: 392...")

        filtered_full_rfm = rfm_df.copy()
        if selected_segments:
            filtered_full_rfm = filtered_full_rfm[filtered_full_rfm["segmento"].isin(selected_segments)]
        if search_query.strip():
            query_str = search_query.strip().lower()
            filtered_full_rfm = filtered_full_rfm[
                filtered_full_rfm["id_cliente"].astype(str).str.contains(query_str)
            ]

        full_display_cols = [
            "id_cliente",
            "segmento",
            "recencia",
            "frecuencia",
            "valor_monetario",
            "R",
            "F",
            "M",
            "rfm_score",
            "accion_recomendada",
        ]
        full_table_df = filtered_full_rfm[full_display_cols].copy()
        full_table_df["id_cliente"] = full_table_df["id_cliente"].apply(lambda cid: f"Cliente #{cid}")
        full_table_df.columns = [
            "ID Cliente",
            "Categoría de Cliente",
            "Días Inactivo",
            "Total Muestras",
            "Facturación ($)",
            "Quintil R",
            "Quintil F",
            "Quintil M",
            "Score RFM",
            "Estrategia Recomendada",
        ]

        def highlight_full_portfolio(row):
            seg = str(row["Categoría de Cliente"])
            if seg == "En Riesgo":
                return ["background-color: #FEE2E2; color: #991B1B; font-weight: 600;"] * len(row)
            elif seg == "Campeones":
                return ["background-color: #DCFCE7; color: #166534; font-weight: 600;"] * len(row)
            elif seg == "Fieles / Alto Valor":
                return ["background-color: #EFF6FF; color: #1E40AF;"] * len(row)
            elif seg == "Potenciales":
                return ["background-color: #FEF3C7; color: #92400E; font-weight: 500;"] * len(row)
            elif seg == "Perdidos":
                return ["background-color: #F1F5F9; color: #475569;"] * len(row)
            return [""] * len(row)

        styled_full = full_table_df.style.apply(highlight_full_portfolio, axis=1).format({
            "Facturación ($)": "${:,.0f}",
            "Días Inactivo": "{:,.0f} días",
            "Total Muestras": "{:,.0f}",
        })

        st.dataframe(
            styled_full,
            use_container_width=True,
            hide_index=True,
        )



