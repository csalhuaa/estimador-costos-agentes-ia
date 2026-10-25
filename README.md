# Estimador Económico de Adopción de Agentes IA

Herramienta determinista para la evaluación económica, sensibilidad y viabilidad en la adopción de agentes de inteligencia artificial en proyectos de software.

El sistema calcula la línea base del proyecto mediante el modelo COCOMO II.2000 (Post-Architecture) y proyecta el impacto financiero mediante las formulaciones analíticas de adopción (F1 a F36). Integra una biblioteca de cálculo puro desacoplada, una interfaz de línea de comandos para automatización y un panel analítico interactivo en Streamlit con soporte para temas claro y oscuro.

---

## Arquitectura del Proyecto

El repositorio está organizado siguiendo principios de arquitectura limpia, asegurando que las reglas matemáticas del negocio no dependan de bibliotecas de interfaz de usuario ni de infraestructura de persistencia:

```
estimador_costos/
├── app.py                     # Punto de entrada de la aplicación web Streamlit
├── cli.py                     # Punto de entrada de la interfaz de línea de comandos (CLI)
├── pyproject.toml             # Metadatos del paquete y configuración de herramientas
├── requirements.txt           # Dependencias de producción y pruebas
├── .streamlit/
│   └── config.toml            # Configuración de tema (colores, fuentes y servidor)
├── modelo/                    # Núcleo analítico puro (M0 a M8)
│   ├── cocomo.py              # Línea base COCOMO II (M1)
│   ├── parametros_ia.py       # Rangos de parámetros y contraste de literatura (M2)
│   ├── adopcion.py            # Costos directos y de licenciamiento (M3)
│   ├── economia.py            # Indicadores financieros: ahorro neto, ROI, RBC (M4)
│   ├── escenarios.py          # Sensibilidad, tornado y veredicto de decisión (M5)
│   ├── costo_real.py          # Consolidación de costos reales ejecutados (M6)
│   ├── contraste.py           # Contraste empírico entre estimado y ejecutado (M7)
│   ├── carga.py               # Adaptador de lectura y validación de Excel (M0)
│   ├── reportes.py            # Generación de informes en Excel y gráficos estáticos (M8)
│   ├── pipeline.py            # Orquestador del flujo analítico integral
│   ├── constantes.py          # Constantes y ponderaciones nominales COCOMO II
│   ├── errores.py             # Definición de excepciones y códigos de error (E01-E11)
│   └── tipos.py               # Contratos de datos inmutables (dataclasses congeladas)
├── interfaz/                  # Capa de presentación para Streamlit
│   ├── tema.py                # Inyección de estilos CSS y tokens de diseño
│   ├── formato.py             # Formateo monetario, porcentual y numérico
│   ├── estado.py              # Gestión y persistencia del estado de sesión
│   ├── graficos.py            # Visualizaciones interactivas con Altair / Vega-Lite
│   ├── componentes.py         # Componentes visuales reutilizables
│   ├── vistas.py              # Vistas de resumen, escenarios, sensibilidad y validación
│   └── iconos.py              # Definiciones SVG vectoriales optimizadas
├── datos/                     # Libros de trabajo de ejemplo y fixtures dorados
└── pruebas/                   # Suite de pruebas automatizadas (unitarias, integración y UI)
```

---

## Requisitos del Sistema

- **Python**: Versión 3.11 o superior.
- **Sistemas Operativos Soportados**: Linux, macOS y Windows.

---

## Instalación

1. **Clonar el repositorio:**

   ```bash
   git clone https://github.com/csalhuaa/estimador-costos-agentes-ia.git
   cd estimador-costos-agentes-ia
   ```

2. **Crear y activar un entorno virtual:**

   En Linux o macOS:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   En Windows (PowerShell):
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. **Instalar dependencias:**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## Modos de Uso

### 1. Panel Web Interactivo (Streamlit)

Permite cargar libros de trabajo Excel, inspeccionar variables del proyecto, explorar escenarios (pesimista, esperado, optimista), realizar análisis de sensibilidad tornado y descargar reportes consolidados:

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en `http://localhost:8501`.

