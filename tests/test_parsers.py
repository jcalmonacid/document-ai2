# app/tests/test_parsers.py
import pytest
from app.utils.parsers import parsear_metadata_filename
from datetime import date


def test_parser_basico():
    filename = "rtran_282_18082025.pdf"
    metadata = parsear_metadata_filename(filename)
    assert metadata["prefijo"] == "rtran"
    assert metadata["numero_correlativo"] == 282
    assert metadata["fecha_archivo"] == date(2025, 8, 18)
    assert metadata["es_fe_de_erratas"] is False


def test_parser_fe_de_erratas():
    filename = "rtran_282_18082025_fe.pdf"
    metadata = parsear_metadata_filename(filename)
    assert metadata["es_fe_de_erratas"] is True


def test_parser_invalid_format():
    with pytest.raises(ValueError):
        parsear_metadata_filename("archivo_invalido.pdf")


def test_parser_invalid_date():
    with pytest.raises(ValueError):
        parsear_metadata_filename("rtran_282_31132025.pdf")
