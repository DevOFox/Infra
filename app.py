"""
Laboratorio: Principio de optimalidad y Sink Tree (Johal, 2008)
Python + NetworkX + Streamlit + Plotly

Ejecutar:  python -m streamlit run app.py
"""

import math

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Laboratorio Johal - Sink Tree", layout="wide")

# ----------------------------------------------------------------------
# DATOS BASE DEL LABORATORIO
# ----------------------------------------------------------------------
ORIGEN, DESTINO = "H", "B"

# Enlaces: (u, v, retardo ms, capacidad Mbps). Datos de ejemplo del laboratorio.
ENLACES_BASE = [
    ("H", "D", 8, 100),
    ("D", "A", 9, 100),
    ("A", "B", 7, 100),
    ("H", "E", 5, 50),
    ("E", "J", 10, 50),
    ("J", "C", 8, 100),
    ("C", "B", 6, 100),
    ("H", "O", 7, 50),
    ("O", "N", 9, 50),
    ("N", "J", 9, 50),
]

# Los tres caminos del artículo, en orden de prioridad (PSRC, SSRC, TSRC)
RUTAS_JOHAL = {
    "PSRC": ["H", "D", "A", "B"],
    "SSRC": ["H", "E", "J", "C", "B"],
    "TSRC": ["H", "O", "N", "J", "C", "B"],
}

# Posiciones fijas para dibujar el grafo
POS = {
    "H": (0.0, 0.0),
    "D": (1.2, 1.6),
    "A": (2.8, 1.6),
    "E": (1.2, 0.0),
    "J": (2.6, 0.0),
    "C": (3.9, 0.0),
    "B": (5.0, 0.8),
    "O": (1.2, -1.6),
    "N": (2.6, -1.6),
}

OBJ_SALTOS = "Mínimo de saltos H(P) (modelo Johal)"
OBJ_RETARDO = "Mínimo retardo D(P)"
OBJ_MULTI = "Multicriterio C(P)"


def tabla_base() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Origen": [e[0] for e in ENLACES_BASE],
            "Destino": [e[1] for e in ENLACES_BASE],
            "Retardo_ms": [float(e[2]) for e in ENLACES_BASE],
            "Banda_Mbps": [float(e[3]) for e in ENLACES_BASE],
            "Disponible": [True] * len(ENLACES_BASE),
        }
    )


# ----------------------------------------------------------------------
# FUNCIONES DEL MODELO
# ----------------------------------------------------------------------
def referencias(df: pd.DataFrame):
    """d_ref y b_ref: máximos valores positivos de la tabla de enlaces actual."""
    d_pos = df.loc[df["Retardo_ms"] > 0, "Retardo_ms"]
    b_pos = df.loc[df["Banda_Mbps"] > 0, "Banda_Mbps"]
    d_ref = float(d_pos.max()) if len(d_pos) else 1.0
    b_ref = float(b_pos.max()) if len(b_pos) else 1.0
    return d_ref, b_ref


def costo_arista(fila, objetivo, alfa, beta, gamma, d_ref, b_ref) -> float:
    """Costo de un enlace según la función objetivo escogida."""
    if objetivo == OBJ_SALTOS:
        return 1.0
    if objetivo == OBJ_RETARDO:
        return float(fila["Retardo_ms"])
    # Multicriterio: alfa + beta*(d/d_ref) + gamma*(b_ref/b)
    return alfa + beta * (fila["Retardo_ms"] / d_ref) + gamma * (b_ref / fila["Banda_Mbps"])


def enlace_usable(fila) -> bool:
    """Un enlace se puede usar si está activo y tiene capacidad positiva."""
    return bool(fila["Disponible"]) and fila["Banda_Mbps"] > 0


def construir_grafo(df, objetivo, alfa, beta, gamma, d_ref, b_ref) -> nx.Graph:
    """Grafo no dirigido solo con enlaces disponibles; atributo 'w' = costo."""
    G = nx.Graph()
    G.add_nodes_from(POS.keys())
    for _, f in df.iterrows():
        if enlace_usable(f):
            G.add_edge(
                f["Origen"],
                f["Destino"],
                w=costo_arista(f, objetivo, alfa, beta, gamma, d_ref, b_ref),
            )
    return G


def indice_enlaces(df: pd.DataFrame) -> dict:
    """Diccionario {frozenset({u,v}): fila} para consultar un enlace sin importar el orden."""
    return {frozenset((f["Origen"], f["Destino"])): f for _, f in df.iterrows()}


