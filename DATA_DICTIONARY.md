# Diccionario de Variables — AgroLab Dashboard

Este documento define la estructura oficial, tipos de datos, descripciones comerciales y roles funcionales de cada una de las variables contenidas en la base de datos del laboratorio (`data/raw/BD_lab_28-8-26.xlsx`).

---

## Estructura General del Dataset

- **Origen de Datos:** `data/raw/BD_lab_28-8-26.xlsx` (Hoja `'Export'`)
- **Dimensiones:** 8.157 registros y 15 variables.
- **Granularidad:** Cada fila representa una muestra agrícola ingresada y procesada por el laboratorio.

---

## Tabla del Diccionario de Datos

| Variable Origen | Nombre Normalizado (`snake_case`) | Tipo Origen | Tipo Destino (ETL) | Nulos Permitidos | Descripción de Negocio | Rol en la Aplicación |
|---|---|---|---|---|---|---|
| `Fecha Ing Muestra` | `fecha_ing_muestra` | `Object` / `Text` | `datetime64[ns]` | No | Fecha de recepción e ingreso físico de la muestra al laboratorio. | Filtro de fechas principal (HU-01, HU-02), Serie temporal continua (HU-02), Recencia RFM y Churn (HU-03). |
| `Muestra` | `id_muestra` | `float64` | `int64` | No | Código de identificación único asignado a la muestra. | Clave Primaria. Conteos de volumen de muestras (HU-01, HU-02), Frecuencia RFM (HU-03). |
| `Carta Camara` | `carta_camara` | `float64` | `Int64` / `float64` | Sí | Número de carta de porte o expediente arbitral asociado. | Atributo secundario de trazabilidad de la muestra. |
| `Fecha de Certificacion` | `fecha_de_certificacion` | `datetime64[us]` | `datetime64[ns]` | Sí | Fecha oficial en que se emitió el certificado de análisis. | Control de tiempos de procesamiento técnico. |
| `Certificado` | `certificado` | `float64` | `Int64` / `float64` | Sí | Número correlativo del certificado oficial de resultados. | Atributo de certificación del análisis. |
| `Fecha Factura` | `fecha_factura` | `datetime64[us]` | `datetime64[ns]` | Sí | Fecha de emisión de la factura comercial correspondiente. | Control y auditoría contable. |
| `PtoVta` | `ptovta` | `float64` | `Int64` | Sí | Punto de venta o sucursal emisora del comprobante fiscal. | Atributo contable regional. |
| `Letra` | `letra` | `string` | `string` | Sí | Tipo o letra del comprobante fiscal (A, B, C). | Clasificación fiscal de venta. |
| `Numero Factura` | `numero_factura` | `float64` | `Int64` | Sí | Número consecutivo del comprobante fiscal emitido. | Identificador de factura comercial. |
| `Id` | `id_cliente` | `float64` | `int64` | No | Código de identificación único del cliente o cuenta comercial. | Agregaciones por cliente, Ranking de Volumen (HU-01), Scoring RFM (HU-03). IDs > 50.000 identifican convenios/campañas. |
| `Razón Social` | `razon_social` | `string` | `string` | Sí | Nombre o razón social oficial de la empresa/cliente. | Nombre descriptivo del cliente en la interfaz UI. |
| `Laboratorios` | `laboratorios` | `string` | `string` | Sí | Departamento o área de laboratorio especializada que realizó el ensayo. | Segmentación por tipo de servicio analítico. |
| `Tipo analisis` | `tipo_analisis` | `string` | `string` | Sí | Nombre técnico del ensayo o determinación analítica solicitada. | Clasificación de servicios de laboratorio. |
| `Especies` | `especies` | `string` | `string` | Sí | Tipo de cultivo agronómico de la muestra (Soja, Trigo, Maíz, Maní, etc.). | Filtro por cultivo (HU-01), Distribución Pareto Top 10 + Otras y Alertas de Capacidad (HU-02). |
| `Importe Solicitud` | `importe_solicitud` | `float64` | `float64` | No | Monto nominal cobrado por la solicitud de análisis ($ ARS). | Base para el cálculo del Valor Monetario (M) en la Segmentación RFM (HU-03). |
| *Calculada (ETL)* | `anio` | `int64` | `int64` | No | Año calendario de ingreso de la muestra (`YYYY`). | Variable analítica auxiliar para agregaciones anuales. |

---

## Reglas de Integridad y Validación de Negocio

1. **Deduplicación de Muestras:** Registros duplicados por la variable `id_muestra` son filtrados en el ETL conservando la entrada más reciente.
2. **Cuentas de Convenio:** Los registros con `id_cliente > 50.000` corresponden a acuerdos comerciales/campañas especiales institucionales.
3. **Formato de Fechas:** Las fechas son normalizadas al estándar `YYYY-MM-DD` sin información de zona horaria.
