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

@st.cache_data(show_spinner="Loading agronomic dataset...")
def load_agronomic_data() -> pd.DataFrame:
    """Loads the sample agronomic dataset from data/raw/sample_agro_data.csv."""
    data_path = os.path.join(get_base_dir(), "data", "raw", "sample_agro_data.csv")
    if not os.path.exists(data_path):
        return pd.DataFrame()
    df = pd.read_csv(data_path)
    df['fecha'] = pd.to_datetime(df['fecha'])
    return df
