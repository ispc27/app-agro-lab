import pandas as pd
import plotly.express as px
import streamlit as st
from src.components.theme import render_header
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

    col_filter1, col_filter2, col_filter3, col_filter4 = st.columns([2, 1, 1, 1])

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
    with col_filter4:
        exclude_agreements = st.checkbox(
            "Excluir convenios (ID > 50.000)",
            value=True,
            help="Las cuentas de convenio institucional se excluyen del scoring individual.",
        )

    if start_date_input > end_date_input:
        st.error("La fecha Desde no puede ser posterior a la fecha Hasta.")
        return

    start_filter = start_date_input if period_mode != "Histórico Completo" else None
    end_filter = end_date_input if period_mode != "Histórico Completo" else None

    # Compute RFM scoring
    rfm_df = compute_rfm_score(
        df,
        start_date=start_filter,
        end_date=end_filter,
        exclude_agreements=exclude_agreements,
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

    def render_metric_card(label: str, value: str, badge_text: str | None = None, badge_bg: str = "#FEE2E2", badge_color: str = "#991B1B") -> str:
        badge_html = f'<span style="background-color: {badge_bg}; color: {badge_color}; font-size: 0.72rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; white-space: nowrap;">{badge_text}</span>' if badge_text else ""
        return f'<div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px 18px; min-height: 98px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02);"><div style="color: #64748B; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">{label}</div><div style="display: flex; align-items: baseline; gap: 8px; flex-wrap: nowrap;"><span style="color: #111827; font-size: 1.55rem; font-weight: 700; line-height: 1.2;">{value}</span>{badge_html}</div></div>'

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
        alert_card_html = (
            f'<div style="background-color: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; padding: 16px 22px; margin: 15px 0 25px 0;">'
            f'<div style="margin-bottom: 6px;"><strong style="color: #991B1B; font-size: 1.05rem; letter-spacing: -0.01em; text-transform: uppercase;">'
            f'Alerta Comercial: {at_risk_count} Cuentas Estratégicas en Riesgo de Fuga</strong></div>'
            f'<div style="color: #7F1D1D; font-size: 0.92rem; line-height: 1.5;">'
            f'Se identificaron <strong>{at_risk_count} cuentas de alto valor histórico o alta frecuencia</strong> que presentan '
            f'más de <strong>{avg_risk_inactivity} días promedio de inactividad</strong> (Recencia R ≤ 2). '
            f'El capital acumulado expuesto asciende a <strong>${at_risk_value:,.0f}</strong> ({risk_pct_value:.1f}% de la facturación del período). '
            f'Se recomienda priorizar estas cuentas para gestiones inmediatas de retención.</div></div>'
        )
        st.markdown(alert_card_html, unsafe_allow_html=True)


    st.markdown("---")

    # --- Visual Analytics: Strategic Matrix & Portfolio Segments ---
    st.markdown("#### Matriz Estratégica RFM y Análisis de Cartera")
    st.caption(
        "Distribución bidimensional del valor comercial frente a la inactividad temporal. Las cuentas en la zona de riesgo "
        "combinan alta facturación acumulada con prolongada inactividad."
    )

    # Cohesive corporate palette consistent with system alert thresholds (Red alert for risk, dark slate/charcoal for segments)
    color_palette = {
        "En Riesgo de Fuga": "#DC2626",         # Alerta crítica de fuga (Rojo)
        "Clientes Clave": "#111827",            # Carbón oscuro principal
        "Clientes Fieles": "#334155",           # Pizarra oscuro
        "Nuevos / Prometedores": "#64748B",     # Pizarra medio
        "Inactivos de Bajo Impacto": "#94A3B8", # Pizarra claro
    }


    tab_scatter, tab_segments = st.tabs([
        "Matriz Estratégica (Recencia vs. Facturación)",
        "Segmentación de Cartera (Impacto Económico)",
    ])

    with tab_scatter:
        scatter_df = rfm_df.copy()
        scatter_df["marker_size"] = scatter_df["frecuencia"].clip(lower=3, upper=100)

        fig_scatter = px.scatter(
            scatter_df,
            x="recencia",
            y="valor_monetario",
            size="marker_size",
            color="segmento",
            color_discrete_map=color_palette,
            hover_name="razon_social",
            hover_data={
                "id_cliente": True,
                "recencia": ":.0f días",
                "frecuencia": ":.0f muestras",
                "valor_monetario": ":$,.0f",
                "rfm_score": True,
                "segmento": True,
                "marker_size": False,
            },
            labels={
                "recencia": "Recencia (Días sin actividad)",
                "valor_monetario": "Facturación Histórica ($)",
                "segmento": "Segmento Comercial",
                "frecuencia": "Muestras Históricas",
                "rfm_score": "Score RFM",
            },
        )

        fig_scatter.update_layout(
            font=dict(family="Poppins"),
            xaxis_title="Días de Inactividad (Recencia)",
            yaxis_title="Facturación Histórica Acumulada ($)",
            legend_title="Segmento Comercial",
            height=460,
            margin=dict(t=25, b=20, l=40, r=20),
            hovermode="closest",
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.caption(
            "Guía de lectura: El tamaño de cada burbuja indica el volumen total de muestras procesadas. "
            "Las burbujas en color rojo (En Riesgo de Fuga) en la zona superior derecha señalan las cuentas de mayor volumen que han dejado de operar recientemente."
        )

    with tab_segments:
        segment_summary = rfm_df.groupby("segmento").agg(
            clientes=("id_cliente", "count"),
            facturacion=("valor_monetario", "sum"),
        ).reset_index()

        segment_summary["pct_facturacion"] = (segment_summary["facturacion"] / total_value * 100).round(1) if total_value > 0 else 0
        segment_summary["pct_clientes"] = (segment_summary["clientes"] / len(rfm_df) * 100).round(1)

        view_metric = st.radio(
            "Métrica de Visualización de Cartera",
            options=["Facturación Acumulada ($)", "Cantidad de Clientes"],
            horizontal=True,
            key="rfm_segment_metric_toggle",
        )

        val_col = "facturacion" if view_metric == "Facturación Acumulada ($)" else "clientes"
        hover_tmpl = "%{label}<br>Facturación: $%{value:,.0f} (%{percent})" if val_col == "facturacion" else "%{label}<br>Clientes: %{value} (%{percent})"

        fig_donut = px.pie(
            segment_summary,
            names="segmento",
            values=val_col,
            color="segmento",
            color_discrete_map=color_palette,
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

    st.markdown("---")

    # --- Priority Churn Risk Table (Colored & Styled) ---
    st.markdown("#### Listado Prioritario de Clientes en Riesgo de Fuga")
    st.caption(
        "Cuentas con baja recencia (quintil R 1 o 2) pero alta frecuencia o alto valor histórico (quintiles F o M 4 o 5). "
        "Ordenadas por facturación descendente para priorizar la gestión comercial de recupero."
    )

    if at_risk_df.empty:
        st.success("No se registran clientes en alerta de fuga con los parámetros actuales.")
    else:
        at_risk_df["contribucion_riesgo"] = (at_risk_df["valor_monetario"] / at_risk_value * 100).round(1) if at_risk_value > 0 else 0.0

        risk_display_cols = [
            "id_cliente",
            "razon_social",
            "nivel_alerta",
            "recencia",
            "frecuencia",
            "valor_monetario",
            "contribucion_riesgo",
            "rfm_score",
        ]
        risk_table_df = at_risk_df[risk_display_cols].copy()
        risk_table_df.columns = [
            "ID Cliente",
            "Razón Social",
            "Nivel de Alerta",
            "Días Inactivo",
            "Muestras Históricas",
            "Facturación ($)",
            "% del Riesgo Total",
            "Score RFM",
        ]

        def highlight_at_risk_rows(row):
            if "Crítico" in str(row["Nivel de Alerta"]):
                return ["background-color: #FEE2E2; color: #991B1B; font-weight: 600;"] * len(row)
            return ["background-color: #FFF1F2; color: #9F1239; font-weight: 500;"] * len(row)

        styled_risk = risk_table_df.style.apply(highlight_at_risk_rows, axis=1).format({
            "Facturación ($)": "${:,.0f}",
            "Días Inactivo": "{:,.0f} días",
            "Muestras Históricas": "{:,.0f}",
            "% del Riesgo Total": "{:.1f}%",
        })

        st.dataframe(
            styled_risk,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    # --- Full RFM Table (Colored & Styled by Segment) ---
    with st.expander("Ver Segmentación RFM Completa de la Cartera (Todos los Clientes)"):
        col_f1, col_f2 = st.columns([2, 2])
        with col_f1:
            segment_options = sorted(rfm_df["segmento"].unique().tolist())
            selected_segments = st.multiselect(
                "Filtrar por Segmento(s) Comercial(es)",
                options=segment_options,
                default=[],
                placeholder="Todos los segmentos",
                help="Seleccione uno o varios segmentos. Si se deja vacío, se muestran todos los segmentos.",
            )
        with col_f2:
            search_query = st.text_input("Buscar por ID o Razón Social", placeholder="Ej: 350 o Agro...")

        filtered_full_rfm = rfm_df.copy()
        if selected_segments:
            filtered_full_rfm = filtered_full_rfm[filtered_full_rfm["segmento"].isin(selected_segments)]
        if search_query.strip():
            query_str = search_query.strip().lower()
            filtered_full_rfm = filtered_full_rfm[
                filtered_full_rfm["id_cliente"].astype(str).str.contains(query_str) |
                filtered_full_rfm["razon_social"].astype(str).str.lower().str.contains(query_str)
            ]

        full_display_cols = [
            "id_cliente",
            "razon_social",
            "segmento",
            "recencia",
            "frecuencia",
            "valor_monetario",
            "R",
            "F",
            "M",
            "rfm_score",
        ]
        full_table_df = filtered_full_rfm[full_display_cols].copy()
        full_table_df.columns = [
            "ID Cliente",
            "Razón Social",
            "Segmento Comercial",
            "Días Inactivo",
            "Total Muestras",
            "Facturación ($)",
            "Quintil R",
            "Quintil F",
            "Quintil M",
            "Score RFM",
        ]

        def highlight_full_portfolio(row):
            seg = str(row["Segmento Comercial"])
            if "En Riesgo" in seg:
                return ["background-color: #FEE2E2; color: #991B1B; font-weight: 600;"] * len(row)
            elif "Clientes Clave" in seg:
                return ["background-color: #DCFCE7; color: #166534; font-weight: 500;"] * len(row)
            elif "Clientes Fieles" in seg:
                return ["background-color: #EFF6FF; color: #1E40AF;"] * len(row)
            elif "Nuevos" in seg or "Prometedores" in seg:
                return ["background-color: #FEF3C7; color: #92400E; font-weight: 500;"] * len(row)
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

    # --- 5x5 Heatmap Matrix: Recency vs. Frequency ---
    with st.expander("Ver Matriz Térmica 5x5 de Concentración RF (Recencia vs. Frecuencia)", expanded=False):
        st.markdown("##### Distribución Matricial de Quintiles RF")
        st.caption(
            "La matriz térmica 5x5 resume las 25 intersecciones operativas entre Recencia y Frecuencia. "
            "El cuadrante superior izquierdo (R1-R2 con F4-F5) concentra a las cuentas de mayor volumen que dejaron de operar (riesgo de fuga), "
            "mientras que el cuadrante superior derecho (R4-R5 con F4-F5) agrupa a los clientes más activos y regulares."
        )

        view_heatmap = st.radio(
            "Métrica de la Matriz RF",
            options=["Cantidad de Clientes", "Facturación Acumulada ($)"],
            horizontal=True,
            key="rfm_heatmap_metric_toggle",
        )

        if view_heatmap == "Cantidad de Clientes":
            rf_counts = pd.crosstab(
                index=rfm_df["F"],
                columns=rfm_df["R"],
                values=rfm_df["id_cliente"],
                aggfunc="count",
            ).reindex(index=[5, 4, 3, 2, 1], columns=[1, 2, 3, 4, 5], fill_value=0)

            fig_heatmap = px.imshow(
                rf_counts,
                labels=dict(x="Quintil de Recencia (R)", y="Quintil de Frecuencia (F)", color="Clientes"),
                x=["R1 (Mayor Inactividad)", "R2", "R3", "R4", "R5 (Más Reciente)"],
                y=["F5 (Mayor Demanda)", "F4", "F3", "F2", "F1 (Menor Demanda)"],
                color_continuous_scale="Greys",
                text_auto=True,
                aspect="auto",
            )
        else:
            rf_billing = pd.crosstab(
                index=rfm_df["F"],
                columns=rfm_df["R"],
                values=rfm_df["valor_monetario"],
                aggfunc="sum",
            ).reindex(index=[5, 4, 3, 2, 1], columns=[1, 2, 3, 4, 5], fill_value=0)

            text_billing = rf_billing.map(lambda v: f"${v:,.0f}" if v > 0 else "$0")

            fig_heatmap = px.imshow(
                rf_billing,
                labels=dict(x="Quintil de Recencia (R)", y="Quintil de Frecuencia (F)", color="Facturación ($)"),
                x=["R1 (Mayor Inactividad)", "R2", "R3", "R4", "R5 (Más Reciente)"],
                y=["F5 (Mayor Demanda)", "F4", "F3", "F2", "F1 (Menor Demanda)"],
                color_continuous_scale="Greys",
                aspect="auto",
            )
            fig_heatmap.update_traces(text=text_billing.values, texttemplate="%{text}")

        fig_heatmap.update_layout(
            font=dict(family="Poppins"),
            margin=dict(t=25, b=25, l=40, r=20),
            height=370,
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)


