from datetime import date

import pandas as pd

from src.modules.common import filtrar_por_periodo

UMBRAL_ID_CONVENIO = 50_000
# qcut necesita al menos un cliente por quintil.
MIN_CLIENTES_RFM = 5


def calcular_rfm(
    df: pd.DataFrame,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    excluir_convenio: bool = True,
) -> pd.DataFrame:
    """Calcula el scoring RFM (Recencia, Frecuencia, Valor Monetario) por cliente.

    Solo considera las muestras del período [fecha_inicio, fecha_fin]: un cliente sin
    envíos en ese período no se segmenta ni puede quedar "En Riesgo". La recencia se
    mide en días hasta fecha_fin. Los quintiles se calculan con rank(method="first")
    antes de qcut para evitar fallas cuando hay muchos clientes con el mismo valor
    (empates), garantizando siempre 5 grupos.

    Args:
        df: DataFrame limpio con columnas fecha_ing_muestra, id_cliente, id_muestra,
            importe_solicitud.
        fecha_inicio: inicio del período analizado. None = sin límite inferior.
        fecha_fin: fin del período y fecha de referencia para la recencia. None =
            fecha máxima del dataset.
        excluir_convenio: si True, excluye clientes con id_cliente > 50.000 (códigos
            de convenio/campaña detectados en el EDA, no clientes individuales reales).

    Returns:
        DataFrame [id_cliente, recencia, frecuencia, valor_monetario, R, F, M,
        rfm_score, en_riesgo], uno por cliente. Vacío si hay menos de 5 clientes.
    """
    data = filtrar_por_periodo(df, fecha_inicio, fecha_fin)

    if excluir_convenio:
        data = data[data["id_cliente"] <= UMBRAL_ID_CONVENIO]

    fecha_referencia = data["fecha_ing_muestra"].max() if fecha_fin is None else pd.Timestamp(fecha_fin)

    rfm = data.groupby("id_cliente").agg(
        recencia=("fecha_ing_muestra", lambda x: (fecha_referencia - x.max()).days),
        frecuencia=("id_muestra", "nunique"),
        valor_monetario=("importe_solicitud", "sum"),
    )

    if len(rfm) < MIN_CLIENTES_RFM:
        return rfm.iloc[0:0].reset_index()

    # Quintiles vía rank(method="first") + qcut: evita errores por valores empatados.
    rfm["R"] = pd.qcut(rfm["recencia"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["F"] = pd.qcut(rfm["frecuencia"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["M"] = pd.qcut(rfm["valor_monetario"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)

    rfm["rfm_score"] = rfm["R"].astype(str) + rfm["F"].astype(str) + rfm["M"].astype(str)
    rfm["en_riesgo"] = (rfm["R"] <= 2) & ((rfm["F"] >= 4) | (rfm["M"] >= 4))

    return rfm.reset_index().sort_values("valor_monetario", ascending=False).reset_index(drop=True)