### 2. Interfaz de Línea de Comandos (CLI)

Diseñada para ejecución por lotes o integración continua (CI/CD):

```bash
python cli.py --entrada ruta/al/archivo.xlsx --salida reporte_calculado.xlsx
```

**Códigos de salida del proceso:**
- `0`: Ejecución exitosa y veredicto de adopción favorable (`Adoptar`).
- `1`: Ejecución exitosa pero veredicto desfavorable o condicionado (`Rechazar` o `Monitorear`).
- `2`: Error de validación en los datos de entrada (violación de reglas E01 a E11).

### 3. Uso Programático como Biblioteca Python

El núcleo analítico puede consumirse directamente desde código Python de forma completamente desacoplada y en memoria:

```python
from modelo.cocomo import estimar_base, verificar_cocomo
from modelo.constantes import NOMBRES_EM, constantes_predeterminadas
from modelo.tipos import Proyecto

c = constantes_predeterminadas()
p = Proyecto(
    nombre="32 KSLOC reference",
    moneda="USD",
    size_ksloc=32,
    sf=dict(c.sf_nominal),
    em=dict.fromkeys(NOMBRES_EM, c.em_nominal),
    sced_em=1,
    sced_pct=100,
    c_pm=1000,
    f=0.59,
    T_meses=None,
    n_u=10,
)
base = estimar_base(p, c)
print(f"PM={base.PM:.4f}, TDEV={base.TDEV:.4f}, USD={base.C_trad:.2f}")
assert verificar_cocomo(c)
```

Salida esperada por consola:
`PM=132.9109, TDEV=17.3712, USD=132910.95`

---

## Estructura del Archivo Excel de Entrada

El libro Excel suministrado (`.xlsx`) debe contener las siguientes hojas con su respectiva estructura de celdas:

| Hoja | Descripción | Reglas Clave |
|---|---|---|
| `proyecto` | Parámetros COCOMO II (KSLOC, Scale Factors, Cost Drivers, costo persona-mes, fracción automatizable `f`). | Requiere `moneda == "USD"`, KSLOC > 0, `f` entre 0 y 1. |
| `parametros_ia` | Rangos (mínimo, esperado, máximo) para los 9 factores de impacto de la IA (reducción `r`, revisión, retrabajo, costos API, licencias, capacitación, integración, etc.). | Validación de consistencia: `min <= esp <= max`. |
| `estudios` | Catálogo de literatura empírica utilizada para contrastar el parámetro de reducción de esfuerzo `r`. | Normalización de aceptación (`Si` / `No`) y rangos válidos. |
| `caso_real` *(opcional)* | Registros empíricos de ejecución por sprints y rubros para proyectos ya implementados. | Consistencia de balance y cálculo de variaciones reales. |

Si el archivo incumple alguna restricción, el validador emite excepciones estructuradas del tipo `ErrorDeEntrada` identificando la hoja, celda, valor observado y regla infringida (E01 a E11).

---

## Verificación y Calidad de Código

El repositorio cuenta con una suite integral de 264 pruebas automatizadas que cubren verificación aritmética contra benchmarks publicados, determinismo, inmutabilidad y pruebas de interfaz de usuario:

```bash
python -m pytest
```

Para ejecutar una verificación concisa:

```bash
python -m pytest -q
```

---

## Despliegue en Streamlit Community Cloud

El proyecto está preparado para desplegarse de manera directa en Streamlit Community Cloud:

1. Iniciar sesión en [share.streamlit.io](https://share.streamlit.io/) vinculando la cuenta de GitHub correspondiente.
2. Hacer clic en **Create app** > **Deploy a public app from GitHub**.
3. Configurar los parámetros de despliegue:
   - **Repository**: `csalhuaa/estimador-costos-agentes-ia`
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. Hacer clic en **Deploy**.

La plataforma instalará de forma automática las dependencias declaradas en `requirements.txt` y levantará el servicio en una URL pública permanente con certificado SSL gestionado.
