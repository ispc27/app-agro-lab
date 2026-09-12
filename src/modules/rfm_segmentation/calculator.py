import os

import pandas as pd

URL_IPC_INDEC = (
    "https://apis.datos.gob.ar/series/api/series/?limit=5000"
    "&ids=148.3_INIVELNAL_DICI_M_26&format=csv"
)
UMBRAL_ID_CONVENIO = 50_000


def cargar_ipc(ruta_backup_local: str | None = None) -> pd.DataFrame | None:
    """Carga el IPC Nacional (INDEC) para ajustar importes por inflación.

    Intenta descargarlo en vivo desde la API oficial de Argentina.gob.ar; si no hay
    conexión, recurre a una copia local de respaldo (data/raw/ipc_indec_mensual.csv).
    Función pura de I/O (sin Streamlit) — el cacheo se aplica en la capa de vista.

    Returns:
        DataFrame [anio_mes, ipc], o None si no se pudo obtener de ninguna fuente
        (en ese caso, el resto del pipeline debe degradar sin usar importe_real).
    """
    try:
        ipc = pd.read_csv(
            URL_IPC_INDEC,
            storage_options={"User-Agent": "Mozilla/5.0"},
            parse_dates=["indice_tiempo"],
        )
        ipc = ipc.rename(columns={"ipc_nivel_general_nacional": "ipc"})
    except Exception:
        if not ruta_backup_local or not os.path.exists(ruta_backup_local):
            return None
        try:
            ipc = pd.read_csv(ruta_backup_local, parse_dates=["indice_tiempo"])
            ipc = ipc.rename(columns={"ipc_nivel_general_nacional": "ipc"})
        except Exception:
            return None

    ipc["anio_mes"] = ipc["indice_tiempo"].dt.to_period("M")
    return ipc[["anio_mes", "ipc"]]


def calcular_importe_real(df: pd.DataFrame, ipc: pd.DataFrame | None) -> pd.DataFrame:
    """Agrega la columna importe_real, ajustando importe_solicitud por inflación (IPC).

    Si el IPC no está disponible (sin conexión y sin respaldo local), degrada
    correctamente: importe_real queda igual a importe_solicitud, sin cortar la app.

    Args:
        df: DataFrame limpio con columnas fecha_ing_muestra, importe_solicitud.
        ipc: DataFrame [anio_mes, ipc] de cargar_ipc(), o None.

    Returns:
        Copia de df con la columna importe_real agregada.
    """
    data = df.copy()

    if ipc is None or ipc.empty:
        data["importe_real"] = data["importe_solicitud"]
        return data

    data["anio_mes"] = data["fecha_ing_muestra"].dt.to_period("M")
    data = data.merge(ipc, on="anio_mes", how="left")

    ipc_base = ipc.loc[ipc["anio_mes"] == ipc["anio_mes"].max(), "ipc"].values[0]
    data["importe_real"] = data["importe_solicitud"] * (ipc_base / data["ipc"])
    # Si algún mes no matcheó con el IPC (ej. mes futuro), no perdemos el importe: usamos el nominal.
    data["importe_real"] = data["importe_real"].fillna(data["importe_solicitud"])

    return data.drop(columns=["anio_mes", "ipc"])


def calcular_rfm(
    df: pd.DataFrame,
    fecha_referencia: pd.Timestamp | None = None,
    excluir_convenio: bool = True,
) -> pd.DataFrame:
    """Calcula el scoring RFM (Recencia, Frecuencia, Valor Monetario) por cliente.

    Usa importe_real (ajustado por inflación) para el Valor Monetario si está
    disponible en el DataFrame; si no, cae a importe_solicitud. Los quintiles se
    calculan con rank(method="first") antes de qcut para evitar fallas cuando hay
    muchos clientes con el mismo valor (empates), garantizando siempre 5 grupos.

    Args:
        df: DataFrame limpio con columnas fecha_ing_muestra, id_cliente, id_muestra,
            y (idealmente) importe_real.
        fecha_referencia: fecha que define "hoy" para calcular la recencia. None =
            fecha máxima del dataset.
        excluir_convenio: si True, excluye clientes con id_cliente > 50.000 (códigos
            de convenio/campaña detectados en el EDA, no clientes individuales reales).

    Returns:
        DataFrame [id_cliente, recencia, frecuencia, valor_monetario, R, F, M,
        rfm_score, en_riesgo], uno por cliente.
    """
    data = df.copy()
    columna_valor = "importe_real" if "importe_real" in data.columns else "importe_solicitud"

    if excluir_convenio:
        data = data[data["id_cliente"] <= UMBRAL_ID_CONVENIO]

    if fecha_referencia is None:
        fecha_referencia = data["fecha_ing_muestra"].max()

    rfm = data.groupby("id_cliente").agg(
        recencia=("fecha_ing_muestra", lambda x: (fecha_referencia - x.max()).days),
        frecuencia=("id_muestra", "nunique"),
        valor_monetario=(columna_valor, "sum"),
    )

    # Quintiles vía rank(method="first") + qcut: evita errores por valores empatados.
    rfm["R"] = pd.qcut(rfm["recencia"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["F"] = pd.qcut(rfm["frecuencia"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["M"] = pd.qcut(rfm["valor_monetario"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)

    rfm["rfm_score"] = rfm["R"].astype(str) + rfm["F"].astype(str) + rfm["M"].astype(str)
    rfm["en_riesgo"] = (rfm["R"] <= 2) & ((rfm["F"] >= 4) | (rfm["M"] >= 4))

    return rfm.reset_index().sort_values("valor_monetario", ascending=False).reset_index(drop=True)
