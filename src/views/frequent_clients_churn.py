import pandas as pd
import plotly.express as px
import streamlit as st
from src.components.theme import render_header, render_metric_card
from src.config.settings import load_agronomic_data
from src.modules.frequent_clients_churn import (
    compute_volume_by_client,
)


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

    col_species, col_status, col_profile = st.columns([2, 1, 1])
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
            "Estado de actividad",
            options=["Todos", "Activos", "Inactivos"],
            index=0,
            help="Criterio: Activo = registra al menos 1 envío en la ventana seleccionada. Inactivo = cuenta histórica sin envíos en el período.",
        )
    with col_profile:
        client_profile = st.selectbox(
            "Tipo de cliente",
            options=["Todos", "Estacional", "Mixto"],
            index=0,
            help="Criterio agronómico: Estacional = monocultivo o envíos en 1-2 meses de campaña. Mixto = multicultivo o actividad en 3 o más meses.",
        )

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
        client_profile=client_profile,
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
    leader_label = f"Cliente #{top_row['id_cliente']}" if top_row is not None else "Sin envíos"
    leader_pct = float(top_row["porcentaje_total"]) if top_row is not None else 0.0
    leader_vol = int(top_row["total_muestras"]) if top_row is not None else 0

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
                leader_label,
                badge_text=f"{leader_pct:.1f}% ({leader_vol:,} m.)".replace(",", "."),
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

    # --- Charts Section: Top 10 + Behavior Profile Distribution ---
    col_chart_top, col_chart_profile = st.columns([3, 2])

    with col_chart_top:
        st.markdown("#### Top 10 Clientes por Volumen de Muestras")
        top_10_df = volume_df.head(10).sort_values("total_muestras", ascending=True).copy()
        top_10_df["cliente_label"] = top_10_df["id_cliente"].apply(lambda cid: f"Cliente #{cid}")

        if top_10_df["total_muestras"].sum() == 0:
            st.info("Todos los clientes en esta selección registran 0 muestras en el período seleccionado.")
        else:
            fig_top = px.bar(
                top_10_df,
                x="total_muestras",
                y="cliente_label",
                orientation="h",
                text="total_muestras",
                labels={"total_muestras": "Cantidad de Muestras", "cliente_label": "Cliente"},
                color_discrete_sequence=["#111827"],
            )
            fig_top.update_traces(
                texttemplate="%{text:,}",
                textposition="outside",
                hovertemplate="Cliente: %{y}<br>Muestras: %{x:,}<extra></extra>",
            )
            fig_top.update_layout(
                font=dict(family="Poppins"),
                showlegend=False,
                height=350,
                margin=dict(l=90, r=40, t=10, b=20),
                xaxis_title="Volumen de Muestras",
                yaxis_title=None,
            )
            st.plotly_chart(fig_top, use_container_width=True)

    with col_chart_profile:
        st.markdown("#### Distribución por Comportamiento (Estacional vs. Mixto)")
        profile_counts = volume_df["tipo_cliente"].value_counts().reset_index()
        profile_counts.columns = ["tipo_cliente", "cantidad"]

        fig_profile = px.pie(
            profile_counts,
            names="tipo_cliente",
            values="cantidad",
            hole=0.52,
            color="tipo_cliente",
            color_discrete_map={
                "Estacional": "#1E293B",
                "Mixto": "#64748B",
            },
        )
        fig_profile.update_traces(textinfo="percent+label", textposition="outside")
        fig_profile.update_layout(
            font=dict(family="Poppins"),
            height=350,
            margin=dict(t=20, b=20, l=10, r=10),
            showlegend=False,
        )
        st.plotly_chart(fig_profile, use_container_width=True)

    # --- Detailed Client Table with Pandas Styler ---
    st.markdown("#### Listado Completo de Clientes Ordenado por Volumen")
    st.caption("Detalle de las cuentas clientes ordenadas descendentemente por cantidad de muestras enviadas en el período.")

    col_search, _ = st.columns([2, 2])
    with col_search:
        search_kw = st.text_input("Buscar por ID de Cliente", placeholder="Ej: 392...")

    filtered_clients = volume_df.copy()
    if search_kw.strip():
        kw = search_kw.strip().lower()
        filtered_clients = filtered_clients[
            filtered_clients["id_cliente"].astype(str).str.contains(kw)
        ]

    display_cols = ["id_cliente", "total_muestras", "porcentaje_total", "estado_cliente", "tipo_cliente", "dias_inactivo"]
    table_df = filtered_clients[display_cols].copy()
    table_df.columns = ["ID Cliente", "Total Muestras", "% de Participación", "Estado", "Tipo de Cliente", "Recencia (Días)"]

    def highlight_client_status(row):
        st_val = str(row["Estado"])
        if st_val == "Activo":
            return ["background-color: #DCFCE7; color: #166534; font-weight: 500;"] * len(row)
        return ["background-color: #F8FAFC; color: #64748B;"] * len(row)

    styled_clients = table_df.style.apply(highlight_client_status, axis=1).format({
        "Total Muestras": "{:,.0f}",
        "% de Participación": "{:.2f}%",
        "Recencia (Días)": "{:,.0f} d.",
    })

    st.dataframe(
        styled_clients,
        use_container_width=True,
        hide_index=True,
    )