def metricas_camino(camino, idx, alfa, beta, gamma, d_ref, b_ref) -> dict:
    """H(P), D(P), B(P), C(P) de un camino (lista de nodos)."""
    aristas = list(zip(camino[:-1], camino[1:]))
    filas = [idx[frozenset(a)] for a in aristas]
    H = len(aristas)
    D = sum(f["Retardo_ms"] for f in filas)
    Bw = min(f["Banda_Mbps"] for f in filas)
    C = sum(costo_arista(f, OBJ_MULTI, alfa, beta, gamma, d_ref, b_ref) for f in filas)
    disponible = all(enlace_usable(f) for f in filas)
    return {"H(P)": H, "D(P) ms": D, "B(P) Mbps": Bw, "C(P)": round(C, 4), "Disponible": disponible}


def camino_optimo(G: nx.Graph):
    try:
        return nx.dijkstra_path(G, ORIGEN, DESTINO, weight="w")
    except nx.NetworkXNoPath:
        return None


def ruta_estatica(df, idx):
    """Primera ruta preconfigurada del artículo cuyos enlaces están todos disponibles."""
    for nombre, camino in RUTAS_JOHAL.items():
        aristas = zip(camino[:-1], camino[1:])
        if all(enlace_usable(idx[frozenset(a)]) for a in aristas):
            return nombre, camino
    return None, None


def sink_tree(G: nx.Graph):
    """Siguiente salto de cada nodo hacia B (árbol de caminos mínimos con raíz en B)."""
    caminos = nx.single_source_dijkstra_path(G, DESTINO, weight="w")
    siguiente = {}
    for nodo, camino in caminos.items():
        if nodo != DESTINO:
            siguiente[nodo] = camino[-2]  # camino va de B a nodo; el penúltimo es el siguiente salto
    return siguiente


# ----------------------------------------------------------------------
# GRÁFICOS
# ----------------------------------------------------------------------
def figura_grafo(df, camino=None, titulo="", mostrar_etiquetas=True):
    fig = go.Figure()
    en_camino = set()
    if camino:
        en_camino = {frozenset(a) for a in zip(camino[:-1], camino[1:])}

    for _, f in df.iterrows():
        u, v = f["Origen"], f["Destino"]
        x0, y0 = POS[u]
        x1, y1 = POS[v]
        usable = enlace_usable(f)
        es_camino = frozenset((u, v)) in en_camino
        if not usable:
            color, ancho, dash = "#d62728", 2, "dash"
        elif es_camino:
            color, ancho, dash = "#2ca02c", 6, "solid"
        else:
            color, ancho, dash = "#9aa0a6", 2, "solid"
        fig.add_trace(
            go.Scatter(x=[x0, x1], y=[y0, y1], mode="lines",
                       line=dict(color=color, width=ancho, dash=dash),
                       hoverinfo="skip", showlegend=False)
        )
        if mostrar_etiquetas:
            etiqueta = f"{f['Retardo_ms']:g} ms<br>{f['Banda_Mbps']:g} Mbps"
            if not usable:
                etiqueta = "CAÍDO"
            fig.add_annotation(x=(x0 + x1) / 2, y=(y0 + y1) / 2, text=etiqueta,
                               showarrow=False, font=dict(size=10),
                               bgcolor="rgba(255,255,255,0.85)")

    nodos = list(POS.keys())
    colores = []
    for n in nodos:
        if n == ORIGEN:
            colores.append("#1f77b4")
        elif n == DESTINO:
            colores.append("#ff7f0e")
        elif camino and n in camino:
            colores.append("#2ca02c")
        else:
            colores.append("#cfd4da")
    fig.add_trace(
        go.Scatter(x=[POS[n][0] for n in nodos], y=[POS[n][1] for n in nodos],
                   mode="markers+text", text=nodos, textposition="middle center",
                   textfont=dict(size=15, color="black"),
                   marker=dict(size=38, color=colores, line=dict(width=2, color="#333")),
                   hoverinfo="skip", showlegend=False)
    )
    fig.update_layout(title=titulo, height=480, margin=dict(l=10, r=10, t=50, b=10),
                      xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"),
                      plot_bgcolor="white")
    return fig


