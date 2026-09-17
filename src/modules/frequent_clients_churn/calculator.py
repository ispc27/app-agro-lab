from datetime import date

import pandas as pd

from src.modules.common import filtrar_por_periodo


def calcular_volumen_por_cliente(
    df: pd.DataFrame,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    especie: str | None = None,
) -> pd.DataFrame:
    """Calcula el volumen de muestras por cliente, ordenado de forma descendente.

    Args:
        df: DataFrame limpio con columnas fecha_ing_muestra, id_cliente, id_muestra, especies.
        fecha_inicio: fecha mínima a incluir (inclusive). None = sin límite inferior.
        fecha_fin: fecha máxima a incluir (inclusive). None = sin límite superior.
        especie: si se indica, filtra solo esa especie de cultivo.

    Returns:
        DataFrame con columnas [id_cliente, total_muestras], ordenado por total_muestras desc.
    """
    data = filtrar_por_periodo(df, fecha_inicio, fecha_fin)
    if especie:
        data = data[data["especies"] == especie]

    resultado = (
        data.groupby("id_cliente")["id_muestra"]
        .nunique()
        .reset_index(name="total_muestras")
        .sort_values("total_muestras", ascending=False)
        .reset_index(drop=True)
    )
    return resultado
