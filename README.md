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
│   ├── reporte.py             # Generación de informes en Excel y gráficos estáticos (M8)
│   ├── pipeline.py            # Orquestador del flujo analítico integral
│   ├── constantes.py          # Constantes y ponderaciones nominales COCOMO II
│   ├── errores.py             # Definición de excepciones y códigos de error (E01-E13)
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

El panel conserva un resumen ejecutivo y cinco pestañas: Escenarios, Sensibilidad, Validación, Evidencia y Exportar. La RBC se presenta con cuatro decimales. Calcular reutiliza resultados válidos si el archivo y la sensibilidad no cambiaron; quitar el archivo elimina resultados, errores y descargas. Volver a subir el mismo archivo permite calcular de nuevo. Los errores inesperados se registran en el servidor, sin exponer detalles técnicos en pantalla.

La recomendación es binaria: `conviene` si el ahorro neto efectivo del escenario esperado es positivo; en otro caso, `no conviene`. Solo para clasificar, un ahorro con valor absoluto menor a 0,005 USD se trata como cero; los importes originales no cambian. Exactamente ±0,005 USD no se ajustan.

La robustez se muestra por separado, sin un tercer color de decisión: `robusta` si los tres escenarios coinciden en la recomendación, o `sensible a los parámetros` si difieren. Ceros y negativos coinciden en rechazar; tres ceros son un rechazo robusto. Los reportes JSON conservan `robusta` como booleano nativo y todos los formatos incluyen `etiqueta_robustez` junto al veredicto con procedencia F30.

### 2. Interfaz de Línea de Comandos (CLI)

Diseñada para ejecución por lotes o integración continua (CI/CD):

```bash
python cli.py --entradas ruta/al/archivo.xlsx --salidas carpeta_nueva_reportes
# Sin destino explícito: genera los cuatro archivos en ./salidas
python cli.py ruta/al/archivo.xlsx --x 30
# Verificación nominal independiente, sin libro ni reportes
python cli.py --verificar
```

**Códigos de salida del proceso:**
- `0`: Ejecución válida, tanto para `conviene` como para `no conviene`; muestra también la robustez.
- `1`: Error de validación en los datos de entrada.
- `2`: Error de uso o fallo inesperado, incluidos destinos de reporte ya existentes.

| Opción | Alias | Regla |
|---|---|---|
| Entrada | `--entrada`, `--entradas`, `-e` o ruta posicional | Use una sola forma; no combine ruta posicional y opción, aunque sean iguales. |
| Destino | `--salida`, `--salidas`, `-s`, `-o` | Directorio, no archivo; por defecto `salidas` en el directorio de ejecución. |
| Sensibilidad | `--x`, `--x_pct`, `-x` | Número finito entre 5 y 50 inclusive; por defecto 20. |
| Verificación | `--verificar` | Imprime `ok` (salida 0) o `revisar` (salida 2); no admite entrada, destino ni sensibilidad explícitos. |

No se aceptan abreviaciones implícitas. Los cuatro archivos son `reporte.xlsx`, `reporte.md`, `resultados.json` y `sensibilidad.png`. La exportación rechaza destinos ya existentes sin sobrescribirlos; para repetir una ejecución use un directorio nuevo. Un error de exportación devuelve 2, aunque la recomendación ya se haya mostrado.

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

La API M5 devuelve `veredicto, robusta = decidir(escenarios)` y requiere exactamente un escenario de cada nombre (`pesimista`, `esperado`, `optimista`); nombres repetidos, ausentes o desconocidos causan `ValueError`. El constructor obligatorio es `Decision(escenarios, sensibilidad, x_pct, veredicto, robusta)`. M7 recibe `contrastar(C_trad, C_ia, cr, robusta, verificacion_ok)` y conserva esa misma robustez en `decision_estable`, sin recalcularla ni mezclarla con exactitud o verificación COCOMO.

El ejemplo sintético sin modificar conserva un ahorro neto esperado de +7400,11 USD: `("conviene", False)`. La referencia publicada de tres ahorros −39537,45 / −3024,73 / 19969,92 corresponde a una prueba de decisión: `("no conviene", False)`, no a una reconstrucción de sus entradas originales incompletas.

---

## Estructura del Archivo Excel de Entrada

El libro Excel suministrado (`.xlsx`) debe contener las siguientes hojas con su respectiva estructura de celdas:

| Hoja | Descripción | Reglas Clave |
|---|---|---|
| `LEEME` | Instrucciones del libro. | Hoja requerida. |
| `proyecto` | Parámetros COCOMO II (KSLOC, Scale Factors, Cost Drivers, costo persona-mes, fracción automatizable `f`). | Requiere `moneda == "USD"`, KSLOC > 0, `f` entre 0 y 1. |
| `parametros_ia` | Rangos (mínimo, esperado, máximo) para los 9 factores de impacto de la IA (reducción `r`, revisión, retrabajo, costos API, licencias, capacitación, integración, etc.). | Validación de consistencia: `min <= esp <= max`. |
| `estudios` | Catálogo de literatura empírica utilizada para contrastar el parámetro de reducción de esfuerzo `r`. | Normalización de aceptación (`Si` / `No`) y rangos válidos. |
| `presupuesto_inicial` | Rubros del presupuesto histórico y alcance. | Datos del caso opcionales; importes positivos para comparar. |
| `costo_real_sprint` | Horas y costos de IA registrados por sprint. | Datos del caso opcionales; debe ser consistente con presupuesto y alcance. |
| `constantes` | Constantes COCOMO y valores nominales. | Valores ausentes usan predeterminados declarados con aviso A06. |
| `verificacion` | Referencia nominal del libro. | Hoja requerida; la verificación independiente usa las constantes nominales del modelo. |
| `rangos` | Referencias de rangos del libro. | Hoja requerida. |

Las nueve hojas deben existir. Si ambas hojas de datos del caso están vacías, el cálculo es predictivo; si solo una tiene datos sustantivos, se informa E08. Los símbolos de proyecto, agentes y constantes se buscan hasta el final usado de sus hojas, sin cortar por filas vacías; se conservan coordenadas reales y se rechazan duplicados.

Si el archivo incumple alguna restricción, el validador agrega excepciones estructuradas del tipo `ErrorDeEntrada` identificando la hoja, celda, valor observado y regla infringida (E01 a E13), sin escribir en el libro de entrada.

---

## Verificación y Calidad de Código

El repositorio cuenta con pruebas automatizadas de verificación aritmética contra referencias publicadas, determinismo, inmutabilidad, CLI, adaptadores e interfaz de usuario. Los datos de prueba inválidos se generan localmente: no requieren documentos externos al repositorio.

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
