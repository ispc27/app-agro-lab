# AgroLab — Plataforma de Análisis y Analítica Agronómica

Plataforma corporativa e interactiva para el análisis de datos agronómicos, monitoreo de capacidad operativa de laboratorios, análisis de estacionalidad y segmentación comercial de cuentas basada en la metodología **CRISP-DM** y una **Arquitectura Limpia en 5 Capas**.

---

## Módulos Analíticos e Historias de Usuario

La plataforma se estructura en tres áreas analíticas protegidas por **Control de Acceso Basado en Roles (RBAC)**:

### 1. Identificación de Clientes Frecuentes (HU-01 / Objetivo 1)
- **Roles autorizados**: `admin`, `responsable_laboratorio`, `responsable_rrii`.
- Ranking interactivo de clientes ordenados descendentemente por volumen de muestras ingresadas en el período.
- Filtros dinámicos superiores: Presets rápidos de fechas (*Todo el Histórico*, *Ciclo 25/26*, *Último Año*, *Últimos 6 Meses*, *Personalizado*) con selectores de fecha `Desde` / `Hasta` (`DD/MM/YYYY`).
- **Filtro Multi-Especie** (`st.multiselect`): Permite filtrar por una, varias o todas las especies simultáneamente.
- **Filtro de Estado de Cuenta**: `Activos` (cuentas con envíos en la ventana), `Inactivos` (cuentas históricas sin envíos) o `Todos`.
- Opción para excluir cuentas de convenio institucional (`id_cliente > 50.000`).
- Top 10 interactivo en gráfico de barras horizontales y tabla completa con buscador en vivo por ID o Razón Social y formateo Styler.

### 2. Demanda, Estacionalidad y Capacidad Operativa (HU-02 / Objetivos 2 y 3)
- **Roles autorizados**: `admin`, `responsable_laboratorio`, `analista_laboratorio`.
- **Distribución por Especie**: Pareto Top 10 + agrupación automatizada `"Otras"` con selector de visualización en Barras o Dona y tabla detallada.
- **Gráfico Unificado de Evolución Mensual**: Serie temporal continua sin saltos temporales, con **Soja y Trigo anclados y preseleccionados por defecto**, y selector multi-cultivo para contrastar cualquier combinación de especies.
- **Superposición de Total Consolidado**: Opción para visualizar simultáneamente la curva agregada de todo el laboratorio.
- **Alertas de Capacidad Operativa**: Umbrales del 75% (Advertencia) y 90% (Saturación) sobre el volumen crítico mensual.
- **Simulador Interactivo "What-If"**: Permite ajustar la capacidad crítica mensual de referencia para evaluar escenarios de sobrecarga operativa.
- **Intervalos Críticos de Demanda**: Desglose analítico de los tipos de ensayo más solicitados (ej. Poder Germinativo, Pureza) para optimizar dotación de personal, insumos y turnos de guardia.

### 3. Segmentación RFM y Alerta de Fuga de Clientes (HU-03 / Objetivo 4)
- **Roles autorizados**: `admin`, `responsable_rrii`, `comercial`.
- Pipeline de clasificación mediante **Scoring RFM de 3 dígitos (111 al 555)** basado en quintiles de Recencia, Frecuencia y Valor Monetario sobre la campaña **Ciclo 25/26** (o períodos configurables).
- **Banner y Listado de Alerta de Churn / Riesgo Comercial**: Detección automática y priorización de cuentas clave con alta facturación/frecuencia histórica pero inactividad prolongada (`R <= 2` con `F >= 4` o `M >= 4`).
- **Matriz Térmica 5x5 RF (Recencia vs. Frecuencia)**: Mapa de calor en escala monocromática `Greys` con selector de métrica (Cantidad de Clientes / Facturación Acumulada $).
- Matriz Estratégica 2D y gráfico Donut de facturación por segmento (*Clientes Clave*, *Clientes Fieles*, *Nuevos/Prometedores*, *En Riesgo*).
- Desglose de cartera completa con filtro multi-segmento y buscador por ID / Razón Social.

---

## Arquitectura del Sistema (Clean Architecture en 5 Capas)

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

## Matriz de Permisos por Rol (RBAC)

| Rol (`role`) | Descripción | Módulos Autorizados |
|---|---|---|
| `admin` | Administrador General del Sistema | Acceso Total (HU-01, HU-02, HU-03) |
| `responsable_laboratorio` | Responsable del Laboratorio | HU-01 (Clientes) + HU-02 (Cultivos y Capacidad) |
| `analista_laboratorio` | Analista de Laboratorio | HU-02 (Cultivos y Capacidad) |
| `responsable_rrii` | Responsable de Relaciones Institucionales | HU-01 (Clientes) + HU-03 (Segmentación RFM) |
| `comercial` | Responsable Comercial | HU-03 (Segmentación RFM y Alerta de Fuga) |

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

6. **Ejecutar Pruebas Automatizadas**:
   ```bash
   pytest -v
   ```

7. **Ingresar al Dashboard**: Abrir en el navegador [http://localhost:8501](http://localhost:8501).
   - Contraseña predeterminada para todos los usuarios demo: `admin123`.

---

## 📄 Documentación Técnica Complementaria

- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)**: Estándares de desarrollo, directiva de cero emojis y guía de prompts para pair programming.
- **[DATA_DICTIONARY.md](DATA_DICTIONARY.md)**: Diccionario oficial de las 15 variables del dataset.