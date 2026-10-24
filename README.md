# Cost estimator: COCOMO II core

The first delivery implements the deterministic COCOMO II.2000
Post-Architecture baseline (M1). It follows `IMPLEMENTACION_MODELO.docx`
sections 5–9; the original documents and input workbook remain unchanged
in the parent directory.

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
| Nominal constants and error transport | M2–M5 agent economics and sensitivity |
| F1–F8 and nominal verification | M6–M7 actual-cost comparison |
| Numerical, architecture and isolated-wheel tests | Reports, pipeline, CLI and Streamlit |

Full agent-example reproduction and real-case validation remain pending
external literature-derived inputs. No parameters are fitted to case hours
or reverse-engineered from the example's rounded outputs.

Implementation evidence and decisions: [core task log](odd/tasks/cocomo-core.md).
