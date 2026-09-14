import plotly.express as px
import streamlit as st
from src.components.theme import render_header
from src.config.settings import load_agronomic_data
from src.modules.frequent_clients_churn import (
    compute_predefined_date_range,
    compute_volume_by_client,
    detect_seasonal_churn_alerts,
)

MONTH_NAMES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

PREDEFINED_RANGES = {
    "Últimos 3 meses": 3,
    "Últimos 6 meses": 6,
    "Último año": 12,
    "Todo el período": None,
}
KEY_RANGE = "frequent_clients_range"
KEY_FROM = "frequent_clients_from"
KEY_TO = "frequent_clients_to"


def _apply_predefined_range(min_date, max_date):
    """Loads the start/end dates for the selected quick-select period."""
    selected_range = st.session_state.get(KEY_RANGE)
    if selected_range is None:
        return
    start_date, end_date = compute_predefined_date_range(min_date, max_date, PREDEFINED_RANGES[selected_range])
    st.session_state[KEY_FROM] = start_date
    st.session_state[KEY_TO] = end_date


def _uncheck_range_on_change(min_date, max_date):
    """Deselects the quick-select option if custom dates no longer match it."""
    selected_range = st.session_state.get(KEY_RANGE)
    if selected_range is None:
        return
    expected = compute_predefined_date_range(min_date, max_date, PREDEFINED_RANGES[selected_range])
    if (st.session_state.get(KEY_FROM), st.session_state.get(KEY_TO)) != expected:
        st.session_state[KEY_RANGE] = None


