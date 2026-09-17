import plotly.express as px
import streamlit as st
from src.components.period_filter import render_period_filter
from src.components.theme import render_header
from src.config.settings import load_agronomic_data
from src.modules.rfm_segmentation import calcular_rfm, MIN_CLIENTES_RFM


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

    filtros = render_period_filter(df, key_prefix="rfm", rango_inicial="Último año")
    if filtros is None:
        return
    fecha_inicio, fecha_fin, _ = filtros

    rfm = calcular_rfm(df, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, excluir_convenio=True)
    if rfm.empty:
        st.info(
            f"Se necesitan al menos {MIN_CLIENTES_RFM} clientes con envíos en el período "
            "seleccionado para calcular la segmentación RFM."
        )
        return

    st.caption(
        f"Solo se segmentan clientes con envíos entre el {fecha_inicio:%d/%m/%Y} y el "
        f"{fecha_fin:%d/%m/%Y}. La recencia se mide en días hasta la fecha Hasta."
    )

    # --- KPIs ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Clientes segmentados", f"{rfm.shape[0]:,}".replace(",", "."))
    col2.metric("Clientes En Riesgo", int(rfm["en_riesgo"].sum()))
    col3.metric(
        "Valor Monetario en riesgo",
        f"${rfm.loc[rfm['en_riesgo'], 'valor_monetario'].sum():,.0f}".replace(",", "."),
    )

    # --- Distribución de scores RFM ---
    st.markdown("#### Distribución de Scores RFM")
    distribucion_scores = rfm["rfm_score"].value_counts().reset_index()
    distribucion_scores.columns = ["rfm_score", "cantidad_clientes"]
    fig = px.bar(
        distribucion_scores.sort_values("rfm_score"),
        x="rfm_score",
        y="cantidad_clientes",
        color_discrete_sequence=["#111827"],
    )
    fig.update_xaxes(type="category")
    fig.update_layout(xaxis_title="Score RFM (R-F-M)", yaxis_title="Clientes", margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

    # --- Alerta: clientes En Riesgo (listado prioritario) ---
    st.markdown("#### Alerta de Fuga: clientes En Riesgo")
    st.caption(
        "Baja Recencia (quintil 1-2) combinada con Alta Frecuencia o Alto Valor "
        "(quintil 4-5): eran buenos clientes en el período y dejaron de operar recientemente."
    )

    en_riesgo = rfm[rfm["en_riesgo"]].copy()
    if en_riesgo.empty:
        st.success("No hay clientes en alerta de fuga para el período seleccionado.")
    else:
        st.warning(f"{en_riesgo.shape[0]} cliente(s) en alerta de fuga — listado prioritario para gestión comercial.")
        en_riesgo["valor_monetario"] = en_riesgo["valor_monetario"].round(0)
        en_riesgo_mostrar = en_riesgo[
            ["id_cliente", "recencia", "frecuencia", "valor_monetario", "rfm_score"]
        ].rename(columns={
            "id_cliente": "Cliente (Id)",
            "recencia": "Días sin operar",
            "frecuencia": "Muestras en el período",
            "valor_monetario": "Valor en el período ($)",
            "rfm_score": "Score RFM",
        })
        st.dataframe(en_riesgo_mostrar, use_container_width=True, hide_index=True)

    # --- Tabla completa ---
    with st.expander("Ver segmentación RFM completa (todos los clientes)"):
        rfm_mostrar = rfm[
            ["id_cliente", "recencia", "frecuencia", "valor_monetario", "R", "F", "M", "rfm_score", "en_riesgo"]
        ].copy()
        rfm_mostrar["valor_monetario"] = rfm_mostrar["valor_monetario"].round(0)
        st.dataframe(rfm_mostrar, use_container_width=True, hide_index=True)
