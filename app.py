import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import pandas as pd
import random

# Configuración con diseño expandido y personalizado
st.set_page_config(page_title="Sink Tree Multicriterio - Thomas, Didi & Daniel", layout="wide")

# Inicialización estructurada del grafo en sesión
if 'G' not in st.session_state:
    G = nx.Graph()
    # Topología base
    rutas_base = [
        ('H', 'D', 8, 100, 1), ('D', 'A', 9, 100, 2), ('A', 'B', 7, 100, 1),
        ('H', 'E', 5, 50, 3), ('E', 'J', 10, 50, 1), ('J', 'C', 8, 100, 2),
        ('C', 'B', 6, 100, 1), ('H', 'O', 7, 50, 4), ('O', 'N', 9, 50, 2),
        ('N', 'J', 9, 50, 1)
    ]
    for u, v, d, b, e in rutas_base:
        G.add_edge(u, v, retardo=d, banda=b, errores=e, activo=True)
    st.session_state.G = G

G = st.session_state.G

st.title("Laboratorio de Redes: Optimización de Rutas Multicriterio")
st.markdown("Cálculo dinámico de C(P), el costo multicriterio normalizado del camino.")

# Panel lateral: Modificación estructural de la red
with st.sidebar:
    st.header("Gestión Dinámica de Nodos")
    
    nuevo_nodo = st.text_input("Habilitar nuevo router (Ej. Z):")
    if st.button("Añadir Nodo") and nuevo_nodo:
        G.add_node(nuevo_nodo)
        st.rerun()
        
    nodo_eliminar = st.selectbox("Eliminar router del grafo:", list(G.nodes()))
    if st.button("Borrar Nodo") and nodo_eliminar:
        G.remove_node(nodo_eliminar)
        st.rerun()

    st.header("Gestión de Enlaces de red")
    col1, col2 = st.columns(2)
    n1 = col1.selectbox("Origen:", list(G.nodes()), key='n1')
    n2 = col2.selectbox("Destino:", list(G.nodes()), key='n2')
    
    ret = st.number_input("Retardo (ms):", min_value=1, value=10)
    bw = st.number_input("Ancho de Banda (Mbps):", min_value=1, value=100)
    err = st.number_input("Tasa de errores (%):", min_value=1, value=1)
    
    if st.button("Crear / Modificar Enlace") and n1 != n2:
        G.add_edge(n1, n2, retardo=ret, banda=bw, errores=err, activo=True)
        st.rerun()
        
    # --- Nueva Función: Generador de Red Aleatoria (Malla) ---
    st.header("Generador Automático Aleatorio")
    st.markdown("Crea una topología compleja al azar.")
    num_nodos = st.number_input("Nodos intermedios", min_value=1, max_value=20, value=5)
    prob_conexion = st.slider("Probabilidad de cruces (Malla)", 0.1, 1.0, 0.3)
    
    if st.button("Generar Red Aleatoria"):
        st.session_state.G.clear()
        
        nodos_intermedios = [f"N{i}" for i in range(num_nodos)]
        todos_los_nodos = ["H"] + nodos_intermedios + ["B"]
        
        # 1. Garantizar al menos un camino principal para que no falle el cálculo
        for i in range(len(todos_los_nodos) - 1):
            st.session_state.G.add_edge(
                todos_los_nodos[i], 
                todos_los_nodos[i+1], 
                retardo=random.randint(5, 50), 
                banda=random.choice([10, 50, 100, 1000]), 
                errores=random.randint(1, 5),
                activo=True
            )
            
        # 2. Añadir enlaces aleatorios extra para formar una malla
        for i in range(len(todos_los_nodos)):
            for j in range(i + 2, len(todos_los_nodos)): # i+2 evita duplicar la línea principal
                if random.random() < prob_conexion:
                    st.session_state.G.add_edge(
                        todos_los_nodos[i], 
                        todos_los_nodos[j], 
                        retardo=random.randint(5, 50), 
                        banda=random.choice([10, 50, 100, 1000]), 
                        errores=random.randint(1, 5),
                        activo=True
                    )
        st.success(f"Topología aleatoria generada con {num_nodos} nodos intermedios.")
        st.rerun()

# Panel Central: Las 4 Variables de Decisión
st.subheader("Ajuste de Pesos Normalizados")
c1, c2, c3, c4 = st.columns(4)
alpha = c1.slider("Saltos (α)", 0.0, 1.0, 0.25)
beta = c2.slider("Demora (β)", 0.0, 1.0, 0.25)
gamma = c3.slider("Capacidad (γ)", 0.0, 1.0, 0.25)
delta = c4.slider("Errores (δ)", 0.0, 1.0, 0.25)

# Normalización
suma_pesos = alpha + beta + gamma + delta
if suma_pesos > 0:
    alpha, beta, gamma, delta = alpha/suma_pesos, beta/suma_pesos, gamma/suma_pesos, delta/suma_pesos

enlaces_activos = [(u, v, d) for u, v, d in G.edges(data=True) if d.get('activo', True)]
if enlaces_activos:
    d_ref = max(d['retardo'] for u, v, d in enlaces_activos)
    b_ref = max(d['banda'] for u, v, d in enlaces_activos)
    e_ref = max(d['errores'] for u, v, d in enlaces_activos)
else:
    d_ref = b_ref = e_ref = 1

