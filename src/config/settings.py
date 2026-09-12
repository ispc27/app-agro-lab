import os
import yaml
import pandas as pd
import streamlit as st

def get_base_dir() -> str:
    """Returns the absolute path to the project root directory."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_config_path() -> str:
    """Returns the path to config.yaml, or falls back to config.example.yaml if config.yaml is not present."""
    base_dir = get_base_dir()
    primary_path = os.path.join(base_dir, "config.yaml")
    example_path = os.path.join(base_dir, "config.example.yaml")
    if os.path.exists(primary_path):
        return primary_path
    elif os.path.exists(example_path):
        return example_path
    return primary_path

def load_settings() -> dict:
    """Loads application settings and user credentials from config.yaml."""
    config_path = get_config_path()
    if not os.path.exists(config_path):
        st.error(f"Configuration file not found at: {config_path}")
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

COLUMN_RENAME_MAP = {
    "Fecha Ing Muestra": "fecha_ing_muestra",
    "Muestra": "id_muestra",
    "Carta Camara": "carta_camara",
    "Fecha de Certificacion": "fecha_de_certificacion",
    "Certificado": "certificado",
    "Fecha Factura": "fecha_factura",
    "PtoVta": "ptovta",
    "Letra": "letra",
    "Numero Factura": "numero_factura",
    "Id": "id_cliente",
    "Razón Social": "razon_social",
    "Laboratorios": "laboratorios",
    "Tipo analisis": "tipo_analisis",
    "Especies": "especies",
    "Importe Solicitud": "importe_solicitud",
}


@st.cache_data(show_spinner="Cargando dataset agronómico...")
def load_agronomic_data() -> pd.DataFrame:
    """Loads and cleans the agronomic dataset from data/raw/sample_agro_data.csv.

    Cleaning steps (ver notebooks/Testeo+practicas_2026.ipynb para el detalle):
    - Descarta filas completamente vacías (artefacto de exportación del CSV).
    - Descarta duplicados por número de muestra, conservando el registro más reciente.
    - Convierte fechas (texto "MM-DD-AA") e importe (texto "$ N.NN") a tipos reales.
    - Normaliza los nombres de columna a snake_case.
    """
    data_path = os.path.join(get_base_dir(), "data", "raw", "sample_agro_data.csv")
    if not os.path.exists(data_path):
        return pd.DataFrame()

    df = pd.read_csv(data_path)
    df = df.dropna(subset=["Muestra"]).reset_index(drop=True)
    df = df.drop_duplicates(subset=["Muestra"], keep="last").reset_index(drop=True)

    columnas_fecha = ["Fecha Ing Muestra", "Fecha de Certificacion", "Fecha Factura"]
    for col in columnas_fecha:
        df[col] = pd.to_datetime(df[col], format="%m-%d-%y")

    df["Importe Solicitud"] = (
        df["Importe Solicitud"].str.replace("$", "", regex=False).str.strip().astype(float)
    )

    df = df.rename(columns=COLUMN_RENAME_MAP)
    df["id_muestra"] = df["id_muestra"].astype(int)
    df["id_cliente"] = df["id_cliente"].astype(int)

    return df
