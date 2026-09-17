from datetime import date

import pandas as pd


def calcular_rango_predefinido(
    fecha_min: date,
    fecha_max: date,
    meses: int | None,
) -> tuple[date, date]:
    """Calcula el rango (desde, hasta) de los últimos `meses` meses que terminan en fecha_max.

    Args:
        fecha_min: primera fecha disponible en el dataset; el rango nunca empieza antes.
        fecha_max: última fecha disponible en el dataset; es el fin del rango.
        meses: cantidad de meses hacia atrás. None = todo el período disponible.

    Returns:
        Tupla (desde, hasta) con fechas inclusivas.
    """
    if meses is None:
        return fecha_min, fecha_max
    desde = (pd.Timestamp(fecha_max) - pd.DateOffset(months=meses)).date()
    return max(desde, fecha_min), fecha_max


def filtrar_por_periodo(
    df: pd.DataFrame,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
) -> pd.DataFrame:
    """Devuelve una copia de df con las muestras ingresadas entre fecha_inicio y fecha_fin (inclusive).

    Args:
        df: DataFrame limpio con columna fecha_ing_muestra.
        fecha_inicio: fecha mínima a incluir. None = sin límite inferior.
        fecha_fin: fecha máxima a incluir. None = sin límite superior.
    """
    data = df.copy()
    if fecha_inicio is not None:
        data = data[data["fecha_ing_muestra"] >= pd.Timestamp(fecha_inicio)]
    if fecha_fin is not None:
        data = data[data["fecha_ing_muestra"] <= pd.Timestamp(fecha_fin)]
    return data
