# Diccionario de Variables — AgroLab Dashboard

Este documento define la estructura oficial, tipos de datos, descripciones comerciales y roles funcionales de cada una de las variables contenidas en la base de datos del laboratorio (`data/raw/BD_lab_28-8-26.xlsx`) y en el dataset procesado de producción (`data/processed/cleaned_agro_data.csv`).

---

## Estructura General del Dataset

- **Origen de Datos Crudo:** `data/raw/BD_lab_28-8-26.xlsx` (Hoja `'Export'`) — 8.157 filas, 15 variables.
- **Dataset Limpio Procesado:** `data/processed/cleaned_agro_data.csv` — **8.149 registros validados** y **16 variables** (15 base + `anio`), con 0 valores nulos y 0 duplicados en muestras.
- **Granularidad:** Cada fila representa una muestra agrícola individual ingresada y ensayada por el laboratorio.
- **Rango Temporal:** Desde el `2020-06-01` hasta el `2026-08-28`.

---

## Tabla del Diccionario de Datos

| Variable Origen | Nombre Normalizado (`snake_case`) | Tipo Origen | Tipo Destino (ETL) | Nulos Permitidos (Limpio) | Descripción de Negocio | Rol en la Aplicación y Dashboard |
|---|---|---|---|---|---|---|
| `Fecha Ing Muestra` | `fecha_ing_muestra` | `Object` / `Text` | `datetime64[ns]` | No | Fecha de recepción e ingreso físico de la muestra al laboratorio. | Filtro de fechas principal (HU-01, HU-02), serie cronológica continua (HU-02), cálculo de Recencia en RFM e inactividad a 90 días (HU-01, HU-03). |
| `Muestra` | `id_muestra` | `float64` | `int64` | No | Código de identificación único asignado a la muestra ensayada. | Clave Primaria. Métrica de volumen analítico (HU-01, HU-02) y Frecuencia en RFM (HU-03). |
| `Carta Camara` | `carta_camara` | `float64` | `int64` / `float64` | No | Número de carta de porte o expediente arbitral asociado. | Atributo de trazabilidad comercial de la muestra. |
| `Fecha de Certificacion` | `fecha_de_certificacion` | `datetime64[us]` | `datetime64[ns]` | No | Fecha oficial en que se emitió el certificado de análisis técnico. | Control de tiempos de procesamiento y certificación de ensayos. |
| `Certificado` | `certificado` | `float64` | `int64` | No | Número correlativo del certificado oficial de resultados emitido. | Identificador del certificado de análisis. |
| `Fecha Factura` | `fecha_factura` | `datetime64[us]` | `datetime64[ns]` | No | Fecha de emisión de la factura fiscal correspondiente. | Control y conciliación contable de ventas. |
| `PtoVta` | `ptovta` | `float64` | `int64` | No | Punto de venta o sucursal emisora del comprobante fiscal. | Atributo de facturación fiscal. |
| `Letra` | `letra` | `string` | `string` | No | Tipo o letra del comprobante fiscal ('FA', 'FB', etc.). | Clasificación fiscal de comprobante. |
| `Numero Factura` | `numero_factura` | `float64` | `int64` | No | Número consecutivo de la factura fiscal emitida. | Identificador fiscal de factura comercial. |
| `Id` | `id_cliente` | `float64` | `int64` | No | Código de identificación único anonimizado del cliente. | Identificador de cuenta comercial. Agregaciones de volumen (HU-01) y quintiles RFM (HU-03). Todos los clientes son evaluados por igual. |
| `Razón Social` | `razon_social` | `string` | `string` | No | Razón social oficial del cliente (anonimizada como `"NN"` en el 100% de los registros). | Campo estático por anonimización. En la interfaz se presenta sistemáticamente como `Cliente #{id_cliente}`. |
| `Laboratorios` | `laboratorios` | `string` | `string` | No | Unidad o departamento técnico que realizó el ensayo (ej. 'Semillas'). | Segmentación por unidad operativa del laboratorio. |
| `Tipo analisis` | `tipo_analisis` | `string` | `string` | No | Descripción comercial de la solicitud o paquete contratado. | Clasificación comercial de servicios. No representa recuentos unitarios de determinaciones de laboratorio. |
| `Especies` | `especies` | `string` | `string` | No | Cultivo agronómico de la muestra (Soja, Trigo, Maíz, Girasol, etc.). | Filtro por cultivo (HU-01), Pareto 80/20 (HU-02) y análisis estacional comparativo Soja vs. Trigo (HU-02/Obj. 3). |
| `Importe Solicitud` | `importe_solicitud` | `float64` | `float64` | No | Monto nominal cobrado por la solicitud de análisis ($). | Métrica económica para facturación acumulada y cálculo del Valor Monetario (M) en RFM (HU-03). |
| *Calculada (ETL)* | `anio` | `int64` | `int64` | No | Año calendario del ingreso de la muestra (`fecha_ing_muestra.dt.year`). | Dimensión temporal auxiliar para agregaciones interanuales y campañas agrícolas. |

---

## Reglas de Integridad y Validación de Negocio

1. **Depuración de Registros Nulos Estructurales:**
   - Se eliminaron las 2 filas de pie de página/totales al final del archivo crudo.
   - Se eliminaron 2 registros técnicos con fecha de certificación ausente (muestras `389801` y `403626`), pasando de 8.157 a 8.153 registros.
2. **Deduplicación Estricta de Muestras:**
   - Se eliminaron 4 muestras duplicadas (`id_muestra`), conservando el primer registro (`keep='first'`), consolidando los **8.149 registros limpios definitivos**.
3. **Igualdad de Cartera (Sin Filtro Arbitrario de Convenios):**
   - Todos los clientes son legítimos y evaluados bajo las mismas reglas de negocio.
   - Se eliminó el filtro de exclusión `id_cliente > 50.000` tanto en el dashboard como en los notebooks, ya que dichos IDs corresponden a identificadores asignados por el sistema de gestión y no a convenios excepcionales.
4. **Anonimización de Clientes:**
   - La columna `razon_social` contiene únicamente el valor `"NN"`. En la capa de presentación y tablas analíticas se utiliza de forma estandarizada `Cliente #{id_cliente}`.
5. **Estandarización y Formato Temporal:**
   - Todas las fechas (`fecha_ing_muestra`, `fecha_de_certificacion`, `fecha_factura`) se normalizan a formato `datetime64[ns]` sin información de zona horaria.
