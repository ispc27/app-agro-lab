# AgroLab — Plataforma de Análisis y Analítica Agronómica

Plataforma corporativa e interactiva para el análisis de datos agronómicos, monitoreo de capacidad operativa de laboratorios y segmentación comercial de cuentas.

---

## Módulos de Análisis

La plataforma proporciona tres áreas analíticas principales:

### 1. Análisis de Clientes Frecuentes
- Monitoreo de cuentas por volumen de muestras enviadas al laboratorio.
- Filtros interactivos por periodo de tiempo y especie de cultivo.

### 2. Monitoreo de Cultivos y Capacidad Operativa
- Métricas acumuladas y distribución por especie de cultivo (Top 10 y agrupación secundaria).
- Análisis de evolución estacional de producción para cultivos clave.
- Alertas de capacidad operativa sobre el volumen mensual total de muestras (todas las especies): alerta operativa desde 140 muestras y cuello de botella desde 190.

### 3. Segmentación RFM y Riesgo de Fuga
- Clasificación de cuentas mediante scoring RFM (Recencia, Frecuencia y Valor Monetario) sobre un período filtrable (por defecto, el último año).
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

4. **Abrir el dashboard en el navegador**: ingresar a [http://localhost:8501](http://localhost:8501). El navegador no se abre automáticamente porque `.streamlit/config.toml` define `headless = true`.

5. **Iniciar sesión**: usuario `admin`. La contraseña la provee el equipo (en `config.example.yaml` solo se guarda su hash bcrypt).

### Datos incluidos

El dataset `data/raw/sample_agro_data.csv` está versionado en el repositorio, por lo que el dashboard muestra datos apenas se clona el proyecto. Fue generado a partir de `notebooks/BD_lab_28-8-26.xlsx`, con fechas en formato `MM-DD-AA` e importes en formato `$ N.NN`, tal como los espera `load_agronomic_data()`.

Para detener la aplicación, presionar `Ctrl+C` en la terminal donde se está ejecutando.

---

## Documentación para Desarrolladores

Para conocer la estructura interna de archivos, convenciones de código y el flujo de trabajo del equipo, consulte la guía técnica:

**[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)**