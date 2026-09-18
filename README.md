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
- **Filtro de Estado de Actividad**: `Activos` (cuentas con envíos en la ventana), `Inactivos` (cuentas históricas sin envíos / recencia > 90 días) o `Todos`.
- **Análisis de Tipo de Cliente**: Clasificación de cartera en `Estacional` (monocultivo o concentración en 1-2 meses) y `Mixto` (multicultivo o actividad distribuida en >=3 meses).
- Métricas KPI con tarjeta de **Cliente Líder** identificado por su número de ID y volumen de participación.
- Top 10 interactivo en gráfico de barras horizontales, gráfico de distribución por perfil agronómico y tabla completa con buscador por ID de cliente y recencia en días.

### 2. Demanda, Estacionalidad y Capacidad Operativa (HU-02 / Objetivos 2 y 3)
- **Roles autorizados**: `admin`, `responsable_laboratorio`, `analista_laboratorio`.
- **Distribución por Especie**: Pareto Top 10 + agrupación automatizada `"Otras"` con selector de visualización en Barras o Dona y tabla detallada.
- **Gráfico 1: Capacidad Operativa y Alertas del Laboratorio (Todas las Especies)**: Serie temporal continua del volumen consolidado de todas las especies recibidas, evaluado con **umbrales operativos fijos: 142 muestras/mes (Alerta Operativa - preventivo)** y **191 muestras/mes (Cuello de Botella - crítico)**. Incluye tarjetas de estado y tabla de auditoría detallada de meses históricos en sobrecarga.
- **Gráfico 2: Patrón de Estacionalidad Agronómica (Trigo y Soja)**: Curvas continuas sin líneas de alerta para los dos cultivos principales (representan el 72.0% del volumen total). Permite visualizar la complementariedad estacional de zafras (fina vs. gruesa), picos y baches de demanda.
- **Nota sobre Ensayos Analíticos**: Se desestimó el desglose por tipo de ensayo debido a que la variable `tipo_analisis` en la base histórica no desagrega determinaciones analíticas unitarias (el 40.8% repite la especie y el resto nombres de convenios comerciales).

### 3. Segmentación RFM y Alerta de Fuga de Clientes (HU-03 / Objetivo 4)
- **Roles autorizados**: `admin`, `responsable_rrii`, `comercial`.
- Pipeline de clasificación mediante **Scoring RFM de 3 dígitos (111 al 555)** basado en quintiles de Recencia, Frecuencia y Valor Monetario sobre la campaña **Ciclo 25/26** (o períodos configurables), evaluando a toda la cartera de clientes sin exclusiones artificiales de ID.
- **5 Categorías Oficiales de Negocio**:
  1. **Campeones** (`#10B981`): Activo más valioso del laboratorio ($R \ge 4, F \ge 4, M \ge 4$).
  2. **Fieles / Alto Valor** (`#2563EB`): Comportamiento sostenido, candidatos para upselling ($R \ge 3$ y $F/M \ge 3$).
  3. **Potenciales** (`#F59E0B`): Clientes recientes con bajo volumen acumulado ($R \ge 3, F \le 2$).
  4. **En Riesgo** (`#DC2626`): Cuentas clave de alta facturación histórica cuya recencia cayó ($R \le 2, F/M \ge 4$).
  5. **Perdidos** (`#64748B`): Inactivos de menor score en los tres indicadores.
- **Distribución de Cartera por Fracciones**: Visualización comparativa (Barras / Dona) con alternancia entre *Facturación Acumulada ($)* y *Cantidad de Clientes*, más Matriz RFM 2D (Recencia vs. Frecuencia).
- **Listado de Contactos Urgentes (Cuentas en Riesgo)**: Tabla priorizada por facturación con nivel de exposición y acciones sugeridas para recupero comercial inmediato o alertas automáticas por correo.
- **Auditoría de Cartera Completa**: Desglose con filtro multi-categoría y buscador por ID de cliente (sin columna redundante Razón Social).

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