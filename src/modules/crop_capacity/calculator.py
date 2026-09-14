import numpy as np
import pandas as pd

CRITICAL_CROPS = ["Soja", "Trigo"]


def compute_crop_distribution(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Calculates sample volume distribution per crop species, grouping remaining into 'Otras'.

    Args:
        df (pd.DataFrame): Clean dataset with columnas especies, id_muestra.
        top_n (int): Number of top crop species to display individually.

    Returns:
        pd.DataFrame: Columns [especies, total_muestras, porcentaje], featuring top N crops
        and an 'Otras' row grouping remaining crops (if applicable).
    """
    counts = df.groupby("especies")["id_muestra"].nunique().sort_values(ascending=False)

    top_crops = counts.head(top_n)
    remaining = counts.iloc[top_n:].sum()

    if remaining > 0:
        top_crops = pd.concat([top_crops, pd.Series({"Otras": remaining})])

    result = top_crops.reset_index()
    result.columns = ["especies", "total_muestras"]
    result["porcentaje"] = (result["total_muestras"] / result["total_muestras"].sum() * 100).round(1)
    return result


def compute_monthly_evolution(df: pd.DataFrame, crop_species: str) -> pd.DataFrame:
    """Calculates monthly sample volume for a given crop species without time gaps.

    Any month in the dataset's date range without samples for that species is filled with 0,
    ensuring a continuous trend curve.

    Args:
        df (pd.DataFrame): Clean dataset with fecha_ing_muestra, especies, id_muestra.
        crop_species (str): Target crop species to analyze.

    Returns:
        pd.DataFrame: Columns [fecha, total_muestras] for every month in dataset range.
    """
    full_range = pd.period_range(
        df["fecha_ing_muestra"].min().to_period("M"),
        df["fecha_ing_muestra"].max().to_period("M"),
        freq="M",
    )

    if isinstance(crop_species, (list, tuple, set)):
        species_data = df[df["especies"].isin(crop_species)].copy()
    else:
        species_data = df[df["especies"] == crop_species].copy()
    species_data["year_month"] = species_data["fecha_ing_muestra"].dt.to_period("M")
    counts = species_data.groupby("year_month")["id_muestra"].nunique()
    counts = counts.reindex(full_range, fill_value=0)

    result = counts.reset_index()
    result.columns = ["year_month", "total_muestras"]
    result["fecha"] = result["year_month"].dt.to_timestamp()
    return result[["fecha", "total_muestras"]]


def assess_capacity_alerts(
    df: pd.DataFrame,
    crop_species: str,
    critical_capacity: float | None = None,
) -> tuple[pd.DataFrame, float]:
    """Evaluates monthly operational capacity status for a critical crop species.

    Compares monthly volume against a reference critical capacity (defaulting to the historical max
    monthly volume for that crop) and classifies each month into Normal / Advertencia (>=75%) / Saturación (>=90%).

    Args:
        df (pd.DataFrame): Clean dataset with fecha_ing_muestra, especies, id_muestra.
        crop_species (str): Target critical crop species.
        critical_capacity (float | None): Reference monthly volume (100%). Default uses max monthly volume.

    Returns:
        tuple[pd.DataFrame, float]: Tuple containing (DataFrame [fecha, total_muestras, porcentaje_capacidad, estado], capacity_used).
    """
    evolution = compute_monthly_evolution(df, crop_species)

    if critical_capacity is None:
        critical_capacity = float(evolution["total_muestras"].max())

    if critical_capacity <= 0:
        evolution["porcentaje_capacidad"] = 0.0
    else:
        evolution["porcentaje_capacidad"] = (evolution["total_muestras"] / critical_capacity * 100).round(1)

    conditions = [
        evolution["porcentaje_capacidad"] >= 90,
        evolution["porcentaje_capacidad"] >= 75,
    ]
    evolution["estado"] = np.select(conditions, ["Saturación", "Advertencia"], default="Normal")

    return evolution, critical_capacity
