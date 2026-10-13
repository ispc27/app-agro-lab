import numpy as np
import pandas as pd

AGREEMENT_ID_THRESHOLD = 50_000


def assign_rfm_segment(row: pd.Series) -> str:
    """Categorizes a client into strategic commercial business segments based on RFM score.

    Official Categories:
        - En Riesgo: Cuentas históricas de alto volumen/facturación cuya recencia cayó (R <= 2 con F >= 4 o M >= 4).
        - Campeones: Activo más valioso; compran recientemente, con alta frecuencia y mayor gasto (R >= 4, F >= 4, M >= 4).
        - Fieles / Alto Valor: Comportamiento sólido y sostenido; candidatos para upselling (R >= 3 y (F >= 3 o M >= 3)).
        - Potenciales: Clientes recientes pero con bajo volumen acumulado (R >= 3 y F <= 2).
        - Perdidos: Menor score en los tres indicadores; inactivos de bajo retorno (R <= 2 y F <= 3 y M <= 3).
    """
    if row["en_riesgo"]:
        return "En Riesgo"
    if row["R"] >= 4 and row["F"] >= 4 and row["M"] >= 4:
        return "Campeones"
    if row["R"] >= 3 and (row["F"] >= 3 or row["M"] >= 3):
        return "Fieles / Alto Valor"
    if row["R"] >= 3 and row["F"] <= 2:
        return "Potenciales"
    return "Perdidos"


def compute_rfm_score(
    df: pd.DataFrame,
    start_date: pd.Timestamp | str | None = None,
    end_date: pd.Timestamp | str | None = None,
    reference_date: pd.Timestamp | None = None,
    exclude_agreements: bool = False,
) -> pd.DataFrame:
    """Computes RFM (Recency, Frequency, Monetary Value) scoring per client account.

    Quintiles are calculated using rank(method="first") prior to qcut to avoid binning errors on duplicate values.
    Supports filtering by specific agricultural cycles (e.g., Ciclo 25/26).

    Variables (RD-02):
        - Recencia (R): Días transcurridos desde la última muestra ingresada.
        - Frecuencia (F): Total de muestras analizadas (órdenes).
        - Valor Monetario (M): Facturación acumulada nominal (importe_solicitud).

    Args:
        df (pd.DataFrame): Clean dataset with fecha_ing_muestra, id_cliente, id_muestra, importe_solicitud.
        start_date (pd.Timestamp | str | None): Optional period lower boundary.
        end_date (pd.Timestamp | str | None): Optional period upper boundary.
        reference_date (pd.Timestamp | None): Reference date for recency calculation. None uses dataset max date.
        exclude_agreements (bool): If True, excludes clients with id_cliente > 50,000 (default False; all clients evaluated).

    Returns:
        pd.DataFrame: Columns [id_cliente, razon_social, recencia, frecuencia, valor_monetario, R, F, M, rfm_score, en_riesgo, segmento, nivel_alerta, accion_recomendada].
    """
    data = df.copy()

    if start_date is not None:
        data = data[data["fecha_ing_muestra"] >= pd.Timestamp(start_date)]
    if end_date is not None:
        data = data[data["fecha_ing_muestra"] <= pd.Timestamp(end_date)]

    if exclude_agreements:
        data = data[data["id_cliente"] <= AGREEMENT_ID_THRESHOLD]

    if data.empty:
        return pd.DataFrame(columns=[
            "id_cliente", "razon_social", "recencia", "frecuencia",
            "valor_monetario", "R", "F", "M", "rfm_score", "en_riesgo",
            "segmento", "nivel_alerta", "accion_recomendada"
        ])

    if reference_date is None:
        reference_date = data["fecha_ing_muestra"].max()

    group_cols = ["id_cliente", "razon_social"] if "razon_social" in data.columns else ["id_cliente"]

    rfm = data.groupby(group_cols).agg(
        recencia=("fecha_ing_muestra", lambda x: (reference_date - x.max()).days),
        frecuencia=("id_muestra", "nunique"),
        valor_monetario=("importe_solicitud", "sum"),
    ).reset_index()

    num_clients = len(rfm)
    if num_clients < 5:
        # Graceful ranking assignment when client count is less than 5
        ranks_r = rfm["recencia"].rank(method="first", ascending=False)
        rfm["R"] = np.ceil(ranks_r / num_clients * 5).astype(int).clip(1, 5)

        ranks_f = rfm["frecuencia"].rank(method="first", ascending=True)
        rfm["F"] = np.ceil(ranks_f / num_clients * 5).astype(int).clip(1, 5)

        ranks_m = rfm["valor_monetario"].rank(method="first", ascending=True)
        rfm["M"] = np.ceil(ranks_m / num_clients * 5).astype(int).clip(1, 5)
    else:
        rfm["R"] = pd.qcut(rfm["recencia"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
        rfm["F"] = pd.qcut(rfm["frecuencia"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
        rfm["M"] = pd.qcut(rfm["valor_monetario"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)

    rfm["rfm_score"] = rfm["R"].astype(str) + rfm["F"].astype(str) + rfm["M"].astype(str)
    rfm["en_riesgo"] = (rfm["R"] <= 2) & ((rfm["F"] >= 4) | (rfm["M"] >= 4))

    # Strategic commercial segment and alert levels
    rfm["segmento"] = rfm.apply(assign_rfm_segment, axis=1)

    def determine_alert_level(row: pd.Series) -> str:
        if not row["en_riesgo"]:
            return "Activo Saludable"
        if row["R"] == 1 and row["M"] >= 4:
            return "Crítico (Alta Exposición)"
        return "Alto Riesgo"

    def determine_recommended_action(row: pd.Series) -> str:
        if not row["en_riesgo"]:
            return "Fidelización regular"
        if row["R"] == 1 and row["M"] >= 4:
            return "Contacto telefónico prioritario / Oferta especial"
        return "Relevamiento comercial pre-campaña"

    rfm["nivel_alerta"] = rfm.apply(determine_alert_level, axis=1)
    rfm["accion_recomendada"] = rfm.apply(determine_recommended_action, axis=1)

    return rfm.sort_values("valor_monetario", ascending=False).reset_index(drop=True)

