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


def compute_monthly_evolution(
    df: pd.DataFrame, crop_species: str | list[str] | None = None
) -> pd.DataFrame:
    """Calculates monthly sample volume for a given crop species or consolidated across all crops without time gaps.

    Any month in the dataset's date range without samples is filled with 0,
    ensuring a continuous trend curve.

    Args:
        df (pd.DataFrame): Clean dataset with fecha_ing_muestra, especies, id_muestra.
        crop_species (str | list[str] | None): Target crop species or None/'Todos los Cultivos' for consolidated lab volume.

    Returns:
        pd.DataFrame: Columns [fecha, total_muestras] for every month in dataset range.
    """
    if df.empty:
        return pd.DataFrame(columns=["fecha", "total_muestras"])

    full_range = pd.period_range(
        df["fecha_ing_muestra"].min().to_period("M"),
        df["fecha_ing_muestra"].max().to_period("M"),
        freq="M",
    )

    if crop_species is None or crop_species in ["Todos", "Todos los Cultivos", "Consolidado"]:
        species_data = df.copy()
    elif isinstance(crop_species, (list, tuple, set)):
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
    crop_species: str | list[str] | None = None,
    critical_capacity: float | None = None,
    warning_threshold: float = 142.0,
    bottleneck_threshold: float = 191.0,
) -> tuple[pd.DataFrame, float]:
    """Evaluates monthly operational capacity status for a crop or consolidated lab volume.

    When critical_capacity is provided, uses custom capacity percentage thresholds (>=75% Advertencia, >=90% Saturación).
    When critical_capacity is None, applies the fixed laboratory operational thresholds:
    warning_threshold = 142.0 (Alerta Operativa / Amarillo) and bottleneck_threshold = 191.0 (Cuello de Botella / Rojo).

    Args:
        df (pd.DataFrame): Clean dataset with fecha_ing_muestra, especies, id_muestra.
        crop_species (str | list[str] | None): Target crop species or None/'Todos los Cultivos' for total consolidated lab volume.
        critical_capacity (float | None): Reference monthly volume if in custom percentage mode.
        warning_threshold (float): Fixed operational warning threshold (default 142 samples/month).
        bottleneck_threshold (float): Fixed operational bottleneck threshold (default 191 samples/month).

    Returns:
        tuple[pd.DataFrame, float]: Tuple containing (DataFrame [fecha, total_muestras, porcentaje_capacidad, estado], capacity_used).
    """
    evolution = compute_monthly_evolution(df, crop_species)

    if critical_capacity is not None:
        if critical_capacity <= 0:
            evolution["porcentaje_capacidad"] = 0.0
        else:
            evolution["porcentaje_capacidad"] = (evolution["total_muestras"] / critical_capacity * 100).round(1)

        conditions = [
            evolution["porcentaje_capacidad"] >= 90,
            evolution["porcentaje_capacidad"] >= 75,
        ]
        evolution["estado"] = np.select(conditions, ["Saturación", "Advertencia"], default="Normal")
        ref_cap = critical_capacity
    else:
        conditions = [
            evolution["total_muestras"] >= bottleneck_threshold,
            evolution["total_muestras"] >= warning_threshold,
        ]
        evolution["estado"] = np.select(conditions, ["Cuello de Botella", "Alerta Operativa"], default="Normal")
        evolution["porcentaje_capacidad"] = (evolution["total_muestras"] / bottleneck_threshold * 100).round(1)
        ref_cap = bottleneck_threshold

    return evolution, ref_cap


def compute_critical_intervals(
    df: pd.DataFrame,
    crop_species: list[str] | str | None = None,
) -> pd.DataFrame:
    """Calculates critical demand intervals by crop species and analysis type.

    Identifies test demand concentration per crop to optimize staffing and consumables (Objetivo 2).

    Args:
        df (pd.DataFrame): Clean dataset with columns especies, tipo_analisis, id_muestra.
        crop_species (list[str] | str | None): Target crops (default CRITICAL_CROPS: Soja and Trigo).

    Returns:
        pd.DataFrame: Columns [especies, tipo_analisis, total_muestras, porcentaje_cultivo]
        sorted by species and total_muestras descending.
    """
    data = df.copy()
    if crop_species is None:
        crops = CRITICAL_CROPS
    elif isinstance(crop_species, str):
        crops = [crop_species]
    else:
        crops = list(crop_species)

    data = data[data["especies"].isin(crops)]
    grouped = (
        data.groupby(["especies", "tipo_analisis"])["id_muestra"]
        .nunique()
        .reset_index(name="total_muestras")
    )
    crop_totals = grouped.groupby("especies")["total_muestras"].transform("sum")
    grouped["porcentaje_cultivo"] = (
        (grouped["total_muestras"] / crop_totals * 100).round(1) if len(crop_totals) > 0 else 0.0
    )
    return grouped.sort_values(["especies", "total_muestras"], ascending=[True, False]).reset_index(drop=True)


MONTH_NAMES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}


