import plotly.express as px
import streamlit as st
from src.components.theme import render_header
from src.config.settings import load_agronomic_data, load_ipc_data
from src.modules.rfm_segmentation import adjust_real_amounts, compute_rfm_score


def render_rfm_segmentation_view():
    """Renders the Segmentación RFM y Alerta de Fuga view layout."""
    render_header(
        "Segmentación RFM y Alerta de Fuga",
        "Pipeline de scoring RFM de cuentas y listado prioritario de clientes en riesgo para gestión comercial."
    )

    df = load_agronomic_data()
    if df.empty:
        st.warning("No se encontraron muestras para el período seleccionado.")
        return

    # Attempt to load IPC data if available, without forcing network calls if offline
    ipc_df = load_ipc_data()
    df = adjust_real_amounts(df, ipc_df)

    # Compute RFM scoring excluding corporate agreements (id_cliente > 50,000)
    rfm_df = compute_rfm_score(df, exclude_agreements=True)

    # --- Summary KPIs ---
    at_risk_count = int(rfm_df["en_riesgo"].sum())
    at_risk_value = rfm_df.loc[rfm_df["en_riesgo"], "valor_monetario"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Clientes Segmentados", f"{rfm_df.shape[0]:,}".replace(",", "."))
    col2.metric("Clientes En Riesgo de Fuga", f"{at_risk_count:,}".replace(",", "."))
    col3.metric("Valor Monetario en Riesgo", f"${at_risk_value:,.0f}".replace(",", "."))

    st.markdown("---")

    # --- RFM Score Distribution ---
    st.markdown("#### Distribución de Scores RFM (Recencia - Frecuencia - Monetario)")
    st.caption("Puntajes de 3 dígitos (del 111 al 555) calculados mediante quintiles. R5=Más reciente, F5=Más muestras, M5=Mayor valor.")
    
    score_distribution = rfm_df["rfm_score"].value_counts().reset_index()
    score_distribution.columns = ["rfm_score", "cantidad_clientes"]
    
    fig = px.bar(
        score_distribution.sort_values("rfm_score"),
        x="rfm_score",
        y="cantidad_clientes",
        text="cantidad_clientes",
        color_discrete_sequence=["#111827"],
        labels={"rfm_score": "Score RFM (R-F-M)", "cantidad_clientes": "Cantidad de Clientes"},
    )
    fig.update_xaxes(type="category")
    fig.update_traces(textposition="outside")
    fig.update_layout(
        font=dict(family="Poppins"),
        xaxis_title="Score RFM (3 dígitos)",
        yaxis_title="Cantidad de Clientes",
        margin=dict(t=30, b=20),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # --- Churn Risk Alert Table (Priority Commercial List) ---
    st.markdown("#### Alerta de Fuga: Listado Prioritario de Clientes En Riesgo")
    st.caption(
        "Cuentas con Baja Recencia (quintil R 1 o 2) pero Alta Frecuencia o Alto Valor histórico (quintiles F o M 4 o 5). "
        "Eran clientes estratégicos que han dejado de operar recientemente."
    )

    at_risk_df = rfm_df[rfm_df["en_riesgo"]].copy()
    if at_risk_df.empty:
        st.success("No se registran clientes en alerta de fuga con los parámetros actuales.")
    else:
        st.warning(f"{at_risk_df.shape[0]} cliente(s) prioritario(s) detectado(s) en alerta de fuga.")
        
        at_risk_df["estado"] = "[En Riesgo]"
        at_risk_df["valor_monetario"] = at_risk_df["valor_monetario"].round(0)
        
        column_config_risk = {
            "id_cliente": st.column_config.NumberColumn("ID Cliente", format="%d"),
            "razon_social": st.column_config.TextColumn("Razón Social"),
            "recencia": st.column_config.NumberColumn("Días Inactivo", format="%d días"),
            "frecuencia": st.column_config.NumberColumn("Muestras Históricas", format="%d"),
            "valor_monetario": st.column_config.NumberColumn("Valor Histórico ($)", format="$ %d"),
            "rfm_score": st.column_config.TextColumn("Score RFM"),
            "estado": st.column_config.TextColumn("Estado de Alerta"),
        }
        
        show_cols = [c for c in ["id_cliente", "razon_social", "recencia", "frecuencia", "valor_monetario", "rfm_score", "estado"] if c in at_risk_df.columns]
        
        st.dataframe(
            at_risk_df[show_cols],
            use_container_width=True,
            hide_index=True,
            column_config=column_config_risk,
        )

    st.markdown("---")

    # --- Full RFM Table ---
    with st.expander("Ver Segmentación RFM Completa (Todos los Clientes)"):
        full_rfm_display = rfm_df.copy()
        full_rfm_display["valor_monetario"] = full_rfm_display["valor_monetario"].round(0)
        full_rfm_display["estado"] = full_rfm_display["en_riesgo"].apply(lambda x: "[En Riesgo]" if x else "[Saludable]")
        
        full_column_config = {
            "id_cliente": st.column_config.NumberColumn("ID Cliente", format="%d"),
            "razon_social": st.column_config.TextColumn("Razón Social"),
            "recencia": st.column_config.NumberColumn("Días Inactivo", format="%d días"),
            "frecuencia": st.column_config.NumberColumn("Total Muestras", format="%d"),
            "valor_monetario": st.column_config.NumberColumn("Valor Total ($)", format="$ %d"),
            "R": st.column_config.NumberColumn("Quintil R", format="%d"),
            "F": st.column_config.NumberColumn("Quintil F", format="%d"),
            "M": st.column_config.NumberColumn("Quintil M", format="%d"),
            "rfm_score": st.column_config.TextColumn("Score RFM"),
            "estado": st.column_config.TextColumn("Estado Segmento"),
        }
        
        full_cols = [c for c in ["id_cliente", "razon_social", "recencia", "frecuencia", "valor_monetario", "R", "F", "M", "rfm_score", "estado"] if c in full_rfm_display.columns]
        
        st.dataframe(
            full_rfm_display[full_cols],
            use_container_width=True,
            hide_index=True,
            column_config=full_column_config,
        )
