# Cost estimator: baseline, economics and decision

The delivered library implements the deterministic COCOMO II.2000
Post-Architecture baseline (M1), agent parameter selection (M2), adoption
costs (M3), economic evaluation (M4), and scenarios/sensitivity/decision (M5). It follows
`IMPLEMENTACION_MODELO.docx` sections 5–9; the original documents and input
workbook remain unchanged in the parent directory.

## Run the tests

Use Python 3.11 or newer. From this directory, with your Python environment
active:

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
```

The core itself has no third-party runtime dependencies. `requirements.txt`
pins the tested pytest and wheel-build backend versions. Excel, chart and UI dependencies will be
introduced with their respective modules, not installed by importing M1.

## Calculate a reference example

The following is a published reference fixture, **not real case-project data**:

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

Expected display: `PM=132.9109, TDEV=17.3712, USD=132910.95`.
Rounding belongs to presentation only; the returned values retain precision.

## Evaluate an agent configuration

Continue the previous example with **illustrative parameters, not values
extracted from primary studies**:

```python
from modelo.adopcion import costos_adopcion
from modelo.economia import evaluar
from modelo.tipos import ValoresIA

v = ValoresIA(
    r=0.3, rho_rev=0.1, rho_retr=0.05, c_api_h=0.2,
    delta=0.02, h_def=2, p_lic=20, h_cap=8, h_int=4,
)
costs = costos_adopcion(base, v, p.n_u)
economics = evaluar(base, p.f, v, costs)
print(f"Net savings (USD): {economics.ahorro_neto:.2f}")
```

For complete min/expected/max ranges, use these M2 functions:

| API | Behavior |
|---|---|
| `valores(parametros, "pesimista")` | Minimum r, maximum costs |
| `valores(parametros, "esperado")` | Expected values for all nine parameters |
| `valores(parametros, "optimista")` | Maximum r, minimum costs |
| `contrastar_r_con_estudios(parametros, estudios)` | Eligible-study min/median/max comparison, warnings A02/A03 |

Both functions live in `modelo.parametros_ia`; inputs use the existing
`ParametrosIA`, `Trio` and `Estudio` contracts. Study acceptance must already
be normalized to `Si`. A02 requires a difference strictly greater than 0.005;
A03 counts only accepted studies with convertible r, including zero.
Cross-checks never replace the supplied ranges. Warnings are sheet-level
(empty `celda`) because this API does not receive source-cell coordinates.

Zero adoption cost gives `rbc=None` and `recuperacion_meses=None`, not
infinity. A positive cost with no gross savings gives RBC=0 and no recovery.
An unattainable break-even above 1 is reported unchanged. Full scenario
execution, sensitivity and the final verdict belong to M5, not to M2.

## Run scenarios and sensitivity

Continue the examples above with **synthetic declared ranges**, not
literature-derived or real-case inputs:

```python
from modelo.escenarios import correr_escenarios, decidir, sensibilidad
from modelo.tipos import ParametrosIA, Trio

def illustrative_range(minimum, expected, maximum):
    return Trio(
        minimum, expected, maximum, "Supuesto declarado", (),
        "Illustrative example only; replace with externally sourced ranges.",
    )

parameters = ParametrosIA(
    r=illustrative_range(0.1, 0.3, 0.5),
    rho_rev=illustrative_range(0.05, 0.1, 0.2),
    rho_retr=illustrative_range(0.02, 0.05, 0.1),
    c_api_h=illustrative_range(0.1, 0.2, 0.3),
    delta=illustrative_range(0.01, 0.02, 0.04),
    h_def=illustrative_range(1, 2, 3),
    p_lic=illustrative_range(10, 20, 30),
    h_cap=illustrative_range(4, 8, 16),
    h_int=illustrative_range(2, 4, 8),
)
scenarios = correr_escenarios(p, c, parameters)
impacts = sensibilidad(p, c, parameters, x_pct=20)
print(decidir(scenarios))
print(impacts[0].parametro)
```

Scenario order is pessimistic, expected, optimistic; all share one project
baseline and horizon. Sensitivity changes each of thirteen inputs separately
around its expected value, recomputes coupled costs, and returns signed
net-savings differences. Rows are sorted by the larger absolute effect, not
by the signed maximum. A supplied project horizon remains supplied.

The explicit clamps are r at 1 and agent costs at 0. Other transformed
project fields are not clipped; user counts intentionally remain fractional.
Tests cover default 20, CLI example 30, and future UI endpoints 5/50. The
specification assigns 5–50 to the UI; this module does not add a separate
core percentage-domain policy or business exceptions.

| Condition | Verdict |
|---|---|
| Pessimistic net savings > 0 | `conviene` |
| Otherwise, optimistic net savings < 0 | `no conviene` |
| Otherwise, including zero boundaries | `no concluyente` |

The expected scenario alone never decides. M5 returns the existing tuples
and verdict; the future pipeline will assemble the `Decision` contract.

## Boundaries and units

- M1 receives already validated data. The Excel reader and its aggregated
  E01–E13 checks belong to M0, which is **not delivered yet**.
- Required input conventions include all five SF and sixteen EM, positive
  size/rates/multipliers, `0 < f < 1`, and a positive supplied duration.
- Size is logical KSLOC, effort is person-months, duration is months,
  `c_pm` is USD/person-month, and the conversion is 152 hours/person-month.
- `PM_ns` excludes SCED_EM; `PM` includes it. TDEV uses `PM_ns` and SCED_pct.
  A supplied `T_meses` changes T, not the calculated TDEV.
- `H_trad` is the reducible share `f × PM × 152`, not all project hours.
- Frozen dataclasses prevent reassignment of fields, not deep mutation of
  nested dictionaries. Calculations do not modify their arguments.
- Fractional user counts are allowed internally during sensitivity; M0 will
  enforce integer counts on original Excel inputs.

## Delivered and next

| Delivered | Deferred |
|---|---|
| Specified typed data contracts | M0 Excel import and validation |
| Nominal constants and error transport | M6–M7 actual-cost comparison |
| F1–F8 and nominal verification | M8 reports |
| M2 scenario values and literature warnings | Pipeline and CLI |
| F17–F27/F31 adoption and economic indicators | Streamlit interface |
| M5 scenarios, sensitivity and verdict | Complete empirical-case validation |
| Numerical, architecture and isolated-wheel tests | Externally collected literature/case inputs |

Full agent-example reproduction and real-case validation remain pending
external literature-derived inputs. No parameters are fitted to case hours
or reverse-engineered from the example's rounded outputs.

Implementation evidence and decisions: [core task log](odd/tasks/cocomo-core.md).
Economics delivery: [agent economics task log](odd/tasks/agent-economics.md).
Current M5 delivery: [scenarios and sensitivity task log](odd/tasks/scenarios-sensitivity.md).
