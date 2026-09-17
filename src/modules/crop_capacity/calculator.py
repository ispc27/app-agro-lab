import numpy as np
import pandas as pd

ESPECIES_EVOLUCION = ["Soja", "Trigo"]

# Umbrales fijos de volumen mensual total (todas las especies), definidos por el laboratorio.
UMBRAL_ALERTA_OPERATIVA = 142
UMBRAL_CUELLO_BOTELLA = 191


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


def calcular_evolucion_mensual(df: pd.DataFrame, especie: str | None = None) -> pd.DataFrame:
    """Calcula el volumen mensual de muestras, sin huecos en el tiempo.

    Cualquier mes del rango del dataset sin muestras se completa con 0, para que el
    gráfico resultante sea una curva continua (Criterio 2.2).

    Args:
        df: DataFrame limpio con columnas fecha_ing_muestra, especies, id_muestra.
        especie: nombre de la especie a analizar. None = total de todas las especies.

    Returns:
        DataFrame [fecha, total_muestras] con un registro por cada mes del rango del dataset.
    """
    rango_completo = pd.period_range(
        df["fecha_ing_muestra"].min().to_period("M"),
        df["fecha_ing_muestra"].max().to_period("M"),
        freq="M",
    )

    data = df if especie is None else df[df["especies"] == especie]
    anio_mes = data["fecha_ing_muestra"].dt.to_period("M")
    conteo = data.groupby(anio_mes)["id_muestra"].nunique()
    conteo = conteo.reindex(rango_completo, fill_value=0)

    resultado = conteo.reset_index()
    resultado.columns = ["anio_mes", "total_muestras"]
    resultado["fecha"] = resultado["anio_mes"].dt.to_timestamp()
    return resultado[["fecha", "total_muestras"]]


def calcular_alerta_capacidad(df: pd.DataFrame) -> pd.DataFrame:
    """Clasifica cada mes según el volumen total de muestras del laboratorio (Criterio 2.3).

    Suma las muestras de todas las especies y compara el total mensual contra los
    umbrales fijos: Alerta operativa desde 142 muestras y Cuello de botella desde 191.

    Args:
        df: DataFrame limpio con columnas fecha_ing_muestra, especies, id_muestra.

    Returns:
        DataFrame [fecha, total_muestras, estado], un registro por mes.
    """
    evolucion = calcular_evolucion_mensual(df)

    condiciones = [
        evolucion["total_muestras"] >= UMBRAL_CUELLO_BOTELLA,
        evolucion["total_muestras"] >= UMBRAL_ALERTA_OPERATIVA,
    ]
    evolucion["estado"] = np.select(condiciones, ["Cuello de botella", "Alerta operativa"], default="Normal")

    return evolucion
