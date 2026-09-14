import os
import pandas as pd

INFLATION_API_URL = (
    "https://apis.datos.gob.ar/series/api/series/?limit=5000"
    "&ids=148.3_INIVELNAL_DICI_M_26&format=csv"
)
AGREEMENT_ID_THRESHOLD = 50_000


def fetch_ipc_inflation_index(local_backup_path: str | None = None) -> pd.DataFrame | None:
    """Fetches National IPC index (INDEC) for inflation adjustment.

    Attempts to fetch live data from official Argentina.gob.ar API.
    If unavailable, falls back gracefully to local backup file (data/raw/ipc_indec_mensual.csv).

    Args:
        local_backup_path (str | None): Optional path to local backup CSV file.

    Returns:
        pd.DataFrame | None: DataFrame [anio_mes, ipc], or None if unavailable from all sources.
    """
    try:
        ipc = pd.read_csv(
            INFLATION_API_URL,
            storage_options={"User-Agent": "Mozilla/5.0"},
            parse_dates=["indice_tiempo"],
        )
        ipc = ipc.rename(columns={"ipc_nivel_general_nacional": "ipc"})
    except Exception:
        if not local_backup_path or not os.path.exists(local_backup_path):
            return None
        try:
            ipc = pd.read_csv(local_backup_path, parse_dates=["indice_tiempo"])
            ipc = ipc.rename(columns={"ipc_nivel_general_nacional": "ipc"})
        except Exception:
            return None

    ipc["anio_mes"] = ipc["indice_tiempo"].dt.to_period("M")
    return ipc[["anio_mes", "ipc"]]


def adjust_real_amounts(df: pd.DataFrame, ipc_df: pd.DataFrame | None) -> pd.DataFrame:
    """Adds column importe_real, adjusting importe_solicitud for inflation (IPC).

    If IPC data is unavailable, degrades gracefully by setting importe_real equal to importe_solicitud.

    Args:
        df (pd.DataFrame): Clean dataset with fecha_ing_muestra, importe_solicitud.
        ipc_df (pd.DataFrame | None): IPC index DataFrame [anio_mes, ipc], or None.

    Returns:
        pd.DataFrame: Copy of df with added importe_real column.
    """
    data = df.copy()

    if ipc_df is None or ipc_df.empty:
        data["importe_real"] = data["importe_solicitud"]
        return data

    data["anio_mes"] = data["fecha_ing_muestra"].dt.to_period("M")
    data = data.merge(ipc_df, on="anio_mes", how="left")

    base_ipc = ipc_df.loc[ipc_df["anio_mes"] == ipc_df["anio_mes"].max(), "ipc"].values[0]
    data["importe_real"] = data["importe_solicitud"] * (base_ipc / data["ipc"])
    data["importe_real"] = data["importe_real"].fillna(data["importe_solicitud"])

    return data.drop(columns=["anio_mes", "ipc"])


def compute_rfm_score(
    df: pd.DataFrame,
    reference_date: pd.Timestamp | None = None,
    exclude_agreements: bool = True,
) -> pd.DataFrame:
    """Computes RFM (Recency, Frequency, Monetary Value) scoring per client account.

    Quintiles are calculated using rank(method="first") prior to qcut to avoid binning errors on duplicate values.

    Args:
        df (pd.DataFrame): Clean dataset with fecha_ing_muestra, id_cliente, id_muestra, and (optionally) importe_real.
        reference_date (pd.Timestamp | None): Reference date for recency calculation. None uses dataset max date.
        exclude_agreements (bool): If True, excludes clients with id_cliente > 50,000 (campaign/agreement codes).

    Returns:
        pd.DataFrame: Columns [id_cliente, recencia, frecuencia, valor_monetario, R, F, M, rfm_score, en_riesgo].
    """
    data = df.copy()
    value_column = "importe_real" if "importe_real" in data.columns else "importe_solicitud"

    if exclude_agreements:
        data = data[data["id_cliente"] <= AGREEMENT_ID_THRESHOLD]

    if reference_date is None:
        reference_date = data["fecha_ing_muestra"].max()

    group_cols = ["id_cliente", "razon_social"] if "razon_social" in data.columns else ["id_cliente"]

    rfm = data.groupby(group_cols).agg(
        recencia=("fecha_ing_muestra", lambda x: (reference_date - x.max()).days),
        frecuencia=("id_muestra", "nunique"),
        valor_monetario=(value_column, "sum"),
    ).reset_index()

    rfm["R"] = pd.qcut(rfm["recencia"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["F"] = pd.qcut(rfm["frecuencia"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["M"] = pd.qcut(rfm["valor_monetario"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)

    rfm["rfm_score"] = rfm["R"].astype(str) + rfm["F"].astype(str) + rfm["M"].astype(str)
    rfm["en_riesgo"] = (rfm["R"] <= 2) & ((rfm["F"] >= 4) | (rfm["M"] >= 4))

    return rfm.sort_values("valor_monetario", ascending=False).reset_index(drop=True)
