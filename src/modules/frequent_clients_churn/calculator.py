from datetime import date
import pandas as pd


def compute_predefined_date_range(
    min_date: date,
    max_date: date,
    months: int | None,
) -> tuple[date, date]:
    """Computes the (start_date, end_date) range covering the last N months ending at max_date.

    Args:
        min_date (date): The earliest available date in dataset (lower boundary).
        max_date (date): The latest available date in dataset (upper boundary).
        months (int | None): Number of months to subtract. None returns the full period.

    Returns:
        tuple[date, date]: Inclusive start and end dates.
    """
    if hasattr(min_date, "date"):
        min_date = min_date.date()
    if hasattr(max_date, "date"):
        max_date = max_date.date()

    if months is None:
        return min_date, max_date
    start_date = (pd.Timestamp(max_date) - pd.DateOffset(months=months)).date()
    return max(start_date, min_date), max_date


def compute_volume_by_client(
    df: pd.DataFrame,
    start_date: pd.Timestamp | date | None = None,
    end_date: pd.Timestamp | date | None = None,
    crop_species: str | None = None,
    exclude_agreements: bool = False,
) -> pd.DataFrame:
    """Calculates sample volume per client, sorted in descending order.

    Args:
        df (pd.DataFrame): Clean dataset with fecha_ing_muestra, id_cliente, razon_social, id_muestra, especies.
        start_date (pd.Timestamp | date | None): Minimum inclusion date (inclusive).
        end_date (pd.Timestamp | date | None): Maximum inclusion date (inclusive).
        crop_species (str | None): Filter by specific crop species if provided.
        exclude_agreements (bool): If True, excludes corporate agreement accounts (id_cliente > 50000).

    Returns:
        pd.DataFrame: Columns [id_cliente, razon_social, total_muestras, porcentaje_total] sorted by total_muestras descending.
    """
    data = df.copy()

    if exclude_agreements:
        data = data[data["id_cliente"] <= 50000]
    if start_date is not None:
        data = data[data["fecha_ing_muestra"] >= pd.Timestamp(start_date)]
    if end_date is not None:
        data = data[data["fecha_ing_muestra"] <= pd.Timestamp(end_date)]
    if crop_species:
        data = data[data["especies"] == crop_species]

    group_cols = ["id_cliente", "razon_social"] if "razon_social" in data.columns else ["id_cliente"]

    result = (
        data.groupby(group_cols)["id_muestra"]
        .nunique()
        .reset_index(name="total_muestras")
        .sort_values("total_muestras", ascending=False)
        .reset_index(drop=True)
    )

    total_muestras = result["total_muestras"].sum()
    result["porcentaje_total"] = (
        (result["total_muestras"] / total_muestras * 100).round(2)
        if total_muestras > 0
        else 0.0
    )
    return result


def detect_seasonal_churn_alerts(
    df: pd.DataFrame,
    reference_date: pd.Timestamp | None = None,
    reference_month: int | None = None,
    exclude_agreements: bool = False,
) -> pd.DataFrame:
    """Detects clients triggering seasonal churn alerts.

    Compares sample volume sent by each client in the reference month against the historical
    average for that same calendar month in prior years. If current volume is 0% of historical average,
    the client is flagged with a seasonal churn alert.

    Args:
        df (pd.DataFrame): Clean dataset with fecha_ing_muestra, id_cliente, razon_social, id_muestra.
        reference_date (pd.Timestamp | None): Reference date defining "today". None uses max date.
        reference_month (int | None): Month number (1-12) to analyze. If provided, overrides reference_date's month.
        exclude_agreements (bool): If True, excludes corporate agreement accounts (id_cliente > 50000).

    Returns:
        pd.DataFrame: Columns [id_cliente, razon_social, volumen_actual, promedio_historico_mismo_mes, alerta_churn_estacional].
    """
    data = df.copy()

    if exclude_agreements:
        data = data[data["id_cliente"] <= 50000]

    if reference_date is None:
        reference_date = data["fecha_ing_muestra"].max()

    current_month = reference_month if reference_month is not None else reference_date.month
    current_year = reference_date.year

    month_data = data[data["fecha_ing_muestra"].dt.month == current_month]
    group_cols = ["id_cliente", "razon_social"] if "razon_social" in month_data.columns else ["id_cliente"]

    current_volume = (
        month_data[month_data["fecha_ing_muestra"].dt.year == current_year]
        .groupby(group_cols)["id_muestra"]
        .nunique()
        .rename("volumen_actual")
    )

    historical_data = month_data[month_data["fecha_ing_muestra"].dt.year < current_year].copy()
    historical_data["year"] = historical_data["fecha_ing_muestra"].dt.year
    historical_average = (
        historical_data.groupby(group_cols + ["year"])["id_muestra"]
        .nunique()
        .groupby(group_cols)
        .mean()
        .rename("promedio_historico_mismo_mes")
    )

    summary = pd.concat([current_volume, historical_average], axis=1)
    summary = summary[summary["promedio_historico_mismo_mes"].notna()].fillna(0)
    summary["promedio_historico_mismo_mes"] = summary["promedio_historico_mismo_mes"].round(1)
    summary["alerta_churn_estacional"] = (
        (summary["volumen_actual"] == 0) & (summary["promedio_historico_mismo_mes"] > 0)
    )

    return summary.reset_index().sort_values(
        ["alerta_churn_estacional", "promedio_historico_mismo_mes"], ascending=[False, False]
    ).reset_index(drop=True)
