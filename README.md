# Laboratorio Johal: Principio de optimalidad y Sink Tree

Aplicación web interactiva hecha con **Python + NetworkX + Streamlit + Plotly** que demuestra cómo cambian las rutas óptimas de una red al modificar retardos, capacidades y fallas de enlaces. Compara la **selección estática** de rutas preconfiguradas con el **recálculo dinámico** mediante el algoritmo de Dijkstra.

Basado en el estudio de Hartinder Singh Johal (2008) sobre el principio de optimalidad y el Sink Tree en enrutamiento estático adaptativo.

## Qué hace

- Modela la red como un grafo no dirigido `G=(V,E)` con routers y enlaces (origen **H**, destino **B**).
- Permite editar en una tabla el **retardo (ms)**, la **capacidad (Mbps)** y la **disponibilidad** de cada enlace.
- Calcula la ruta óptima con tres funciones objetivo:
  - Mínimo de saltos `H(P)` (modelo original de Johal)
  - Mínimo retardo `D(P)`
  - Multicriterio `C(P)` con pesos α, β, γ normalizados
- Muestra el cuello de botella `B(P) = min b_ij` de cada ruta.
- Compara la primera ruta estática disponible (PSRC, SSRC, TSRC) contra el camino recalculado.
- Dibuja el **Sink Tree** hacia B con flechas de siguiente salto.
- Exporta los resultados y la tabla de enlaces en CSV.

## Formulación

```
H(P) = Σ h_ij                       con h_ij = 1
D(P) = Σ d_ij
C(P) = Σ [ α + β·(d_ij / d_ref) + γ·(b_ref / b_ij) ]     con α + β + γ = 1
B(P) = min b_ij
```

`d_ref` y `b_ref` son los máximos positivos de la tabla de enlaces actual, por lo que cambian al editar los datos. La app los muestra para que se registren en cada experimento.

## Requisitos

- Python 3.9 o superior
- Las librerías de `requirements.txt`: streamlit, networkx, plotly, pandas

## Cómo ejecutarlo

### Windows, con un clic

Descarga el proyecto, ponlo en una carpeta y haz doble clic en **`ejecutar.bat`**. Instala lo necesario si falta y abre la app en el navegador.

### Desde la terminal

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Se abre en http://localhost:8501. No ejecutes `python app.py` directamente: una app de Streamlit debe lanzarse con `streamlit run`.

## Estructura del proyecto

```
.
├── app.py              # Código completo de la aplicación
├── requirements.txt    # Dependencias
├── ejecutar.bat        # Lanzador de un clic para Windows
└── README.md
```

## Experimentos del laboratorio

| Prueba | Acción en la app | Resultado esperado |
| --- | --- | --- |
| A. Réplica original | Restablecer; criterio de saltos | H(P1)=3, H(P2)=4, H(P3)=5 |
| B. Cambio de retardo | H–D = 40 ms; criterio de retardo | D(P1)=56, D(P2)=29, D(P3)=39 ms; mejor ruta H–E–J–C–B |
| C. Fallo primario | Desmarcar H–D | Selección estática SSRC; coincide con el óptimo recalculado |
| D. Doble fallo | Desmarcar también H–E | Solo queda TSRC |
| E. Cuello de botella | E–J = 5 Mbps | B(P2) = 5 Mbps |
| F. Cambio de pesos | Multicriterio con (1,0,0), (0,1,0), (0,0,1), (0.5,0.35,0.15) | Con (0.5,0.35,0.15): C(P1)=2.79, C(P2)=3.915, C(P3)=5.065 |

## Cómo está organizado el código

- **Datos base:** lista de enlaces, rutas de Johal y posiciones para dibujar.
- **Modelo:** `costo_arista`, `construir_grafo`, `metricas_camino`, `camino_optimo`, `ruta_estatica`, `sink_tree`.
- **Gráficos:** `figura_grafo` y `figura_sink_tree` con Plotly.
- **Interfaz:** barra lateral con criterio y pesos, y cuatro secciones (tabla, comparación de rutas, Sink Tree, exportación).

## Alcance

Los valores en ms y Mbps y la función multicriterio son construcciones de este laboratorio. **No** son resultados experimentales reportados por Johal; el artículo original no optimiza una función combinada de retardo, ancho de banda y confiabilidad.

## Referencia

Johal, H. S. (2008). *Optimality Principle Based Sink Tree Methodology for Adaptive Static Routing Using Multiple Route Configuration Scheme.* Advances in Electrical and Electronics Engineering / WCECS 2008. DOI: [10.1109/WCECS.2008.21](https://doi.org/10.1109/WCECS.2008.21)
