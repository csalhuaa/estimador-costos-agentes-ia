"""M0 validates public workbook inputs without ever saving the source."""

from datetime import date
from hashlib import sha256

import pytest

from modelo.carga import cargar_entradas
from modelo.errores import ErrorDeEntrada
from pruebas.fixtures_excel import libro_sintetico


def load(tmp_path, mutate=lambda w: None, *, caso=True):
    w = libro_sintetico(caso=caso)
    mutate(w)
    path = tmp_path / "synthetic.xlsx"
    w.save(path)
    w.close()
    before = sha256(path.read_bytes()).hexdigest()
    try:
        return cargar_entradas(path)
    finally:
        assert sha256(path.read_bytes()).hexdigest() == before


def test_valid_preserves_decimals_dates_and_all_supplemental_cells(tmp_path):
    e = load(tmp_path)
    assert e.proyecto.f == 0.59
    assert e.proyecto.T_meses is None
    assert e.proyecto.n_u == 10
    assert not e.estudios
    assert e.caso.sprints[0].inicio == date(2026, 1, 2)
    assert e.caso.sprints[0].fin == date(2026, 1, 16)
    assert e.caso.rubros[0].en_alcance
    cells = {(x.hoja, x.celda): x.valor for x in e.fuente.celdas}
    assert cells["presupuesto_inicial", "F13"] == "Synthetic note"
    assert cells["costo_real_sprint", "O6"] == "Synthetic observation"
    assert e.fuente.nombre == "synthetic.xlsx"
    assert len(e.fuente.sha256) == 64
    assert {x.codigo for x in e.avisos} == {"A04", "A05"}


def test_scaffold_and_default_metadata_are_not_optional_records(tmp_path):
    assert load(tmp_path, caso=False).caso is None


@pytest.mark.parametrize(
    "code,sheet,cell,value",
    [
        ("E01", "proyecto", "C31", None),
        ("E02", "proyecto", "C7", "many"),
        ("E03", "proyecto", "C34", 1.5),
        ("E04", "parametros_ia", "D6", 0.9),
        ("E05", "parametros_ia", "I6", None),
        ("E06", "proyecto", "C6", "PEN"),
        ("E07", "proyecto", "B7", "unknown"),
        ("E09", "costo_real_sprint", "P6", "No"),
        ("E10", "costo_real_sprint", "E6", 19801),
        ("E11", "costo_real_sprint", "P6", "perhaps"),
        ("E13", "costo_real_sprint", "C6", "2020-01-01"),
    ],
)
def test_each_field_error_is_aggregated_and_source_unchanged(
    tmp_path, code, sheet, cell, value
):
    with pytest.raises(ErrorDeEntrada) as caught:
        load(tmp_path, lambda w: setattr(w[sheet][cell], "value", value))
    assert code in {p.codigo for p in caught.value.problemas}
    assert "(valor:" in str(caught.value)
    assert all(p.hoja and p.mensaje.endswith(".") for p in caught.value.problemas)


def test_e08_one_substantive_dataset(tmp_path):
    def mutate(w):
        for row in w["presupuesto_inicial"].iter_rows(min_row=13, max_row=24):
            for cell in row:
                cell.value = None

    with pytest.raises(ErrorDeEntrada) as caught:
        load(tmp_path, mutate)
    assert "E08" in {p.codigo for p in caught.value.problemas}


def test_e12_extension_and_corrupt_workbook(tmp_path):
    for name in ("bad.xls", "bad.xlsx"):
        path = tmp_path / name
        path.write_bytes(b"not a workbook")
        with pytest.raises(ErrorDeEntrada) as caught:
            cargar_entradas(path)
        assert [p.codigo for p in caught.value.problemas] == ["E12"]
        assert path.read_bytes() == b"not a workbook"


def test_missing_sheet_and_multiple_independent_errors(tmp_path):
    def mutate(w):
        del w["rangos"]
        w["proyecto"]["C31"] = None
        w["proyecto"]["C32"] = 2

    with pytest.raises(ErrorDeEntrada) as caught:
        load(tmp_path, mutate)
    assert {"E01", "E03", "E07"} <= {p.codigo for p in caught.value.problemas}


