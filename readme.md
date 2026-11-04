# Laboratorio de Redes: Optimización de Rutas Multicriterio (Sink Tree)

Este proyecto es una aplicación interactiva desarrollada en Python y Streamlit, basada en el estudio de optimalidad y Sink Tree de Hartinder Singh Johal (2008). Permite modelar routers y enlaces mediante un grafo no dirigido y calcular rutas óptimas utilizando una función objetivo multicriterio.

## Autores
- Thomas

- Didi

- Daniel


## Características Principales
- **Grafo Interactivo:** Visualización de la topología de red usando Plotly.

- **Gestión Dinámica:** Agregar o eliminar routers y modificar parámetros de enlaces (retardo, ancho de banda, tasa de errores y disponibilidad) en tiempo real.

- **Función Multicriterio $C(P)$:** Cálculo de costos normalizados ajustando pesos ($\alpha, \beta, \gamma, \delta$) para saltos, demora, capacidad y tasa de errores.

- **Comparativa de Rutas:** Evaluación automática frente a las rutas estáticas originales del estudio (PSRC, SSRC, TSRC).


## Requisitos
Asegúrate de tener Python 3.9+ instalado. Las dependencias se encuentran en `requirements.txt`.

## Instalación y Ejecución
1. Clona este repositorio o descarga los archivos.

2. Abre una terminal (CMD o PowerShell) en la carpeta del proyecto.
3. Instala las dependencias:
   ```bash
   python -m pip install -r requirements.txt
   ```