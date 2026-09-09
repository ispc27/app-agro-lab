# AgroLab — Plataforma de Análisis y Analítica Agronómica

Plataforma corporativa e interactiva para el análisis de datos agronómicos, monitoreo de capacidad operativa de laboratorios, detección de churn estacional y segmentación comercial de cuentas.

---

## Módulos de Análisis

La plataforma proporciona tres áreas analíticas principales:

### 1. Análisis de Clientes Frecuentes y Churn Estacional
- Monitoreo de cuentas por volumen de muestras enviadas al laboratorio.
- Filtros interactivos por periodo de tiempo y especie de cultivo.
- Detección de alertas por caída anómala en la recencia de envíos respecto a promedios históricos.

### 2. Monitoreo de Cultivos y Capacidad Operativa
- Métricas acumuladas y distribución por especie de cultivo (Top 10 y agrupación secundaria).
- Análisis de evolución estacional de producción para cultivos clave.
- Indicadores y alertas de volumen al alcanzar umbrales críticos de capacidad operativa en el laboratorio (75% de advertencia y 90% de saturación).

### 3. Segmentación RFM y Riesgo de Fuga
- Clasificación de cuentas mediante scoring RFM (Recencia, Frecuencia y Valor Monetario).
- Detección dinámica y listado prioritario de cuentas en riesgo de fuga para gestión comercial.

---

## Arquitectura del Proyecto

El sistema utiliza una arquitectura modular dividida en capas para separar la lógica de procesamiento de datos de la interfaz visual:

```text
app-agro-lab/
├── app.py                      # Enrutador principal de la aplicación
├── config.yaml                 # Configuración del sistema
├── DEVELOPER_GUIDE.md          # Guía técnica de desarrollo
├── README.md                   # Documentación principal
├── requirements.txt            # Dependencias de Python
├── data/                       # Almacenamiento de fuentes de datos
└── src/                        # Código fuente
    ├── config/                 # Configuración de entornos y carga de datos en caché
    ├── core/                   # Autenticación y gestión de sesiones
    ├── components/             # Componentes de interfaz (Tema visual y Sidebar)
    ├── modules/                # Lógica de negocio y procesamiento de datos
    └── views/                  # Vistas y pantallas del dashboard
```

---

## Ejecución del Sistema

### Requisitos
- Python 3.10 o superior

### Pasos para Ejecutar

1. **Crear y activar el entorno virtual (`.venv`)**:
   ```bash
   python -m venv .venv
   ```
   - **En Windows (PowerShell / CMD):**
     ```powershell
     .\.venv\Scripts\activate
     ```
   - **En Linux / macOS:**
     ```bash
     source .venv/bin/activate
     ```

2. **Instalar las dependencias del proyecto**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Iniciar la aplicación**:
   ```bash
   streamlit run app.py
   ```

---

## Documentación para Desarrolladores

Para conocer la estructura interna de archivos, convenciones de código y el flujo de trabajo del equipo, consulte la guía técnica:

**[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)**