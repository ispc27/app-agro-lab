import numpy as np
import pandas as pd

ESPECIES_CRITICAS = ["Soja", "Trigo"]


def calcular_distribucion_especies(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Calcula la distribución de muestras por especie, agrupando el resto en "Otras".

    Args:
        df: DataFrame limpio con columnas especies, id_muestra.
        top_n: cantidad de especies principales a mostrar individualmente.

    Returns:
        DataFrame [especies, total_muestras, porcentaje], con las top_n especies
        y una fila "Otras" agrupando el resto (si corresponde).
    """
    conteo = df.groupby("especies")["id_muestra"].nunique().sort_values(ascending=False)

    principales = conteo.head(top_n)
    resto = conteo.iloc[top_n:].sum()

    if resto > 0:
        principales = pd.concat([principales, pd.Series({"Otras": resto})])

    resultado = principales.reset_index()
    resultado.columns = ["especies", "total_muestras"]
    resultado["porcentaje"] = (resultado["total_muestras"] / resultado["total_muestras"].sum() * 100).round(1)
    return resultado


def calcular_evolucion_mensual(df: pd.DataFrame, especie: str) -> pd.DataFrame:
    """Calcula el volumen mensual de muestras de una especie, sin huecos en el tiempo.

    Cualquier mes del rango del dataset sin muestras de esa especie se completa con 0,
    para que el gráfico resultante sea una curva continua (Criterio 2.2).

    Args:
        df: DataFrame limpio con columnas fecha_ing_muestra, especies, id_muestra.
        especie: nombre de la especie a analizar.

    Returns:
        DataFrame [fecha, total_muestras] con un registro por cada mes del rango del dataset.
    """
    rango_completo = pd.period_range(
        df["fecha_ing_muestra"].min().to_period("M"),
        df["fecha_ing_muestra"].max().to_period("M"),
        freq="M",
    )

    data_especie = df[df["especies"] == especie].copy()
    data_especie["anio_mes"] = data_especie["fecha_ing_muestra"].dt.to_period("M")
    conteo = data_especie.groupby("anio_mes")["id_muestra"].nunique()
    conteo = conteo.reindex(rango_completo, fill_value=0)

    resultado = conteo.reset_index()
    resultado.columns = ["anio_mes", "total_muestras"]
    resultado["fecha"] = resultado["anio_mes"].dt.to_timestamp()
    return resultado[["fecha", "total_muestras"]]


def calcular_alerta_capacidad(
    df: pd.DataFrame,
    especie: str,
    capacidad_critica: float | None = None,
) -> tuple[pd.DataFrame, float]:
    """Calcula el estado de capacidad operativa mensual de una especie crítica.

    Compara el volumen de cada mes contra una capacidad crítica de referencia (por
    defecto, el máximo histórico mensual de esa especie) y clasifica el mes en
    Normal / Advertencia (>=75%) / Saturación (>=90%), según el Criterio 2.3.

    Args:
        df: DataFrame limpio con columnas fecha_ing_muestra, especies, id_muestra.
        especie: nombre de la especie crítica a evaluar.
        capacidad_critica: volumen mensual de referencia (100%). Si es None, se usa
            el máximo histórico mensual de la especie.

    Returns:
        Tupla (DataFrame [fecha, total_muestras, porcentaje_capacidad, estado], capacidad_critica usada).
    """
    evolucion = calcular_evolucion_mensual(df, especie)

    if capacidad_critica is None:
        capacidad_critica = float(evolucion["total_muestras"].max())

    if capacidad_critica <= 0:
        evolucion["porcentaje_capacidad"] = 0.0
    else:
        evolucion["porcentaje_capacidad"] = (evolucion["total_muestras"] / capacidad_critica * 100).round(1)

    condiciones = [
        evolucion["porcentaje_capacidad"] >= 90,
        evolucion["porcentaje_capacidad"] >= 75,
    ]
    evolucion["estado"] = np.select(condiciones, ["Saturación", "Advertencia"], default="Normal")

    return evolucion, capacidad_critica
