import os
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from data import data_loader
from domain.models import Estudiante

@pytest.fixture
def mock_parquet_file(tmp_path):
    data = [
        {
            "id": "226201.1001",
            "periodo": "2026-1",
            "nrc": "1001",
            "codigo_estudiante": "N0001",
            "nombre_estudiante": "Diego Test",
            "email_upn": "diego@upn.pe",
            "correo_est_personal": "diego@personal.com"
        },
        {
            "id": "226201.1001",
            "periodo": "2026-1",
            "nrc": "1001",
            "codigo_estudiante": "N0002",
            "nombre_estudiante": "William Test",
            "email_upn": "william@upn.pe",
            "correo_est_personal": None 
        }
    ]
    df = pd.DataFrame(data)
    file_path = tmp_path / "estudiantes_test.parquet"
    df.to_parquet(file_path)
    return str(file_path)

def test_load_estudiantes_from_fake_file(mock_parquet_file, monkeypatch):
    monkeypatch.setenv("PATH_ESTUDIANTES", mock_parquet_file)
    data_loader.load_estudiantes.cache_clear()
    
    estudiantes = data_loader.load_estudiantes()
    
    assert len(estudiantes) == 2
    assert estudiantes[0].nombre_estudiante == "Diego Test"
    
    # Aquí la clave: En Pandas, None se convierte en NaN. 
    # Verificamos si es NaN usando pandas.isna() o comparando con nan
    assert pd.isna(estudiantes[1].correo_est_personal)
    
    # También podemos probar la propiedad dinámica que creaste
    assert estudiantes[0].email_destino == "diego@upn.pe"
    # Si el institucional falla, debería usar el personal (aunque sea NaN en este caso, 
    # pero tu lógica dice que prefiere institucional)
    assert estudiantes[1].email_destino == "william@upn.pe"

def test_get_env_variable_error(monkeypatch):
    monkeypatch.delenv("PATH_ESTUDIANTES", raising=False)
    with pytest.raises(ValueError, match="La variable de entorno 'PATH_ESTUDIANTES' no está definida"):
        data_loader.load_estudiantes.cache_clear()
        data_loader.load_estudiantes()