def figura_sink_tree(df, siguiente):
    fig = figura_grafo(df, camino=None, titulo=f"Sink Tree hacia {DESTINO} (flechas = siguiente salto)",
                       mostrar_etiquetas=False)
    for nodo, sig in siguiente.items():
        x0, y0 = POS[nodo]
        x1, y1 = POS[sig]
        fig.add_annotation(x=x1, y=y1, ax=x0, ay=y0, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=3, arrowsize=1.6, arrowwidth=3,
                           arrowcolor="#2ca02c", standoff=24, startstandoff=24)
    return fig


# ----------------------------------------------------------------------
# INTERFAZ
# ----------------------------------------------------------------------
st.title("Laboratorio: Principio de optimalidad y Sink Tree")
st.caption("Basado en Johal (2008). Los datos en ms y Mbps y la función multicriterio son "
           "construcciones del laboratorio, no resultados del artículo.")

if "version" not in st.session_state:
    st.session_state.version = 0

# ---------------- Barra lateral ----------------
st.sidebar.header("Función objetivo")
objetivo = st.sidebar.radio("Criterio de optimización", [OBJ_SALTOS, OBJ_RETARDO, OBJ_MULTI])

st.sidebar.subheader("Pesos (solo multicriterio)")
a_raw = st.sidebar.slider("α  (saltos)", 0.0, 1.0, 0.5, 0.05)
b_raw = st.sidebar.slider("β  (retardo)", 0.0, 1.0, 0.35, 0.05)
g_raw = st.sidebar.slider("γ  (penalización capacidad)", 0.0, 1.0, 0.15, 0.05)
suma = a_raw + b_raw + g_raw
if suma == 0:
    st.sidebar.warning("Los tres pesos son 0; se usan pesos iguales (1/3).")
    alfa = beta = gamma = 1 / 3
else:
    alfa, beta, gamma = a_raw / suma, b_raw / suma, g_raw / suma
st.sidebar.write(f"Normalizados: α={alfa:.3f}, β={beta:.3f}, γ={gamma:.3f}")

if st.sidebar.button("Restablecer tabla y parámetros"):
    st.session_state.version += 1
    st.rerun()

# ---------------- Sección 1: tabla editable ----------------
st.header("1. Tabla de enlaces")
st.write("Edita **Retardo_ms**, **Banda_Mbps** y **Disponible** (desmarcar = enlace caído).")
df = st.data_editor(
    tabla_base(),
    key=f"editor_{st.session_state.version}",
    disabled=["Origen", "Destino"],
    hide_index=True,
    width="stretch",
    column_config={
        "Retardo_ms": st.column_config.NumberColumn("Retardo_ms", min_value=0.0, step=1.0),
        "Banda_Mbps": st.column_config.NumberColumn("Banda_Mbps", min_value=0.0, step=1.0),
        "Disponible": st.column_config.CheckboxColumn("Disponible"),
    },
)
df = df.fillna({"Retardo_ms": 0.0, "Banda_Mbps": 0.0, "Disponible": False})

d_ref, b_ref = referencias(df)
idx = indice_enlaces(df)
G = construir_grafo(df, objetivo, alfa, beta, gamma, d_ref, b_ref)

# ---------------- Sección 2: ruta óptima vs estática ----------------
st.header("2. Ruta óptima recalculada vs. selección estática")
st.latex(r"H(P)=\sum_{(i,j)\in P}h_{ij},\quad h_{ij}=1")
st.latex(r"D(P)=\sum_{(i,j)\in P}d_{ij}")
st.latex(r"C(P)=\sum_{(i,j)\in P}\left[\alpha+\beta\frac{d_{ij}}{d_{ref}}+\gamma\frac{b_{ref}}{b_{ij}}\right],\quad \alpha+\beta+\gamma=1")
st.latex(r"B(P)=\min_{(i,j)\in P} b_{ij}")
st.info(f"d_ref = {d_ref:g} ms | b_ref = {b_ref:g} Mbps | α={alfa:.3f}, β={beta:.3f}, γ={gamma:.3f}  "
        "(regístralos en cada experimento: cambian si modificas la tabla).")

optimo = camino_optimo(G)
nombre_est, camino_est = ruta_estatica(df, idx)

col1, col2 = st.columns([3, 2])
with col1:
    if optimo:
        st.plotly_chart(figura_grafo(df, optimo, f"Camino óptimo recalculado ({objetivo})"),
                        width="stretch")
    else:
        st.error("No existe camino disponible entre H y B con los enlaces actuales.")
        st.plotly_chart(figura_grafo(df, None, "Sin camino H → B"), width="stretch")

