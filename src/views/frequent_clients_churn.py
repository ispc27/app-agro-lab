import pandas as pd
import plotly.express as px
import streamlit as st
from src.components.theme import render_header
from src.config.settings import load_agronomic_data
from src.modules.frequent_clients_churn import (
    compute_volume_by_client,
)


def render_metric_card(label: str, value: str, badge_text: str | None = None, badge_bg: str = "#EFF6FF", badge_color: str = "#1E40AF") -> str:
    badge_html = f'<span style="background-color: {badge_bg}; color: {badge_color}; font-size: 0.72rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; white-space: nowrap;">{badge_text}</span>' if badge_text else ""
    return f'<div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px 18px; min-height: 98px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02);"><div style="color: #64748B; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">{label}</div><div style="display: flex; align-items: baseline; gap: 8px; flex-wrap: nowrap;"><span style="color: #111827; font-size: 1.55rem; font-weight: 700; line-height: 1.2;">{value}</span>{badge_html}</div></div>'


def render_frequent_clients_churn_view():
    """Renders the Identificación de Clientes Frecuentes view layout (HU-01 / Objetivo 1)."""
    render_header(
        "Identificación de Clientes Frecuentes",
        "Listado interactivo de cuentas frecuentes ordenadas por volumen de muestras, con filtros dinámicos por período y especie de cultivo."
    )

    df = load_agronomic_data()
    if df.empty:
        st.warning("No se encontraron muestras para el período seleccionado.")
        return

    min_date = df["fecha_ing_muestra"].min().date()
    max_date = df["fecha_ing_muestra"].max().date()
    available_species = sorted(df["especies"].dropna().unique().tolist())

    # --- Top Filter Panel ---
    col_filter_preset, col_filter_start, col_filter_end = st.columns([2, 1, 1])

    with col_filter_preset:
        preset = st.selectbox(
            "Filtro por Período de Tiempo",
            options=["Todo el Histórico", "Ciclo 25/26", "Último Año", "Últimos 6 Meses", "Personalizado"],
            index=0,
            help="Seleccione un rango rápido de fechas para filtrar la cartera de clientes.",
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
        start_date_input = st.date_input(
            "Fecha Desde",
            value=start_val,
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY",
            disabled=(preset != "Personalizado"),
        )
    with col_filter_end:
        end_date_input = st.date_input(
            "Fecha Hasta",
            value=end_val,
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY",
            disabled=(preset != "Personalizado"),
        )

    col_species, col_status, col_convenio = st.columns([2, 2, 2])
    with col_species:
        selected_species = st.multiselect(
            "Especie(s) de cultivo",
            options=available_species,
            default=[],
            placeholder="Todas las especies",
            help="Seleccione una o varias especies. Si se deja vacío, se consideran todas las especies de la cartera.",
        )
    with col_status:
        client_status = st.selectbox(
            "Estado del cliente",
            options=["Todos", "Activos", "Inactivos"],
            index=0,
            help="Filtrar por clientes con envíos en la ventana (Activos) o sin envíos en la ventana (Inactivos).",
        )
    with col_convenio:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        exclude_agreements = st.checkbox("Excluir convenios (ID > 50.000)", value=False)

    if start_date_input > end_date_input:
        st.error("La fecha Desde no puede ser posterior a la fecha Hasta.")
        return

    species_filter = selected_species if selected_species else None

    volume_df = compute_volume_by_client(
        df,
        start_date=start_date_input,
        end_date=end_date_input,
        crop_species=species_filter,
        client_status=client_status,
        exclude_agreements=exclude_agreements,
    )

    if volume_df.empty:
        st.info("No se encontraron muestras para los filtros seleccionados.")
        return

    # --- Summary KPIs ---
    total_clients = volume_df.shape[0]
    active_count = int((volume_df["estado_cliente"] == "Activo").sum()) if "estado_cliente" in volume_df.columns else total_clients
    active_pct = (active_count / total_clients * 100) if total_clients > 0 else 0.0
    total_muestras_sum = int(volume_df["total_muestras"].sum())

    top_row = volume_df[volume_df["total_muestras"] > 0].iloc[0] if not volume_df[volume_df["total_muestras"] > 0].empty else None
    leader_name = str(top_row["razon_social"]) if top_row is not None else "Sin envíos"
    leader_pct = float(top_row["porcentaje_total"]) if top_row is not None else 0.0

    avg_active_samples = (total_muestras_sum / active_count) if active_count > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            render_metric_card(
                "Clientes en Cartera",
                f"{total_clients:,}".replace(",", "."),
                badge_text=f"{active_pct:.1f}% activos",
                badge_bg="#DCFCE7",
                badge_color="#166534",
            ),
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            render_metric_card(
                "Total de Muestras",
                f"{total_muestras_sum:,}".replace(",", "."),
            ),
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            render_metric_card(
                "Cliente Líder",
                leader_name[:20] + ("..." if len(leader_name) > 20 else ""),
                badge_text=f"{leader_pct:.1f}% del total",
                badge_bg="#EFF6FF",
                badge_color="#1E40AF",
            ),
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            render_metric_card(
                "Promedio / Cliente Activo",
                f"{avg_active_samples:.1f} m.",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # --- Top 10 Plotly Chart ---
    st.markdown("#### Top 10 Clientes por Volumen de Muestras")
    top_10_df = volume_df.head(10).sort_values("total_muestras", ascending=True).copy()

    def _format_client_label(row):
        rz = str(row.get("razon_social", "")).strip()
        cid = row["id_cliente"]
        if rz and rz.upper() not in ["NN", "NAN", "NONE"]:
            return f"{rz} ({cid})"
        return f"Cliente {cid}"

    top_10_df["cliente_label"] = top_10_df.apply(_format_client_label, axis=1)

    if top_10_df["total_muestras"].sum() == 0:
        st.info("Todos los clientes en esta selección registran 0 muestras ingresadas en el período seleccionado (cuentas inactivas).")
    else:
        fig = px.bar(
            top_10_df,
            x="total_muestras",
            y="cliente_label",
            orientation="h",
            text="total_muestras",
            labels={"total_muestras": "Cantidad de Muestras", "cliente_label": "Cliente"},
            color_discrete_sequence=["#111827"],
        )
        fig.update_traces(
            texttemplate="%{text:,}",
            textposition="outside",
            hovertemplate="Cliente: %{y}<br>Muestras: %{x:,}<extra></extra>",
        )
        fig.update_layout(
            font=dict(family="Poppins"),
            showlegend=False,
            height=380,
            margin=dict(l=110, r=40, t=20, b=20),
            xaxis_title="Volumen de Muestras",
            yaxis_title=None,
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- Detailed Client Table with Pandas Styler ---
    st.markdown("#### Listado Completo de Clientes Ordenado por Volumen")
    st.caption("Detalle de las cuentas clientes ordenadas descendentemente por cantidad de muestras enviadas en el período.")

    col_search, _ = st.columns([2, 2])
    with col_search:
        search_kw = st.text_input("Buscar cliente por ID o Razón Social", placeholder="Ej: 105 o Agro...")

    filtered_clients = volume_df.copy()
    if search_kw.strip():
        kw = search_kw.strip().lower()
        filtered_clients = filtered_clients[
            filtered_clients["id_cliente"].astype(str).str.contains(kw)
            | filtered_clients["razon_social"].astype(str).str.lower().str.contains(kw)
        ]

    display_cols = ["id_cliente", "razon_social", "total_muestras", "porcentaje_total", "estado_cliente"]
    table_df = filtered_clients[display_cols].copy()
    table_df.columns = ["ID Cliente", "Razón Social", "Total Muestras", "% de Participación", "Estado"]

    def highlight_client_status(row):
        if str(row["Estado"]) == "Activo":
            return ["background-color: #DCFCE7; color: #166534; font-weight: 500;"] * len(row)
        return ["background-color: #F8FAFC; color: #64748B;"] * len(row)

    styled_clients = table_df.style.apply(highlight_client_status, axis=1).format({
        "Total Muestras": "{:,.0f}",
        "% de Participación": "{:.2f}%",
    })

    st.dataframe(
        styled_clients,
        use_container_width=True,
        hide_index=True,
    )
