# Problemas al correr el WRF-Chem con MOZCART
Resumen: La especiación de las emisiones de compuestos orgánicos volátiles sin metano (NMVOC) generó un exceso de isoprenos. 
Esto conllevó a un error numérico en las reacciones químicas de formación de ozono. El mensaje fue el siguiente:

```bash
Forced exit from Rosenbrock due to the following error:
 Step size too small
 T=  6.000000000000008E-025 and H=  6.000000000000008E-025
```

Al inicio, se pensó que estaba relacionado con la estructura del modelo y las condiciones meteorológicas del modelo (ERA5), tambiém en la opción de fotólisis (`phot_opt`).
Sin embargo, lo que se encontró fue el exceso de isoprenos debido a la especiación. Esto fue detectado cuando se realizó la simulación del WRF-Chem sin activar las emisiones biogénicas del MEGAN (modo online).
Las pruebas de simulación fueron cinco para encontrar el problema:

- [no] solucionó cambiar ERA5 por NCEP-GDAS 0.25 grados
- [no] solucionó variar la estructura del dominio del modelo
- [no] solucionó cambiar la parametrización de configuraciones físicas del modelo
- [no] solucionó cambiar la configuración de las opciones del `phot_opt` de 3 a 1 (Madronich fotólisis)
- [si] solucionó desactivar MEGAN online: Generó estabilidad química, lo que sugiere que el exceso de VOC provocó una formación muy exagerada de ozono que hizo colapsar al modelo.
- [no] solucionó activar MEGAN online (1) y eliminar `ISOP` (isoprenos) de las emisiones antrópicas.
- [si] solucionó activar MEGAN (3) y eliminar `ISOP` (isoprenos) de las emisiones antrópicas.