def render_frequent_clients_churn_view():
    """Renders the Clientes Frecuentes y Churn Estacional view layout."""
    render_header(
        "Clientes Frecuentes y Churn Estacional",
        "Identificación de cuentas clave por volumen de muestras y alertas de recencia estacional."
    )

    df = load_agronomic_data()
    if df.empty:
        st.warning("No se encontraron muestras para el período seleccionado.")
        return

    # --- Dynamic Filters ---
    min_date = df["fecha_ing_muestra"].min().date()
    max_date = df["fecha_ing_muestra"].max().date()
    available_species = ["Todas"] + sorted(df["especies"].dropna().unique().tolist())

    st.session_state.setdefault(KEY_RANGE, "Todo el período")
    st.session_state.setdefault(KEY_FROM, min_date)
    st.session_state.setdefault(KEY_TO, max_date)

    st.segmented_control(
        "Período",
        options=list(PREDEFINED_RANGES),
        key=KEY_RANGE,
        on_change=_apply_predefined_range,
        args=(min_date, max_date),
        help=f"Los rangos se calculan hasta el último ingreso registrado ({max_date:%d/%m/%Y}).",
    )

    col_from, col_to, col_species, col_convenio = st.columns([1, 1, 1, 1])
    with col_from:
        start_date_input = st.date_input(
            "Desde",
            key=KEY_FROM,
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY",
            on_change=_uncheck_range_on_change,
            args=(min_date, max_date),
        )
    with col_to:
        end_date_input = st.date_input(
            "Hasta",
            key=KEY_TO,
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY",
            on_change=_uncheck_range_on_change,
            args=(min_date, max_date),
        )
    with col_species:
        selected_species = st.selectbox("Especie de cultivo", available_species)
    with col_convenio:
        exclude_agreements = st.checkbox("Excluir convenios (ID > 50.000)", value=False)

    if start_date_input > end_date_input:
        st.error("La fecha Desde no puede ser posterior a la fecha Hasta.")
        return

    species_filter = None if selected_species == "Todas" else selected_species

    volume_df = compute_volume_by_client(
        df,
        start_date=start_date_input,
        end_date=end_date_input,
        crop_species=species_filter,
        exclude_agreements=exclude_agreements,
    )

    if volume_df.empty:
        st.info("No se encontraron muestras para el período y/o especie seleccionados.")
        return

    # --- Summary KPIs ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Clientes con envíos", f"{volume_df.shape[0]:,}".replace(",", "."))
    col2.metric("Total de muestras", f"{volume_df['total_muestras'].sum():,}".replace(",", "."))
    leader_name = (
        f"{volume_df.iloc[0]['razon_social']} (Id: {volume_df.iloc[0]['id_cliente']})"
        if "razon_social" in volume_df.columns
        else str(volume_df.iloc[0]["id_cliente"])
    )
    col3.metric("Cliente líder", leader_name)

    st.markdown("---")

    # --- Top 10 Plotly Chart ---
    st.markdown("#### Top 10 Clientes por Volumen de Muestras")
    top_10_df = volume_df.head(10).sort_values("total_muestras", ascending=True).copy()
    
    def _format_client_label(row):
        rz = str(row.get("razon_social", "")).strip()
        cid = row["id_cliente"]
        if rz and rz.upper() not in ["NN", "NAN", "NONE"]:
            return f"{rz} (ID: {cid})"
        return f"Cliente {cid}"

    top_10_df["cliente_label"] = top_10_df.apply(_format_client_label, axis=1)
    
    fig = px.bar(
        top_10_df,
        x="total_muestras",
        y="cliente_label",
        orientation="h",
        text="total_muestras",
        labels={"total_muestras": "Cantidad de Muestras", "cliente_label": "Cliente"},
        color_discrete_sequence=["#111827"],
    )
    fig.update_layout(
        font=dict(family="Poppins"),
        showlegend=False,
        height=380,
        margin=dict(l=110, r=40, t=30, b=20),
        xaxis_title="Volumen de Muestras",
        yaxis_title=None,
        coloraxis_showscale=False,
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

    # --- Detailed Client Table ---
    st.markdown("#### Tabla Completa de Clientes Ordenada por Volumen")
    
    column_config = {
        "id_cliente": st.column_config.NumberColumn(
            "ID Cliente",
            format="%d",
            help="Identificador único de la cuenta",
        ),
        "razon_social": st.column_config.TextColumn(
            "Razón Social",
            help="Nombre del cliente o entidad",
        ),
        "total_muestras": st.column_config.NumberColumn(
            "Total Muestras",
            format="%d",
            help="Volumen total de muestras recibidas",
        ),
        "porcentaje_total": st.column_config.NumberColumn(
            "% del Total",
            format="%.2f %%",
            help="Porcentaje de participación sobre el total de muestras",
        ),
    }
    
    st.dataframe(
        volume_df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
    )

    st.markdown("---")

    # --- Seasonal Churn Alert ---
    st.markdown("#### Alerta de Churn Estacional")
    st.caption(
        "Identificación de clientes cuyo volumen de envío en el mes seleccionado es 0% respecto a su promedio "
        "histórico para la misma época del año (mismo mes calendario)."
    )

    col_month, _ = st.columns([2, 2])
    with col_month:
        default_month = max_date.month
        selected_month_num = st.selectbox(
            "Mes de análisis estacional",
            options=list(MONTH_NAMES_ES.keys()),
            format_func=lambda m: MONTH_NAMES_ES[m],
            index=default_month - 1,
            help="Seleccione el mes calendario para evaluar la recencia histórica de envíos.",
        )

    alert_df = detect_seasonal_churn_alerts(
        df,
        reference_month=selected_month_num,
        exclude_agreements=exclude_agreements,
    )
    alert_clients = alert_df[alert_df["alerta_churn_estacional"]].copy()

    month_label = MONTH_NAMES_ES[selected_month_num]

    if alert_clients.empty:
        st.success(f"No hay clientes en alerta de churn estacional para el mes de {month_label}.")
    else:
        st.warning(f"{alert_clients.shape[0]} cliente(s) detectado(s) en alerta de churn estacional para {month_label}.")
        
        at_risk_vol = alert_clients["promedio_historico_mismo_mes"].sum()
        
        kpi_col1, kpi_col2 = st.columns(2)
        kpi_col1.metric(f"Clientes Inactivos en {month_label}", str(alert_clients.shape[0]))
        kpi_col2.metric("Volumen Histórico Promedio en Riesgo (Muestras)", f"{at_risk_vol:.1f}")

        alert_clients["estado"] = "[Alerta Churn 0%]"
        
        alert_column_config = {
            "id_cliente": st.column_config.NumberColumn("ID Cliente", format="%d"),
            "razon_social": st.column_config.TextColumn("Razón Social"),
            "volumen_actual": st.column_config.NumberColumn("Volumen Actual (Mes)", format="%d"),
            "promedio_historico_mismo_mes": st.column_config.NumberColumn("Promedio Histórico (Mismo Mes)", format="%.1f"),
            "estado": st.column_config.TextColumn("Estado de Alerta"),
        }
        
        show_cols = [c for c in ["id_cliente", "razon_social", "volumen_actual", "promedio_historico_mismo_mes", "estado"] if c in alert_clients.columns]
        
        st.dataframe(
            alert_clients[show_cols],
            use_container_width=True,
            hide_index=True,
            column_config=alert_column_config,
        )