def test_defaults_and_runtime_warning_origins_are_honest(tmp_path):
    def mutate(w):
        w["constantes"]["B5"] = None
        w["proyecto"]["C32"] = 0.5
        w["presupuesto_inicial"]["B8"] = "Sí"

    e = load(tmp_path, mutate)
    assert e.constantes.A == 2.94
    assert {"A01", "A04", "A05", "A06", "A07"} <= {a.codigo for a in e.avisos}
    assert "A" in e.fuente.constantes_predeterminadas


def test_study_retention_eligibility_and_cited_ids(tmp_path):
    def mutate(w):
        for col, value in enumerate(
            (
                "E01",
                "Synthetic author",
                "2026",
                "Synthetic title",
                "Venue",
                "urn:synthetic",
                "Synthetic",
                "Tool",
                "Task",
                "Time",
                "Declared only",
                "0,2",
                "Por revisar",
                "Risk",
                "Limit",
            ),
            1,
        ):
            w["estudios"].cell(6, col, value)
        w["parametros_ia"]["G6"] = "Estudio"
        w["parametros_ia"]["H6"] = "E01"

    e = load(tmp_path, mutate)
    assert e.estudios[0].cumple == "Por revisar"
    assert e.estudios[0].r_equivalente == 0.2
    assert "A08" in {a.codigo for a in e.avisos}
    assert {(x.celda, x.valor) for x in e.fuente.celdas if x.hoja == "estudios"} >= {
        ("O6", "Limit"),
        ("E6", "Venue"),
    }


@pytest.mark.parametrize(
    "sheet,cell,value",
    [
        ("proyecto", "C7", 0),
        ("proyecto", "C31", -1),
        ("proyecto", "C32", 0),
        ("proyecto", "C32", 1),
        ("proyecto", "C34", 0),
        ("proyecto", "C33", 0),
        ("parametros_ia", "D6", -0.01),
        ("parametros_ia", "F6", 1.01),
        ("parametros_ia", "D7", -0.01),
        ("presupuesto_inicial", "D13", 0),
        ("costo_real_sprint", "D6", -1),
    ],
)
def test_named_domain_boundaries(tmp_path, sheet, cell, value):
    with pytest.raises(ErrorDeEntrada) as caught:
        load(tmp_path, lambda w: setattr(w[sheet][cell], "value", value))
    assert "E03" in {p.codigo for p in caught.value.problemas}


def test_previous_numeric_contract_and_optional_dates_are_preserved(tmp_path):
    def mutate(w):
        w["proyecto"]["C33"] = "12,5"
        w["costo_real_sprint"]["B6"] = None
        w["costo_real_sprint"]["C6"] = None

    e = load(tmp_path, mutate)
    from modelo.cocomo import estimar_base

    assert estimar_base(e.proyecto, e.constantes).PM == pytest.approx(132.9109477935492)
    assert e.proyecto.T_meses == 12.5


def test_missing_study_ids_and_unknown_origins_are_rejected_together(tmp_path):
    def mutate(w):
        w["parametros_ia"]["G6"] = "Estudio"
        w["parametros_ia"]["G7"] = "Unknown origin"
        w["parametros_ia"]["G8"] = "Estudio"
        w["parametros_ia"]["H8"] = "E99"

    with pytest.raises(ErrorDeEntrada) as caught:
        load(tmp_path, mutate)
    assert {p.celda for p in caught.value.problemas if p.codigo == "E05"} == {
        "H6",
        "G7",
        "H8",
    }


def test_positive_comparison_denominators_and_included_budget_required(tmp_path):
    def mutate(w):
        w["presupuesto_inicial"]["G13"] = "No"
        for cell in ("D6", "K6", "L6", "M6", "N6"):
            w["costo_real_sprint"][cell] = 0

    with pytest.raises(ErrorDeEntrada) as caught:
        load(tmp_path, mutate)
    assert {"E03", "E09"} <= {p.codigo for p in caught.value.problemas}


def test_complete_activity_hours_and_serial_dates(tmp_path):
    def mutate(w):
        w["costo_real_sprint"]["B6"] = 46024
        for cell in ("E6", "F6", "G6", "H6"):
            w["costo_real_sprint"][cell] = 10

    e = load(tmp_path, mutate)
    assert e.caso.sprints[0].inicio == date(2026, 1, 2)
    assert e.caso.sprints[0].horas_4_actividades == 40
    assert "A05" not in {a.codigo for a in e.avisos}


