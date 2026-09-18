from datetime import date
import numpy as np
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
    crop_species: str | list[str] | None = None,
    client_status: str = "todos",
    client_profile: str = "todos",
    exclude_agreements: bool = False,
) -> pd.DataFrame:
    """Calculates sample volume per client, sorted in descending order, with client status and profile filters.

    Args:
        df (pd.DataFrame): Clean dataset with fecha_ing_muestra, id_cliente, id_muestra, especies.
        start_date (pd.Timestamp | date | None): Minimum inclusion date (inclusive).
        end_date (pd.Timestamp | date | None): Maximum inclusion date (inclusive).
        crop_species (str | list[str] | None): Filter by specific crop species or list of species if provided.
        client_status (str): Filter by status: 'todos'/'all', 'activos'/'active', 'inactivos'/'inactive'.
        client_profile (str): Filter by profile: 'todos', 'estacional', 'mixto'.
        exclude_agreements (bool): If True, excludes accounts with id_cliente > 50000.

    Returns:
        pd.DataFrame: Columns [id_cliente, total_muestras, porcentaje_total, estado_cliente, tipo_cliente, dias_inactivo]
        (and razon_social if present in df) sorted by total_muestras descending.
    """
    data = df.copy()

    if exclude_agreements:
        data = data[data["id_cliente"] <= 50000]

    # Filter by crop species across portfolio if specified
    if crop_species:
        if isinstance(crop_species, str) and crop_species != "Todas":
            data = data[data["especies"] == crop_species]
        elif isinstance(crop_species, (list, tuple, set)):
            species_clean = [s for s in crop_species if s != "Todas"]
            if species_clean:
                data = data[data["especies"].isin(species_clean)]

    # Client portfolio
    all_clients = data[["id_cliente"]].drop_duplicates()

    # Compute behavioral profile: Estacional (monoculture or <=2 active months) vs Mixto (>=2 species or >=3 active months)
    ref_date = pd.Timestamp(end_date) if end_date is not None else data["fecha_ing_muestra"].max()
    client_profiles = data.groupby("id_cliente").agg(
        n_species=("especies", "nunique"),
        n_months=("fecha_ing_muestra", lambda s: s.dt.month.nunique()),
        last_date=("fecha_ing_muestra", "max"),
    ).reset_index()

    client_profiles["tipo_cliente"] = client_profiles.apply(
        lambda r: "Mixto" if (r["n_species"] >= 2 or r["n_months"] >= 3) else "Estacional",
        axis=1,
    )
    client_profiles["dias_inactivo"] = (pd.Timestamp(ref_date) - pd.to_datetime(client_profiles["last_date"])).dt.days
    client_profiles["dias_inactivo"] = client_profiles["dias_inactivo"].clip(lower=0).fillna(0).astype(int)

    # Filter window data for date range
    window_data = data.copy()
    if start_date is not None:
        window_data = window_data[window_data["fecha_ing_muestra"] >= pd.Timestamp(start_date)]
    if end_date is not None:
        window_data = window_data[window_data["fecha_ing_muestra"] <= pd.Timestamp(end_date)]

    # Calculate samples sent in the window
    window_vol = (
        window_data.groupby("id_cliente")["id_muestra"]
        .nunique()
        .reset_index(name="total_muestras")
    )

    result = pd.merge(all_clients, window_vol, on="id_cliente", how="left")
    result["total_muestras"] = result["total_muestras"].fillna(0).astype(int)
    result["estado_cliente"] = np.where(result["total_muestras"] > 0, "Activo", "Inactivo")

    result = pd.merge(result, client_profiles[["id_cliente", "tipo_cliente", "dias_inactivo"]], on="id_cliente", how="left")
    result["tipo_cliente"] = result["tipo_cliente"].fillna("Estacional")
    result["dias_inactivo"] = result["dias_inactivo"].fillna(0).astype(int)

    # Preserve razon_social if present in source dataset
    if "razon_social" in df.columns:
        rz_map = df.drop_duplicates(subset=["id_cliente"]).set_index("id_cliente")["razon_social"]
        result["razon_social"] = result["id_cliente"].map(rz_map).fillna("NN")

    total_muestras = result["total_muestras"].sum()
    result["porcentaje_total"] = (
        (result["total_muestras"] / total_muestras * 100).round(2)
        if total_muestras > 0
        else 0.0
    )

    # Filter by client_status
    status_lower = str(client_status).lower()
    if status_lower in ["activos", "activo", "active"]:
        result = result[result["estado_cliente"] == "Activo"]
    elif status_lower in ["inactivos", "inactivo", "inactive"]:
        result = result[result["estado_cliente"] == "Inactivo"]

    # Filter by client_profile (Estacional vs Mixto)
    profile_lower = str(client_profile).lower()
    if "estacional" in profile_lower:
        result = result[result["tipo_cliente"] == "Estacional"]
    elif "mixto" in profile_lower:
        result = result[result["tipo_cliente"] == "Mixto"]

    return result.sort_values(["total_muestras", "id_cliente"], ascending=[False, True]).reset_index(drop=True)


def detect_seasonal_churn_alerts(
    df: pd.DataFrame,
    reference_date: pd.Timestamp | None = None,
    reference_month: int | None = None,
    crop_species: str | None = None,
    exclude_agreements: bool = False,
) -> pd.DataFrame:
    """Detects clients triggering seasonal churn alerts.

    Compares sample volume sent by each client in the reference month against the historical
    average for that same calendar month in prior years. If current volume is 0% of historical average,
    the client is flagged with a seasonal churn alert. Supports filtering by crop species (Objetivo 1).

    Args:
        df (pd.DataFrame): Clean dataset with fecha_ing_muestra, id_cliente, razon_social, id_muestra, especies.
        reference_date (pd.Timestamp | None): Reference date defining "today". None uses max date.
        reference_month (int | None): Month number (1-12) to analyze. If provided, overrides reference_date's month.
        crop_species (str | None): Optional crop species to evaluate seasonal churn for that specific crop.
        exclude_agreements (bool): If True, excludes corporate agreement accounts (id_cliente > 50000).

    Returns:
        pd.DataFrame: Columns [id_cliente, razon_social, volumen_actual, promedio_historico_mismo_mes, alerta_churn_estacional].
    """
    data = df.copy()

    if exclude_agreements:
        data = data[data["id_cliente"] <= 50000]

    if crop_species and crop_species != "Todas":
        data = data[data["especies"] == crop_species]

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
