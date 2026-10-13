import pandas as pd
import pytest
from src.modules.rfm_segmentation import compute_rfm_score


@pytest.fixture
def sample_rfm_df():
    # 10 regular clients and 1 corporate agreement client (>50000)
    records = []
    base_date = pd.Timestamp("2026-08-28")

    for c_id in range(1, 11):
        # Client 1: very recent (0 days ago), high frequency (20 samples), high value (20000)
        # Client 10: inactive (300 days ago), high frequency (20 samples), high value (20000) -> Should be "En Riesgo"!
        days_ago = (c_id - 1) * 30
        sample_count = 5 if c_id < 8 else 20
        value_each = 1000.0 * c_id

        for s in range(sample_count):
            records.append({
                "fecha_ing_muestra": base_date - pd.Timedelta(days=days_ago),
                "id_muestra": c_id * 100 + s,
                "id_cliente": c_id,
                "razon_social": f"Cliente {c_id}",
                "importe_solicitud": value_each,
            })

    # Add agreement account (> 50000)
    records.append({
        "fecha_ing_muestra": base_date,
        "id_muestra": 9999,
        "id_cliente": 50001,
        "razon_social": "Convenio Especial",
        "importe_solicitud": 500000.0,
    })

    return pd.DataFrame(records)


def test_rfm_scoring_and_agreement_exclusion(sample_rfm_df):
    # Default: exclude_agreements=False, so 50001 is included (all clients equal)
    rfm_all = compute_rfm_score(sample_rfm_df)
    assert 50001 in rfm_all["id_cliente"].values
    assert len(rfm_all) == 11

    # When explicit exclude_agreements=True is passed
    rfm = compute_rfm_score(sample_rfm_df, exclude_agreements=True)
    assert 50001 not in rfm["id_cliente"].values
    assert len(rfm) == 10

    # Score of 3 digits
    for score in rfm["rfm_score"]:
        assert len(score) == 3
        assert all(c in "12345" for c in score)

    # R, F, M should be integer quintiles between 1 and 5
    assert rfm["R"].between(1, 5).all()
    assert rfm["F"].between(1, 5).all()
    assert rfm["M"].between(1, 5).all()


def test_at_risk_account_labeling(sample_rfm_df):
    rfm = compute_rfm_score(sample_rfm_df, exclude_agreements=True)

    # Accounts with R in [1, 2] and (F >= 4 or M >= 4) must be flagged "en_riesgo"
    at_risk = rfm[rfm["en_riesgo"]]
    for _, row in at_risk.iterrows():
        assert row["R"] <= 2
        assert (row["F"] >= 4) or (row["M"] >= 4)


def test_cycle_filtering(sample_rfm_df):
    # Filter to specific date window
    rfm_cycle = compute_rfm_score(
        sample_rfm_df,
        start_date="2026-08-01",
        end_date="2026-08-28",
        exclude_agreements=True,
    )
    assert not rfm_cycle.empty
    # Only clients active in August 2026 should be returned
    assert len(rfm_cycle) < 10


def test_strategic_segments_and_alert_levels(sample_rfm_df):
    rfm = compute_rfm_score(sample_rfm_df)

    assert "segmento" in rfm.columns
    assert "nivel_alerta" in rfm.columns
    assert "accion_recomendada" in rfm.columns

    # Verify that valid segments are exclusively from the 5 official categories
    official_segments = {"Campeones", "Fieles / Alto Valor", "Potenciales", "En Riesgo", "Perdidos"}
    assert set(rfm["segmento"].unique()).issubset(official_segments)

    # Verify that all at-risk clients have segment "En Riesgo"
    at_risk = rfm[rfm["en_riesgo"]]
    assert (at_risk["segmento"] == "En Riesgo").all()
    assert at_risk["nivel_alerta"].str.contains("Riesgo|Crítico|Alto", case=False).all()

    # Verify that non-risk clients have "Activo Saludable"
    healthy = rfm[~rfm["en_riesgo"]]
    assert (healthy["nivel_alerta"] == "Activo Saludable").all()



