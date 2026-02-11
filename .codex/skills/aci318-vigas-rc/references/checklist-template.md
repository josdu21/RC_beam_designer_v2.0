# Plantilla de salida - Checklist de diseno ACI 318-19

Usa esta plantilla como formato por defecto.

## 1. Datos de entrada
- Geometria: `b`, `h`, `cover`, `d` (si disponible).
- Materiales: `fc`, `fy`.
- Cargas: `Mu+`, `Mu-`, `Vu`, `Tu`.
- Parametros de detalle: `n_legs`, `diametro_estribo`, `n_barras_torsion` (si aplica).

## 2. Checklist por mecanismo

### 2.1 Flexion
- Verificacion:
  - `code_ref:` ...
  - `formula_id:` ...
  - `estado:` `cumple|advertencia|no cumple|pendiente`
  - `justificacion:` ...

### 2.2 Cortante
- Verificacion:
  - `code_ref:` ...
  - `formula_id:` ...
  - `estado:` `cumple|advertencia|no cumple|pendiente`
  - `justificacion:` ...

### 2.3 Torsion
- Verificacion:
  - `code_ref:` ...
  - `formula_id:` ...
  - `estado:` `cumple|advertencia|no cumple|pendiente`
  - `justificacion:` ...

## 3. Criterios ACI gobernantes
- Flexion: `code_ref` + razon breve.
- Cortante: `code_ref` + razon breve.
- Torsion: `code_ref` + razon breve.

## 4. Resultado global
- Estado global: `cumple|advertencia|no cumple|pendiente`.
- Resumen tecnico: maximo 5 lineas.

## 5. Acciones recomendadas
1. Accion prioritaria 1 (si existe no cumplimiento critico).
2. Accion prioritaria 2.
3. Accion prioritaria 3.

## 6. Datos faltantes (si aplica)
- Campo faltante:
  - impacto tecnico:
  - decision bloqueada:
