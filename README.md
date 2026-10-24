# Cost estimator: baseline, economics and decision

The delivered library implements the deterministic COCOMO II.2000
Post-Architecture baseline (M1), agent parameter selection (M2), adoption
costs (M3), economic evaluation (M4), scenarios/sensitivity/decision (M5),
and recorded actual-cost comparison (M6–M7). It follows
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
| Nominal constants and error transport | M8 reports |
| F1–F8 and nominal verification | Pipeline and CLI |
| M2 scenario values and literature warnings | Streamlit interface |
| F17–F27/F31 adoption and economic indicators | Complete empirical-case validation |
| M5 scenarios, sensitivity and verdict | Externally collected literature/case inputs |
| M6–M7 actual cost, errors and stability | |
| Numerical, architecture and isolated-wheel tests | |

Full agent-example reproduction and real-case validation remain pending
external literature-derived inputs. No parameters are fitted to case hours
or reverse-engineered from the example's rounded outputs.

Implementation evidence and decisions: [core task log](odd/tasks/cocomo-core.md).
Economics delivery: [agent economics task log](odd/tasks/agent-economics.md).
Current M5 delivery: [scenarios and sensitivity task log](odd/tasks/scenarios-sensitivity.md).

## Compare a synthetic recorded cost

Continue the earlier examples with this **entirely synthetic case and declared
agent configuration**, not a reconstruction of the original project. No upstream
parameters are fitted to its budget, hours or cash payments.

```python
from dataclasses import replace

from modelo.contraste import contrastar
from modelo.costo_real import calcular_costo_real
from modelo.tipos import CasoValidacion, CostoReal, ParametrosIA, Rubro, Sprint, Trio

synthetic_project = replace(
    p, nombre="Synthetic actual-cost example", size_ksloc=1,
    c_pm=1520, T_meses=2, n_u=2,
)
synthetic_parameters = ParametrosIA(*(
    Trio(value, value, value, "Supuesto declarado", (), "Synthetic example only")
    for value in (0.3, 0, 0, 0, 0, 0, 0, 0, 0)
))
synthetic_base = estimar_base(synthetic_project, c)
synthetic_scenarios = correr_escenarios(synthetic_project, c, synthetic_parameters)
synthetic_case = CasoValidacion(
    rubros=(Rubro("Synthetic historical budget", None, 1300, True),),
    sprints=(
        Sprint(1, None, None, 100, None, 20, 5, 10, 15, True),
        Sprint(2, None, None, 50, None, 10, 0, 0, 0, True),
    ),
)
actual = calcular_costo_real(synthetic_case, synthetic_base.t_h)
comparison = contrastar(
    C_trad=synthetic_base.C_trad,
    C_ia=synthetic_scenarios[1].resultado.C_ia,
    cr=actual,
    veredicto_por_escenarios=synthetic_scenarios,
    verificacion_ok=verificar_cocomo(c),
)
assert actual == CostoReal(1300, 1560, 150, 60, None, 2)
assert (comparison.cumple_exactitud, comparison.decision_estable,
        comparison.verificacion_cocomo_ok) == (False, True, True)
print(f"Budget={actual.C_presup:.2f}, actual={actual.C_real:.2f}, "
      f"deviation={comparison.desviacion_presup:.2%}")
```

Expected display:
`Budget=1300.00, actual=1560.00, deviation=20.00%`.

| Result | Rule |
|---|---|
| `C_presup` | Sum included `Rubro.costo_usd`; do not rebuild historical cash from budget hours. |
| `C_real` | All programmer hours in `hubo_programacion` sprints × `t_h`, plus their four IA cash categories once. No f weighting, role inference or task allocation. |
| `horas_totales`, `costo_ia_real`, `n_sprints` | Raw included hours, IA cash total and programming-sprint count. Training/integration cash means third-party payments, not duplicated team labor. |
| `H_real_4` | Sum recorded included activity hours; any included `None` makes it `None`. Zero is recorded; excluded missing rows do not affect completeness. |
| `err_estimacion_ia`, `err_cocomo_vs_presup` | Absolute errors relative to actual cost and historical budget, respectively. |
| `desviacion_presup` | Signed `(C_real - C_presup) / C_presup`; negative means under budget. |

Actual cost and budget must be positive before calling M7; M0 will own invalid
input validation and business error codes. Ratios use exact decimal-rational
arithmetic before conversion to float. `cumple_exactitud` includes exactly 25%
error, without epsilon or money rounding (including 1000.1 versus 750.075).
`veredicto_por_escenarios` is the canonical M5 `tuple[Escenario, ...]`, not a
verdict string or a list of savings. `decision_estable` requires exactly three
strictly positive or three strictly negative net savings; any zero, mixed signs
or insufficient evidence is not stable. This does not change M5's equilibrium
verdict `no concluyente`. `verificacion_cocomo_ok` transports `verificacion_ok`
independently and never gates the other flags.

M6/M7 return existing frozen contracts without files, output or input mutation.
Delivery evidence: [actual cost and comparison task log](odd/tasks/actual-cost-contrast.md).
