from decimal import Decimal

import pytest
from nutritwin_domain.units import convert, to_canonical


def test_mass_boundary_conversion_is_exact() -> None:
    assert convert(Decimal("1000"), "ug", "mg") == Decimal("1")
    assert convert(Decimal("0.001"), "g", "mg") == Decimal("1")


def test_energy_conversion() -> None:
    assert convert(Decimal("4.184"), "kJ", "kcal") == Decimal("1")


def test_unsupported_and_float_inputs_fail_closed() -> None:
    with pytest.raises(ValueError):
        convert(Decimal("1"), "cup", "g")
    with pytest.raises(TypeError):
        to_canonical("iron", 1.2, "mg")  # type: ignore[arg-type]