with col2:
    st.subheader("Camino óptimo recalculado")
    if optimo:
        m = metricas_camino(optimo, idx, alfa, beta, gamma, d_ref, b_ref)
        st.success(" → ".join(optimo))
        st.write(f"H(P) = {m['H(P)']} | D(P) = {m['D(P) ms']:g} ms | "
                 f"B(P) = {m['B(P) Mbps']:g} Mbps | C(P) = {m['C(P)']}")
    st.subheader("Selección estática (artículo)")
    if camino_est:
        m = metricas_camino(camino_est, idx, alfa, beta, gamma, d_ref, b_ref)
        st.warning(f"{nombre_est}: " + " → ".join(camino_est))
        st.write(f"H(P) = {m['H(P)']} | D(P) = {m['D(P) ms']:g} ms | "
                 f"B(P) = {m['B(P) Mbps']:g} Mbps | C(P) = {m['C(P)']}")
        if optimo and optimo == camino_est:
            st.caption("Coinciden: la ruta estática también es la óptima para este criterio.")
        elif optimo:
            st.caption("Difieren: el recálculo encontró una ruta mejor que la primera estática disponible.")
    else:
        st.error("Ninguna de las tres rutas preconfiguradas está disponible.")

st.subheader("Métricas de las tres rutas del artículo")
filas_rutas = []
for nombre, camino in RUTAS_JOHAL.items():
    m = metricas_camino(camino, idx, alfa, beta, gamma, d_ref, b_ref)
    filas_rutas.append({"Ruta": nombre, "Recorrido": "–".join(camino), **m})
tabla_rutas = pd.DataFrame(filas_rutas)
st.dataframe(tabla_rutas, hide_index=True, width="stretch")

# ---------------- Sección 3: Sink Tree ----------------
st.header("3. Sink Tree hacia B")
siguiente = sink_tree(G)
st.plotly_chart(figura_sink_tree(df, siguiente), width="stretch")
filas_st = []
for nodo in POS:
    if nodo == DESTINO:
        continue
    filas_st.append({"Router": nodo, "Siguiente salto hacia B": siguiente.get(nodo, "— (sin ruta)")})
st.dataframe(pd.DataFrame(filas_st), hide_index=True, width="stretch")
st.caption("El Sink Tree fija UN solo siguiente salto por nodo; no muestra rutas de respaldo.")

# ---------------- Sección 4: definiciones y exportación ----------------
st.header("4. Definiciones y exportación")
st.markdown(
    """
- **G=(V,E):** grafo no dirigido de routers y enlaces.
- **h_ij:** costo por salto (=1). **d_ij:** retardo (ms). **b_ij:** capacidad (Mbps). **f_ij:** 1 activo, 0 caído.
- **H(P), D(P):** suma de saltos y de retardos. **B(P)=min b_ij:** cuello de botella.
- **C(P):** costo multicriterio normalizado; la penalización b_ref/b_ij sirve para usar Dijkstra y **no** equivale a B(P).
- **T_B:** árbol de siguientes saltos hacia B.
"""
)

filas_res = []
for nombre, camino in RUTAS_JOHAL.items():
    m = metricas_camino(camino, idx, alfa, beta, gamma, d_ref, b_ref)
    filas_res.append({"Tipo": f"Johal {nombre}", "Recorrido": "-".join(camino), **m})
if optimo:
    m = metricas_camino(optimo, idx, alfa, beta, gamma, d_ref, b_ref)
    filas_res.append({"Tipo": "Óptimo recalculado", "Recorrido": "-".join(optimo), **m})
else:
    filas_res.append({"Tipo": "Óptimo recalculado", "Recorrido": "SIN RUTA"})
res = pd.DataFrame(filas_res)
res.insert(0, "Objetivo", objetivo)
res["alpha"], res["beta"], res["gamma"] = round(alfa, 4), round(beta, 4), round(gamma, 4)
res["d_ref"], res["b_ref"] = d_ref, b_ref
res["Seleccion_estatica"] = nombre_est if nombre_est else "NINGUNA"

c1, c2 = st.columns(2)
c1.download_button("Descargar CSV de resultados", res.to_csv(index=False).encode("utf-8-sig"),
                   "resultados_johal.csv", "text/csv")
c2.download_button("Descargar CSV de enlaces", df.assign(Disponible=df["Disponible"].astype(int))
                   .to_csv(index=False).encode("utf-8-sig"), "enlaces_johal.csv", "text/csv")
