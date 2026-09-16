import os
import pandas as pd
import pytest
from src.config.settings import get_base_dir, load_agronomic_data


def test_cleaned_agro_data_file_exists():
    base_dir = get_base_dir()
    csv_path = os.path.join(base_dir, "data", "processed", "cleaned_agro_data.csv")
    assert os.path.exists(csv_path), f"El archivo procesado no existe en {csv_path}"


def test_load_agronomic_data_integrity():
    df = load_agronomic_data()
    assert not df.empty, "El dataset agronómico cargado no debe estar vacío"
    assert len(df) == 8150, f"Se esperaban 8.150 registros limpios, se obtuvieron {len(df)}"

    required_columns = [
        "fecha_ing_muestra", "id_muestra", "id_cliente", "razon_social",
        "laboratorios", "tipo_analisis", "especies", "importe_solicitud"
    ]
    for col in required_columns:
        assert col in df.columns, f"Columna requerida '{col}' no encontrada en el dataset"


def test_no_duplicate_samples():
    df = load_agronomic_data()
    assert df["id_muestra"].duplicated().sum() == 0, "No deben existir muestras duplicadas en el dataset limpio"


def test_column_datatypes():
    df = load_agronomic_data()
    assert pd.api.types.is_datetime64_any_dtype(df["fecha_ing_muestra"]), "fecha_ing_muestra debe ser datetime"
    assert pd.api.types.is_integer_dtype(df["id_muestra"]), "id_muestra debe ser entero"
    assert pd.api.types.is_integer_dtype(df["id_cliente"]), "id_cliente debe ser entero"
    assert pd.api.types.is_numeric_dtype(df["importe_solicitud"]), "importe_solicitud debe ser numérico"
