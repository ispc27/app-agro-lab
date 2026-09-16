import pandas as pd
import pytest
from src.modules.frequent_clients_churn import (
    compute_volume_by_client,
    detect_seasonal_churn_alerts,
)


@pytest.fixture
def sample_agro_df():
    data = {
        "fecha_ing_muestra": pd.to_datetime([
            "2025-08-10", "2025-08-12", "2025-08-15",
            "2026-08-01", "2026-08-05",
            "2024-08-10", "2024-08-12",
        ]),
        "id_muestra": [101, 102, 103, 104, 105, 106, 107],
        "id_cliente": [1, 1, 2, 1, 3, 2, 2],
        "razon_social": ["Cliente A", "Cliente A", "Cliente B", "Cliente A", "Cliente C", "Cliente B", "Cliente B"],
        "especies": ["Soja", "Soja", "Trigo", "Soja", "Maíz", "Trigo", "Trigo"],
        "importe_solicitud": [1000.0, 1000.0, 1500.0, 2000.0, 800.0, 1200.0, 1200.0],
    }
    return pd.DataFrame(data)


def test_compute_volume_descending_order(sample_agro_df):
    vol = compute_volume_by_client(sample_agro_df, client_status="todos")
    assert not vol.empty
    # Must be sorted descending by total_muestras
    muestras_list = vol["total_muestras"].tolist()
    assert muestras_list == sorted(muestras_list, reverse=True)


def test_client_status_filtering(sample_agro_df):
    # Filter to 2026 only: Cliente A and C have samples, Cliente B has 0 samples in 2026
    start_d = pd.Timestamp("2026-01-01")
    end_d = pd.Timestamp("2026-12-31")

    all_vol = compute_volume_by_client(sample_agro_df, start_date=start_d, end_date=end_d, client_status="todos")
    assert len(all_vol) == 3
    assert set(all_vol["estado_cliente"].unique()) == {"Activo", "Inactivo"}

    active_vol = compute_volume_by_client(sample_agro_df, start_date=start_d, end_date=end_d, client_status="activos")
    assert len(active_vol) == 2
    assert (active_vol["total_muestras"] > 0).all()

    inactive_vol = compute_volume_by_client(sample_agro_df, start_date=start_d, end_date=end_d, client_status="inactivos")
    assert len(inactive_vol) == 1
    assert inactive_vol.iloc[0]["id_cliente"] == 2
    assert inactive_vol.iloc[0]["total_muestras"] == 0


def test_seasonal_churn_alert_detection(sample_agro_df):
    # In August (month 8):
    # Cliente 2 sent samples in 2024 and 2025, but 0 samples in August 2026
    alerts = detect_seasonal_churn_alerts(sample_agro_df, reference_month=8)
    churn_clients = alerts[alerts["alerta_churn_estacional"]]

    assert not churn_clients.empty
    assert 2 in churn_clients["id_cliente"].values
    assert churn_clients.loc[churn_clients["id_cliente"] == 2, "volumen_actual"].values[0] == 0
    assert churn_clients.loc[churn_clients["id_cliente"] == 2, "promedio_historico_mismo_mes"].values[0] > 0


def test_multi_crop_species_filtering(sample_agro_df):
    # Filter by a list of species: ["Soja", "Maíz"]
    vol_multi = compute_volume_by_client(sample_agro_df, crop_species=["Soja", "Maíz"])
    assert not vol_multi.empty
    # Cliente A (Soja: 3) and Cliente C (Maíz: 1) should be present
    assert 1 in vol_multi["id_cliente"].values
    assert 3 in vol_multi["id_cliente"].values
    assert 2 not in vol_multi["id_cliente"].values  # Cliente B only has Trigo

