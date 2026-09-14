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


@st.cache_data(show_spinner="Cargando y procesando dataset agronómico (ETL)...")
def load_agronomic_data() -> pd.DataFrame:
    """Loads, cleans, and transforms the agronomic dataset (CRISP-DM ETL Pipeline).

    Sources supported:
    1. Primary Processed: data/processed/cleaned_agro_data.csv
    2. Primary Raw: data/raw/BD_lab_28-8-26.xlsx (Sheet 'Export')
    """
    base_dir = get_base_dir()
    processed_path = os.path.join(base_dir, "data", "processed", "cleaned_agro_data.csv")
    excel_path = os.path.join(base_dir, "data", "raw", "BD_lab_28-8-26.xlsx")

    if os.path.exists(processed_path):
        df = pd.read_csv(processed_path)
        date_cols = ["fecha_ing_muestra", "fecha_de_certificacion", "fecha_factura"]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        df["id_muestra"] = df["id_muestra"].astype(int)
        df["id_cliente"] = df["id_cliente"].astype(int)
        return df

    if os.path.exists(excel_path):
        df = pd.read_excel(excel_path, sheet_name=0)
    else:
        return pd.DataFrame()

    # Drop null rows in critical identifier columns
    df = df.dropna(subset=["Muestra", "Id"]).reset_index(drop=True)

    # Remove sample duplicates, keeping the latest entry
    df = df.drop_duplicates(subset=["Muestra"], keep="last").reset_index(drop=True)

    # Parse date columns to datetime64[ns]
    columnas_fecha = ["Fecha Ing Muestra", "Fecha de Certificacion", "Fecha Factura"]
    for col in columnas_fecha:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Clean and convert Importe Solicitud to float
    if "Importe Solicitud" in df.columns:
        if df["Importe Solicitud"].dtype == object:
            df["Importe Solicitud"] = (
                df["Importe Solicitud"]
                .astype(str)
                .str.replace("$", "", regex=False)
                .str.strip()
                .astype(float)
            )
        else:
            df["Importe Solicitud"] = df["Importe Solicitud"].astype(float)

    # Rename columns to snake_case
    df = df.rename(columns=COLUMN_RENAME_MAP)

    # Integer type casting for IDs
    df["id_muestra"] = df["id_muestra"].astype(int)
    df["id_cliente"] = df["id_cliente"].astype(int)

    # Save processed backup CSV for auditing
    processed_dir = os.path.join(base_dir, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    df.to_csv(os.path.join(processed_dir, "cleaned_agro_data.csv"), index=False)

    return df


@st.cache_data(show_spinner="Actualizando índice de inflación (INDEC)...")
def load_ipc_data() -> pd.DataFrame | None:
    """Loads national IPC inflation index (INDEC), using local backup if network is unavailable."""
    from src.modules.rfm_segmentation.calculator import fetch_ipc_inflation_index
    local_backup = os.path.join(get_base_dir(), "data", "raw", "ipc_indec_mensual.csv")
    return fetch_ipc_inflation_index(local_backup_path=local_backup)
