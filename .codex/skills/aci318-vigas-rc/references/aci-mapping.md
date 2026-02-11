# Mapeo de verificaciones ACI 318-19 (vigas RC)

Usa este mapeo para citar `code_ref` y `formula_id` de forma consistente.

## 1) Flexion
- `formula_id: As_min`
  - `code_ref: ACI 318-19 Table 9.6.1.2`
  - Criterio: verificar acero minimo longitudinal.
- `formula_id: phi_strain_classification`
  - `code_ref: ACI 318-19 Section 21.2.2`
  - Criterio: clasificacion por deformacion de traccion (`phi` y ductilidad).
- `formula_id: phiMn_quadratic_discriminant`
  - `code_ref: ACI 318-19 Section 22.2`
  - Criterio: detectar seccion sobrecargada/compresion no admisible.

## 2) Cortante
- `formula_id: Vc_simplified`
  - `code_ref: ACI 318-19 Section 22.5`
  - Criterio: capacidad de cortante del concreto.
- `formula_id: Vu_threshold_no_stirrups`
  - `code_ref: ACI 318-19 Section 9.6`
  - Criterio: evaluar si se puede omitir refuerzo de cortante.
- `formula_id: Vs_max`
  - `code_ref: ACI 318-19 Section 22.5`
  - Criterio: limite maximo de contribucion de estribos.
- `formula_id: stirrup_spacing`
  - `code_ref: ACI 318-19 Table 9.7.6.2.2`
  - Criterio: separacion maxima de estribos y minima por refuerzo minimo.

## 3) Torsion
- `formula_id: T_th`
  - `code_ref: ACI 318-19 Section 22.7`
  - Criterio: determinar torsion despreciable.
- `formula_id: combined_shear_torsion_stress`
  - `code_ref: ACI 318-19 Section 22.7.7.1`
  - Criterio: verificacion de adecuacion de seccion para cortante + torsion.
- `formula_id: At_over_s`
  - `code_ref: ACI 318-19 Section 22.7`
  - Criterio: refuerzo transversal requerido por torsion.
- `formula_id: Al_min_and_required`
  - `code_ref: ACI 318-19 Eq. 9.6.4.3(a)`
  - Criterio: refuerzo longitudinal adicional por torsion.

## 4) Normalizacion de entrada
- `formula_id: <load>_SIGN_NORMALIZATION`
  - `code_ref: Input Policy (proyecto)`
  - Criterio: si llega carga negativa por convencion de signo, documentar conversion a magnitud como advertencia.

## 5) Reglas de clasificacion de estado
- `cumple`: verificacion satisfecha sin condiciones.
- `advertencia`: verificacion satisfecha con riesgo, transicion o baja ductilidad.
- `no cumple`: verificacion critica no satisfecha.
- `pendiente`: falta informacion para concluir.
