# RC Beam Designer

Aplicacion web con Streamlit para el diseno de vigas de concreto reforzado segun ACI 318-19.

## Funcionalidades

- **Flexion**: Calculo de refuerzo longitudinal para momentos positivos y negativos
- **Cortante**: Diseno de estribos con metodo simplificado
- **Torsion**: Verificacion de umbral, adecuacion de seccion y refuerzo requerido
- **Reporte**: Resumen consolidado de todo el diseno
- **Trazabilidad ACI**: Salida con verificaciones normativas (`trace`) por modulo
- **Estado central de diseno**: Coherencia entre pestanas y reporte

## Requisitos

- Python 3.9+
- Dependencias: ver `requirements.txt`

## Uso

```bash
pip install -r requirements.txt
streamlit run app.py
```

O alternativamente:

```bash
python run_app.py
```

## Estructura del Proyecto

```
app.py                          # Entrada principal Streamlit
run_app.py                      # Script para lanzar la app
src/models/
    aci_constants.py            # Constantes ACI 318-19 (MPa)
    units.py                    # Helpers de conversion de unidades
    section.py                  # Modelo BeamSection
    flexure.py                  # Calculos de flexion
    shear.py                    # Calculos de cortante
    torsion.py                  # Calculos de torsion
src/ui/
    plotting.py                 # Visualizaciones matplotlib
    tabs/                       # Modulos de pestanas UI
tests/                          # Tests unitarios (pytest)
```

## Unidades

- **Entrada**: cm, MPa, kN, kNm
- **Calculos internos**: mm, N, N-mm
- **Norma**: ACI 318-19 (unidades SI)

## Tests

```bash
python -m pytest tests/ -v
```

## Calidad de codigo

```bash
pip install -r requirements-dev.txt
python -m ruff check src tests
python -m mypy src/models
```