def compute_seasonal_peak_months(
    df: pd.DataFrame, crop_species: str | list[str] | None = None
) -> dict:
    """Identifies historical seasonal peak demand months for a given crop or consolidated volume.

    Returns dict with peak window details (e.g. peak months names, average volume, % of annual volume).
    """
    evolution = compute_monthly_evolution(df, crop_species)
    if evolution.empty or evolution["total_muestras"].sum() == 0:
        return {
            "peak_months_str": "Sin datos",
            "peak_avg_monthly": 0,
            "peak_concentration_pct": 0.0,
            "top_months": [],
        }

    evolution["month_num"] = evolution["fecha"].dt.month
    monthly_avg = evolution.groupby("month_num")["total_muestras"].mean()
    top_months = monthly_avg.sort_values(ascending=False).head(3)

    top_month_indices = sorted(top_months.index.tolist())
    top_month_names = [MONTH_NAMES_ES[m] for m in top_month_indices]

    peak_str = " - ".join(top_month_names)
    total_avg_annual = monthly_avg.sum()
    peak_sum = top_months.sum()
    pct = (peak_sum / total_avg_annual * 100).round(1) if total_avg_annual > 0 else 0.0

    return {
        "peak_months_str": peak_str,
        "peak_avg_monthly": round(top_months.mean(), 1),
        "peak_concentration_pct": pct,
        "top_months": top_month_names,
    }


def compute_campaign_comparison(
    df: pd.DataFrame, crop_species: str | list[str] | None = None
) -> pd.DataFrame:
    """Computes month-by-month sample volume comparison between Ciclo 24/25 (Jul 2024 - Jun 2025)
    and Ciclo 25/26 (Jul 2025 - Jun 2026).

    Returns pd.DataFrame with columns: [order, mes_nombre, Ciclo 24/25, Ciclo 25/26].
    """
    evo = compute_monthly_evolution(df, crop_species)
    if evo.empty:
        return pd.DataFrame(columns=["order", "mes_nombre", "Ciclo 24/25", "Ciclo 25/26"])

    # Agricultural cycle month order: Jul (7) to Jun (6)
    agri_months = [7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6]
    month_names = ["Jul", "Ago", "Sep", "Oct", "Nov", "Dic", "Ene", "Feb", "Mar", "Abr", "May", "Jun"]

    result_rows = []
    for idx, (m_num, m_name) in enumerate(zip(agri_months, month_names)):
        yr_24_25 = 2024 if m_num >= 7 else 2025
        yr_25_26 = 2025 if m_num >= 7 else 2026

        vol_24_25 = evo[
            (evo["fecha"].dt.year == yr_24_25) & (evo["fecha"].dt.month == m_num)
        ]["total_muestras"].sum()

        vol_25_26 = evo[
            (evo["fecha"].dt.year == yr_25_26) & (evo["fecha"].dt.month == m_num)
        ]["total_muestras"].sum()

        result_rows.append({
            "order": idx + 1,
            "mes_nombre": m_name,
            "Ciclo 24/25": int(vol_24_25),
            "Ciclo 25/26": int(vol_25_26),
        })

    return pd.DataFrame(result_rows)


def generate_communication_campaign_insights(df: pd.DataFrame) -> list[dict]:
    """Generates actionable communication campaign recommendations for producers (HU-02).

    Returns list of dicts with insight details: [titulo, categoria, detalle, nivel].
    """
    if df.empty:
        return []

    distribution = compute_crop_distribution(df, top_n=10)
    top_crop = distribution.iloc[0]["especies"] if not distribution.empty else "N/A"
    top_pct = distribution.iloc[0]["porcentaje"] if not distribution.empty else 0.0

    secondary_crops = distribution.iloc[1:5]["especies"].tolist() if len(distribution) > 1 else []

    insights = [
        {
            "titulo": f"Campaña de Fidelización y Servicios Especiales — {top_crop}",
            "categoria": "Cultivo Dominante",
            "detalle": f"{top_crop} representa el {top_pct:.1f}% de la demanda total del laboratorio. Se recomienda lanzar promociones de análisis de pureza y poder germinativo 60 días antes de la ventana de siembra principal.",
            "nivel": "Prioritario",
            "color": "#1E40AF",
            "bg": "#EFF6FF",
        },
        {
            "titulo": f"Campaña de Fomento y Captación de Productores — Especies Secundarias ({', '.join(secondary_crops[:3])})",
            "categoria": "Diversificación de Demanda",
            "detalle": f"Los cultivos secundarios ({', '.join(secondary_crops[:3])}) presentan potencial de crecimiento en la zona de influencia. Promover paquetes multicultivo y convenios comerciales para aumentar volumen en meses de baja demanda.",
            "nivel": "Oportunidad",
            "color": "#166534",
            "bg": "#DCFCE7",
        },
        {
            "titulo": "Planificación de Campañas según Ventana Estacional",
            "categoria": "Estacionalidad Pre-Cosecha",
            "detalle": "Iniciar difusión técnica y recordatorios automáticos por email 45 días antes de los picos históricos estacionales para evitar la congestión del laboratorio en la última semana de recepción.",
            "nivel": "Operativo",
            "color": "#92400E",
            "bg": "#FEF3C7",
        },
    ]
    return insights


