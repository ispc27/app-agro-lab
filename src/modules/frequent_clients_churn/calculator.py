import pandas as pd


def calcular_volumen_por_cliente(
    df: pd.DataFrame,
    fecha_inicio: pd.Timestamp | None = None,
    fecha_fin: pd.Timestamp | None = None,
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
    data = df.copy()

    if fecha_inicio is not None:
        data = data[data["fecha_ing_muestra"] >= pd.Timestamp(fecha_inicio)]
    if fecha_fin is not None:
        data = data[data["fecha_ing_muestra"] <= pd.Timestamp(fecha_fin)]
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


def calcular_alerta_churn_estacional(
    df: pd.DataFrame,
    fecha_referencia: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Detecta clientes con Alerta de Churn Estacional.

    Compara, para cada cliente, el volumen de muestras enviadas en el mes de la fecha de
    referencia contra el promedio histórico de ese cliente en ese mismo mes calendario en
    años anteriores. Si el volumen actual es 0% del promedio histórico (no envió nada este
    año en su época habitual), se marca en alerta.

    Args:
        df: DataFrame limpio con columnas fecha_ing_muestra, id_cliente, id_muestra.
        fecha_referencia: fecha que define "hoy" para el análisis. None = fecha máxima del dataset.

    Returns:
        DataFrame con columnas [id_cliente, volumen_actual, promedio_historico_mismo_mes,
        alerta_churn_estacional], solo para clientes con actividad histórica en ese mes.
    """
    data = df.copy()

    if fecha_referencia is None:
        fecha_referencia = data["fecha_ing_muestra"].max()

    mes_actual = fecha_referencia.month
    anio_actual = fecha_referencia.year

    en_mes = data[data["fecha_ing_muestra"].dt.month == mes_actual]

    volumen_actual = (
        en_mes[en_mes["fecha_ing_muestra"].dt.year == anio_actual]
        .groupby("id_cliente")["id_muestra"]
        .nunique()
        .rename("volumen_actual")
    )

    historico = en_mes[en_mes["fecha_ing_muestra"].dt.year < anio_actual].copy()
    historico["anio"] = historico["fecha_ing_muestra"].dt.year
    promedio_historico = (
        historico.groupby(["id_cliente", "anio"])["id_muestra"]
        .nunique()
        .groupby("id_cliente")
        .mean()
        .rename("promedio_historico_mismo_mes")
    )

    resumen = pd.concat([volumen_actual, promedio_historico], axis=1)
    # Solo tiene sentido evaluar clientes con historial en ese mes (promedio no nulo)
    resumen = resumen[resumen["promedio_historico_mismo_mes"].notna()].fillna(0)
    resumen["alerta_churn_estacional"] = (
        (resumen["volumen_actual"] == 0) & (resumen["promedio_historico_mismo_mes"] > 0)
    )

    return resumen.reset_index().sort_values(
        ["alerta_churn_estacional", "promedio_historico_mismo_mes"], ascending=[False, False]
    ).reset_index(drop=True)
