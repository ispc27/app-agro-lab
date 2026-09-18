import pandas as pd
import pytest
from src.modules.crop_capacity import (
    assess_capacity_alerts,
    compute_crop_distribution,
    compute_monthly_evolution,
    compute_critical_intervals,
    compute_seasonal_peak_months,
    compute_campaign_comparison,
    generate_communication_campaign_insights,
)


@pytest.fixture
def sample_crops_df():
    # 12 different crops
    crops = ["Soja", "Trigo", "Maíz", "Girasol", "Cebada", "Sorgo", "Maní", "Centeno", "Avena", "Arroz", "Algodón", "Colza"]
    records = []
    sample_id = 1
    for idx, crop in enumerate(crops):
        # assign decreasing number of samples
        count = 30 - (idx * 2)
        for i in range(count):
            records.append({
                "fecha_ing_muestra": pd.Timestamp("2026-01-01") + pd.DateOffset(months=i % 6),
                "id_muestra": sample_id,
                "especies": crop,
                "tipo_analisis": "Poder Germinativo" if i % 2 == 0 else "Pureza",
            })
            sample_id += 1
    return pd.DataFrame(records)


def test_crop_distribution_pareto_and_exact_sum(sample_crops_df):
    dist = compute_crop_distribution(sample_crops_df, top_n=10)
    assert len(dist) == 11  # 10 top crops + 1 "Otras" row
    assert dist.iloc[-1]["especies"] == "Otras"

    total_samples = sample_crops_df["id_muestra"].nunique()
    table_sum = dist["total_muestras"].sum()
    assert total_samples == table_sum, f"El total acumulado ({total_samples}) debe coincidir de forma exacta con la suma de la tabla ({table_sum})"


def test_continuous_monthly_evolution_no_gaps():
    # Dataset with samples in Jan and Mar 2026, but missing Feb 2026
    df = pd.DataFrame({
        "fecha_ing_muestra": pd.to_datetime(["2026-01-15", "2026-03-15"]),
        "id_muestra": [1, 2],
        "especies": ["Trigo", "Trigo"],
    })
    evo = compute_monthly_evolution(df, "Trigo")
    # Must contain Jan, Feb, Mar (3 months)
    assert len(evo) == 3
    # Feb must have 0 samples
    feb_row = evo[evo["fecha"].dt.month == 2]
    assert len(feb_row) == 1
    assert feb_row.iloc[0]["total_muestras"] == 0


def test_capacity_alerts_thresholds():
    df = pd.DataFrame({
        "fecha_ing_muestra": pd.to_datetime([
            "2026-01-01", "2026-01-02",
            "2026-02-01", "2026-02-02", "2026-02-03", "2026-02-04",
            "2026-03-01", "2026-03-02", "2026-03-03", "2026-03-04", "2026-03-05",
        ]),
        "id_muestra": list(range(1, 12)),
        "especies": ["Soja"] * 11,
    })
    # Capacity = 5:
    # Jan = 2 (40% -> Normal)
    # Feb = 4 (80% -> Advertencia >= 75%)
    # Mar = 5 (100% -> Saturación >= 90%)
    res, _ = assess_capacity_alerts(df, "Soja", critical_capacity=5.0)

    states = dict(zip(res["fecha"].dt.month, res["estado"]))
    assert states[1] == "Normal"
    assert states[2] == "Advertencia"
    assert states[3] == "Saturación"


def test_fixed_operational_thresholds_142_and_191():
    # Jan: 100 (< 142 -> Normal)
    # Feb: 150 (>= 142 and < 191 -> Alerta Operativa)
    # Mar: 200 (>= 191 -> Cuello de Botella)
    records = []
    for _ in range(100):
        records.append({"fecha_ing_muestra": pd.Timestamp("2026-01-10"), "id_muestra": len(records) + 1, "especies": "Soja"})
    for _ in range(150):
        records.append({"fecha_ing_muestra": pd.Timestamp("2026-02-10"), "id_muestra": len(records) + 1, "especies": "Soja"})
    for _ in range(200):
        records.append({"fecha_ing_muestra": pd.Timestamp("2026-03-10"), "id_muestra": len(records) + 1, "especies": "Soja"})

    df = pd.DataFrame(records)
    res, ref_cap = assess_capacity_alerts(df, "Soja")
    assert ref_cap == 191.0

    states = dict(zip(res["fecha"].dt.month, res["estado"]))
    assert states[1] == "Normal"
    assert states[2] == "Alerta Operativa"
    assert states[3] == "Cuello de Botella"



def test_compute_critical_intervals(sample_crops_df):
    intervals = compute_critical_intervals(sample_crops_df, ["Soja", "Trigo"])
    assert not intervals.empty
    assert set(intervals["especies"].unique()) == {"Soja", "Trigo"}
    assert "tipo_analisis" in intervals.columns
    assert "porcentaje_cultivo" in intervals.columns


def test_consolidated_monthly_evolution_and_alerts(sample_crops_df):
    # Pass crop_species=None or "Todos los Cultivos"
    evo_all = compute_monthly_evolution(sample_crops_df, crop_species=None)
    total_samples = sample_crops_df["id_muestra"].nunique()
    assert evo_all["total_muestras"].sum() == total_samples

    alerts_all, max_cap = assess_capacity_alerts(sample_crops_df, crop_species="Todos los Cultivos")
    assert max_cap > 0
    assert "estado" in alerts_all.columns


def test_optional_enhancements_functions(sample_crops_df):
    peak_info = compute_seasonal_peak_months(sample_crops_df, "Soja")
    assert "peak_months_str" in peak_info
    assert peak_info["peak_concentration_pct"] > 0

    comp_df = compute_campaign_comparison(sample_crops_df)
    assert len(comp_df) == 12
    assert "Ciclo 24/25" in comp_df.columns
    assert "Ciclo 25/26" in comp_df.columns

    insights = generate_communication_campaign_insights(sample_crops_df)
    assert len(insights) >= 3
    assert "titulo" in insights[0]