def test_unparseable_date_is_e13_and_formula_input_is_not_executed(tmp_path):
    def mutate(w):
        w["costo_real_sprint"]["B6"] = "not a date"
        w["proyecto"]["C31"] = "=1+1"

    with pytest.raises(ErrorDeEntrada) as caught:
        load(tmp_path, mutate)
    assert {"E01", "E13"} <= {p.codigo for p in caught.value.problemas}


def test_sparse_case_ignores_blank_scaffold_rows(tmp_path):
    def mutate(w):
        for c in "ABCDEFG":
            w["presupuesto_inicial"][f"{c}24"] = w["presupuesto_inicial"][
                f"{c}13"
            ].value
            w["presupuesto_inicial"][f"{c}13"] = None
        for c in "BCDEFGHKLMNOP":
            w["costo_real_sprint"][f"{c}17"] = w["costo_real_sprint"][f"{c}6"].value
            w["costo_real_sprint"][f"{c}6"] = None

    e = load(tmp_path, mutate)
    assert len(e.caso.rubros) == len(e.caso.sprints) == 1
    assert e.caso.sprints[0].numero == 12


def test_symbol_lookup_uses_real_moved_coordinates(tmp_path):
    def mutate(w):
        s = w["proyecto"]
        s["B7"], s["B31"] = s["B31"].value, s["B7"].value
        s["C7"], s["C31"] = s["C31"].value, s["C7"].value

    e = load(tmp_path, mutate)
    assert e.proyecto.size_ksloc == 32 and e.proyecto.c_pm == 1000


@pytest.mark.parametrize("sheet", ["proyecto", "parametros_ia"])
def test_symbols_survive_inserted_row(tmp_path, sheet):
    workbook = libro_sintetico(caso=False)
    workbook[sheet].insert_rows(6)
    path = tmp_path / "grown.xlsx"
    workbook.save(path)
    workbook.close()
    before = sha256(path.read_bytes()).digest()
    try:
        entries = cargar_entradas(path)
        assert entries.proyecto.n_u == 10
        assert entries.parametros.h_int.esperado == 4
        cells = {(c.hoja, c.celda): c.valor for c in entries.fuente.celdas}
        if sheet == "proyecto":
            assert cells["proyecto", "C35"] == 10
        else:
            assert cells["parametros_ia", "E15"] == 4
    finally:
        assert sha256(path.read_bytes()).digest() == before


def test_constant_symbols_survive_inserted_row(tmp_path):
    def mutate(workbook):
        workbook["constantes"].insert_rows(6)

    entries = load(tmp_path, mutate, caso=False)
    assert entries.constantes.sced_pct_nominal == 100
    assert not entries.fuente.constantes_predeterminadas
    assert any(
        c.hoja == "constantes" and c.celda == "B17" and c.valor == 100
        for c in entries.fuente.celdas
    )


@pytest.mark.parametrize(
    "sheet,cell,value",
    [("proyecto", "C64", 10), ("parametros_ia", "E44", 4), ("constantes", "B46", 100)],
)
def test_symbols_cross_thirty_blank_rows_preserving_values_and_provenance(
    tmp_path, sheet, cell, value
):
    baseline = load(tmp_path, caso=False)
    entries = load(tmp_path, lambda w: w[sheet].insert_rows(6, 30), caso=False)
    assert (entries.proyecto, entries.parametros, entries.constantes) == (
        baseline.proyecto,
        baseline.parametros,
        baseline.constantes,
    )
    assert not entries.fuente.constantes_predeterminadas
    assert any(
        c.hoja == sheet and c.celda == cell and c.valor == value
        for c in entries.fuente.celdas
    )


@pytest.mark.parametrize(
    "sheet,column,symbol",
    [("proyecto", "B", "Size"), ("parametros_ia", "A", "r"), ("constantes", "A", "A")],
)
def test_duplicate_symbols_after_long_blank_gap_still_reject_without_writes(
    tmp_path, sheet, column, symbol
):
    with pytest.raises(ErrorDeEntrada) as caught:
        load(
            tmp_path,
            lambda w: setattr(w[sheet][f"{column}100"], "value", symbol),
            caso=False,
        )
    assert any(
        p.codigo == "E07"
        and p.hoja == sheet
        and p.celda == f"{column}100"
        and "Símbolo duplicado" in p.mensaje
        for p in caught.value.problemas
    )