# Filtrar grafo para cálculo de rutas (solo enlaces activos)
G_activo = nx.Graph()
for u, v, d in G.edges(data=True):
    if d.get('activo', True):
        costo = alpha*(1) + beta*(d['retardo']/d_ref) + gamma*(b_ref/d['banda']) + delta*(d['errores']/e_ref)
        G[u][v]['peso_optimo'] = costo
        G_activo.add_edge(u, v, weight=costo)

st.subheader("Visualización y Ruta Óptima")
origen = st.selectbox("Seleccionar origen H (s):", list(G.nodes()), index=list(G.nodes()).index('H') if 'H' in G.nodes() else 0)
destino = 'B'

ruta_optima = []
if destino in G_activo.nodes() and origen in G_activo.nodes():
    try:
        ruta_optima = nx.shortest_path(G_activo, source=origen, target=destino, weight='weight')
        st.success(f"Ruta dinámica más eficiente calculada: {' ➔ '.join(ruta_optima)}")
    except nx.NetworkXNoPath:
        st.error(f"La red está fragmentada. No hay conexión entre {origen} y {destino}.")

# Renderizado del Grafo
pos = nx.spring_layout(G, seed=42)
edge_traces = []
for u, v, data in G.edges(data=True):
    x0, y0 = pos[u]
    x1, y1 = pos[v]
    
    es_ruta = len(ruta_optima) > 0 and (u in ruta_optima and v in ruta_optima) and (abs(ruta_optima.index(u) - ruta_optima.index(v)) == 1)
    
    if not data.get('activo', True):
        color = 'red'
        dash = 'dash'
        width = 1
    elif es_ruta:
        color = '#2ca02c'
        dash = 'solid'
        width = 4
    else:
        color = '#cccccc'
        dash = 'solid'
        width = 2
        
    edge_traces.append(go.Scatter(x=[x0, x1, None], y=[y0, y1, None], line=dict(width=width, color=color, dash=dash), hoverinfo='none', mode='lines'))

node_x = [pos[n][0] for n in G.nodes()]
node_y = [pos[n][1] for n in G.nodes()]
node_trace = go.Scatter(x=node_x, y=node_y, mode='markers+text', text=list(G.nodes()), textposition="bottom center", marker=dict(size=25, color='#4A90E2', line=dict(width=2, color='DarkSlateGrey')))

fig = go.Figure(data=edge_traces + [node_trace], layout=go.Layout(showlegend=False, margin=dict(b=0, l=0, r=0, t=0), xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
st.plotly_chart(fig, use_container_width=True)

st.divider()

# TABLA INTERACTIVA Y RESET DE ESTADO
col_reset, col_title = st.columns([1, 4])
with col_reset:
    if st.button("🔄 Resetear Red"):
        if 'G' in st.session_state:
            del st.session_state['G']
        st.rerun()

st.subheader("Estado de Conexiones (Deshabilitar / Editar)")
datos_enlaces = [{"Origen": u, "Destino": v, "Retardo_ms": d.get('retardo'), "Banda_Mbps": d.get('banda'), "Errores_%": d.get('errores'), "Activo": d.get('activo', True)} for u, v, d in G.edges(data=True)]

if datos_enlaces:
    df_enlaces = pd.DataFrame(datos_enlaces)
    df_editado = st.data_editor(df_enlaces, disabled=["Origen", "Destino"], hide_index=True, use_container_width=True)
    
    hubo_cambios = False
    for _, fila in df_editado.iterrows():
        u, v = fila["Origen"], fila["Destino"]
        if G[u][v]['activo'] != fila["Activo"] or G[u][v]['retardo'] != fila["Retardo_ms"] or G[u][v]['banda'] != fila["Banda_Mbps"] or G[u][v]['errores'] != fila["Errores_%"]:
            G[u][v]['activo'] = fila["Activo"]
            G[u][v]['retardo'] = fila["Retardo_ms"]
            G[u][v]['banda'] = fila["Banda_Mbps"]
            G[u][v]['errores'] = fila["Errores_%"]
            hubo_cambios = True
    
    if hubo_cambios:
        st.rerun()

st.divider()

# COMPARACIÓN CON RUTAS DEL ARTÍCULO ORIGINAL
st.subheader("Comparativa de Rutas Base (Johal 2008)")
RUTAS_JOHAL = {
    "PSRC (Ruta Primaria)": ["H", "D", "A", "B"],
    "SSRC (Ruta Secundaria)": ["H", "E", "J", "C", "B"],
    "TSRC (Ruta Terciaria)": ["H", "O", "N", "J", "C", "B"],
}

comparativa = []
for nombre, ruta in RUTAS_JOHAL.items():
    activa = True
    costo_total = 0
    for i in range(len(ruta)-1):
        u, v = ruta[i], ruta[i+1]
        if not G.has_edge(u, v) or not G[u][v].get('activo', True):
            activa = False
            break
        costo_total += G[u][v].get('peso_optimo', 0)
    
    comparativa.append({
        "Ruta": nombre,
        "Recorrido": " ➔ ".join(ruta),
        "Costo Multicriterio (C(P))": round(costo_total, 4) if activa else "Inviable (Enlace Caído)",
        "Estado": "✅ Disponible" if activa else "❌ Rota"
    })

st.dataframe(pd.DataFrame(comparativa), hide_index=True, use_container_width=True)
