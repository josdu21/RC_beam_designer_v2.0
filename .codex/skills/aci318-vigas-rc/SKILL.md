---
name: aci318-vigas-rc
description: Realiza revision tecnica y checklist auditable de vigas de concreto reforzado segun ACI 318-19 (flexion, cortante, torsion), con trazabilidad obligatoria por seccion/ecuacion y manejo explicito de datos faltantes. Usa esta skill cuando el usuario pida revisar, validar, auditar o documentar el diseno de una viga RC bajo ACI 318-19, o cuando necesite una salida estructurada de cumplimiento (cumple/advertencia/no cumple/pendiente).
---

# ACI 318-19 Vigas RC

Usa esta skill para producir un checklist tecnico consistente con la logica del proyecto y referencias ACI.

## Flujo obligatorio
1. Recibir datos de entrada de geometria, materiales y cargas.
2. Verificar completitud de datos minimos.
3. Validar consistencia basica de entradas.
4. Ejecutar checklist por mecanismo: flexion, cortante, torsion.
5. Emitir resultado por verificacion con criterio ACI gobernante.
6. Consolidar estado global y acciones recomendadas.

## Datos minimos requeridos
- Geometria: `b`, `h`, `cover`.
- Materiales: `fc`, `fy`.
- Cargas: `Mu+`, `Mu-`, `Vu`, `Tu`.
- Opcionales de detalle: `n_legs`, `diametro_estribo`, `n_barras_torsion`.

Si falta cualquier dato minimo, no inventes valores. Marca `pendiente` y pide el dato puntual faltante.

## Validaciones basicas de entrada
- Verifica `b > 0`, `h > 0`, `fc > 0`, `fy > 0`.
- Verifica `cover > 0` y `cover < h`.
- Trata cargas negativas como magnitud solo si el contexto lo indica; registra advertencia de normalizacion de signo.
- Si alguna validacion falla, marca `no cumple` para ese bloque y explica la correccion requerida.

## Ejecucion del checklist por mecanismo
Carga `references/aci-mapping.md` antes de emitir criterios normativos.

### Flexion
- Evalua acero minimo (`As_min`) y estado de ductilidad (`phi` por deformacion de traccion).
- Reporta el estado de `Mu+` y `Mu-` por separado.
- Clasifica cada verificacion como `cumple`, `advertencia` o `no cumple`.

### Cortante
- Evalua `Vc`, necesidad de estribos, verificacion de `Vs_max`, y separacion gobernante.
- Si la seccion no satisface limite de cortante, marca `no cumple`.

### Torsion
- Evalua umbral `T_th` para torsion despreciable.
- Evalua chequeo combinado cortante-torsion en seccion transversal.
- Si torsion es significativa, reporta `At/s` y `Al` requeridos.

## Regla de trazabilidad obligatoria
Para cada verificacion incluye siempre:
- `code_ref`: seccion o ecuacion ACI.
- `formula_id`: identificador corto de la formula usada.
- `estado`: `cumple`, `advertencia`, `no cumple` o `pendiente`.
- `justificacion`: maximo 2 lineas, concreta y numerica cuando aplique.

## Formato de salida
Carga `references/checklist-template.md` y sigue exactamente su estructura.

Si el usuario no pide otro formato, entrega:
1. Datos de entrada.
2. Checklist de verificaciones por mecanismo.
3. Resumen de cumplimiento global.
4. Acciones recomendadas priorizadas.
5. Lista de datos faltantes (si existen).

## Criterios de decision global
- `cumple`: no hay `no cumple`; puede haber advertencias menores controlables.
- `advertencia`: no hay `no cumple`, pero hay riesgos tecnicos que requieren atencion.
- `no cumple`: existe al menos una verificacion critica no satisfecha.
- `pendiente`: faltan datos para concluir una o mas verificaciones criticas.

## Notas de disciplina
- No cites texto extenso del codigo ACI.
- Usa referencias por seccion/ecuacion y resume criterio tecnico.
- Mantiene consistencia con los `formula_id` usados en el proyecto cuando sea posible.
