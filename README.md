# AgroLab — Plataforma de Análisis y Analítica Agronómica

Plataforma corporativa e interactiva para el análisis de datos agronómicos, monitoreo de capacidad operativa de laboratorios, detección de churn estacional y segmentación comercial de cuentas basada en la metodología **CRISP-DM** y una **Arquitectura Limpia en 5 Capas**.

---

## 📋 Módulos Analíticos e Historias de Usuario

La plataforma se estructura en tres áreas analíticas protegidas por **Control de Acceso Basado en Roles (RBAC)**:

### 1. Clientes Frecuentes y Churn Estacional (HU-01)
- **Roles autorizados**: `admin`, `responsable_laboratorio`, `responsable_rrii`.
- Ranking interactivo de cuentas ordenadas por volumen de muestras recibidas.
- Filtros dinámicos reactivos por rango de fechas (3 meses, 6 meses, 1 año, Todo) y especie de cultivo.
- Detección de **alertas de Churn estacional** (clientes cuyo volumen en el mes seleccionado es 0% respecto a su promedio histórico del mismo mes).
- Opción para filtrar u omitir cuentas de convenio (`id_cliente > 50.000`).

### 2. Cultivos y Capacidad Operativa (HU-02)
- **Roles autorizados**: `admin`, `responsable_laboratorio`, `analista_laboratorio`.
- KPI de muestras acumuladas 100% coincidente con la suma de la distribución por especie.
- Selector alternable entre gráfico de Barras de Pareto y gráfico de Torta/Dona (Top 10 + categoría automatizada `"Otras"`).
- Tendencia temporal cronológica continua (75 meses sin vacíos temporales) para Soja y Trigo.
- **Alertas de capacidad operativa**: Umbrales del 75% (Advertencia) y 90% (Saturación) sobre el volumen crítico.
- **Simulador Interactivo de Capacidad Crítica "What-If"** para evaluar escenarios de sobrecarga en el laboratorio.

### 3. Segmentación RFM y Alerta de Fuga (HU-03)
- **Roles autorizados**: `admin`, `responsable_rrii`, `comercial`.
- Pipeline de clasificación mediante **Score RFM de 3 dígitos (111 al 555)** basado en quintiles de Recencia, Frecuencia y Valor Monetario.
- Exclusión por defecto de cuentas de convenio para análisis individual de clientes.
- Detección dinámica y listado prioritario de gestión comercial para cuentas **En Riesgo** (baja recencia `R <= 2` con alta frecuencia o valor histórico `F >= 4` o `M >= 4`).

---

## 🏛️ Arquitectura del Sistema (Clean Architecture en 5 Capas)

El código fuente respeta estrictamente la separación de responsabilidades:

```text
app-agro-lab/
├── app.py                      # Enrutador principal y validación RBAC
├── .gitignore                  # Reglas de versión y exclusión de secretos
├── config.example.yaml         # Plantilla de configuración y credenciales
├── DATA_DICTIONARY.md          # Diccionario formal de variables
├── DEVELOPER_GUIDE.md          # Guía técnica de arquitectura y estándares
├── README.md                   # Documentación principal del repositorio
├── requirements.txt            # Dependencias del entorno Python
├── data/
│   ├── processed/
│   │   └── cleaned_agro_data.csv  # Dataset procesado y limpio (ETL backup)
│   └── raw/
│       └── BD_lab_28-8-26.xlsx    # Fuente original de datos del laboratorio
├── notebooks/
│   └── 01_eda_crisp_dm.ipynb     # Notebook oficial de EDA y Profiling CRISP-DM
└── src/
    ├── components/             # Componentes visuales (Tema monocromático y Sidebar)
    ├── config/                 # Configuración del entorno y pipeline ETL en caché
    ├── core/                   # Autenticación bcrypt y gestión de sesión
    ├── modules/                # Capa de lógica de negocio pura en Python
    └── views/                  # Controladores de vista en Streamlit
```

---

## 🔑 Matriz de Permisos por Rol (RBAC)

| Rol (`role`) | Descripción | Módulos Autorizados |
|---|---|---|
| `admin` | Administrador General del Sistema | Acceso Total (HU-01, HU-02, HU-03) |
| `responsable_laboratorio` | Responsable del Laboratorio | HU-01 (Clientes) + HU-02 (Cultivos) |
| `analista_laboratorio` | Analista de Laboratorio | HU-02 (Cultivos y Capacidad) |
| `responsable_rrii` | Responsable de Relaciones Institucionales | HU-01 (Clientes) + HU-03 (RFM) |
| `comercial` | Responsable Comercial | HU-03 (Segmentación RFM) |

---

## 🚀 Guía de Inicio Rápido

### Requisitos Previos
- Python 3.10 o superior.

### Pasos para Ejecutar

1. **Clonar el repositorio y situarse en la carpeta raíz**:
   ```bash
   git clone <url-del-repositorio>
   cd app-agro-lab
   ```

2. **Crear y activar el entorno virtual (`.venv`)**:
   ```bash
   python -m venv .venv
   ```
   - **En Windows (PowerShell):**
     ```powershell
     .\.venv\Scripts\activate
     ```
   - **En Linux / macOS:**
     ```bash
     source .venv/bin/activate
     ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar el archivo local de credenciales**:
   ```bash
   cp config.example.yaml config.yaml
   ```
   *(En Windows PowerShell: `Copy-Item config.example.yaml config.yaml`)*

5. **Iniciar la aplicación**:
   ```bash
   streamlit run app.py
   ```

6. **Ingresar al Dashboard**: Abrir en el navegador [http://localhost:8501](http://localhost:8501).
   - Contraseña predeterminada para todos los usuarios demo: `admin123`.

---

## 📄 Documentación Técnica Complementaria

- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)**: Estándares de desarrollo, directiva de cero emojis y guía de prompts para pair programming.
- **[DATA_DICTIONARY.md](DATA_DICTIONARY.md)**: Diccionario oficial de las 15 variables del dataset.