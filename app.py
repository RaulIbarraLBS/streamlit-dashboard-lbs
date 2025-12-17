import streamlit as st
import pandas as pd
from google.cloud import bigquery
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="Reporte LBS+ (Streamlit)")

# Estilo CSS para ocultar menú y limpiar la vista (Estilo "App Nativa")
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #f8f9fa; }
    /* Estilo para las tarjetas de métricas */
    div[data-testid="metric-container"] {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. CONEXIÓN A BIGQUERY (Con Caché para NO saturar RAM)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300) # Se actualiza cada 5 minutos
def get_data():
    # Intenta leer secretos para conexión segura
    try:
        # Crea cliente usando los secretos de Streamlit Cloud
        # OJO: Esto requiere configurar .streamlit/secrets.toml
        client = bigquery.Client() 
        
        # Tu Query EXACTO basado en tus capturas
        query = """
        SELECT 
            profesor,
            campus,
            periodo,
            grado,
            grupo,
            materia,
            escolaridad,
            progreso_tareas,
            progreso_temas,
            progreso_foros,
            progreso_recursos,
            horas_respuesta,
            minutos_respuesta,
            conversaciones_pendientes
        FROM `dashboard-app-lbs.dashboard_dataset.vista_dashboard_maestra`
        """
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        st.error(f"Error de conexión con BigQuery: {e}")
        return pd.DataFrame() # Retorna vacío si falla

# Cargar datos
df_original = get_data()

if df_original.empty:
    st.stop() # Detiene la app si no hay datos

# -----------------------------------------------------------------------------
# 3. FILTROS (Replica de tu barra superior)
# -----------------------------------------------------------------------------
with st.container():
    st.image("https://via.placeholder.com/150x50?text=Logo+LBS+", width=150) # Pon tu logo aquí si tienes URL
    st.markdown("### Reporte de estadísticas de app LBS+")
    
    # Creamos 2 filas de filtros para que se vea limpio
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    col_f5, col_f6, col_f7, col_btn = st.columns(4)

    # Lógica de filtrado en cascada (Simple)
    with col_f1:
        selected_profesor = st.multiselect("Profesor", options=df_original['profesor'].unique())
    with col_f2:
        selected_campus = st.multiselect("Campus", options=df_original['campus'].unique())
    with col_f3:
        selected_escolaridad = st.multiselect("Escolaridad", options=df_original['escolaridad'].unique())
    with col_f4:
        selected_grado = st.multiselect("Grado", options=df_original['grado'].unique())
    
    with col_f5:
        selected_grupo = st.multiselect("Grupo", options=df_original['grupo'].unique())
    with col_f6:
        selected_materia = st.multiselect("Materia", options=df_original['materia'].unique())
    with col_f7:
        selected_periodo = st.multiselect("Periodo", options=df_original['periodo'].unique())
    
    with col_btn:
        st.write("") # Espacio
        if st.button("Borrar Filtros", type="primary"):
            st.rerun()

    # APLICAR FILTROS
    df_filtered = df_original.copy()
    if selected_profesor: df_filtered = df_filtered[df_filtered['profesor'].isin(selected_profesor)]
    if selected_campus: df_filtered = df_filtered[df_filtered['campus'].isin(selected_campus)]
    if selected_escolaridad: df_filtered = df_filtered[df_filtered['escolaridad'].isin(selected_escolaridad)]
    if selected_grado: df_filtered = df_filtered[df_filtered['grado'].isin(selected_grado)]
    if selected_grupo: df_filtered = df_filtered[df_filtered['grupo'].isin(selected_grupo)]
    if selected_materia: df_filtered = df_filtered[df_filtered['materia'].isin(selected_materia)]
    if selected_periodo: df_filtered = df_filtered[df_filtered['periodo'].isin(selected_periodo)]

# -----------------------------------------------------------------------------
# 4. FUNCIÓN DE SEMÁFORO (GAUGE CHART)
# -----------------------------------------------------------------------------
def plot_gauge(value, title):
    # Reglas: Rojo < 0.5, Amarillo 0.5-0.85, Verde > 0.85
    color = "#28a745" # Verde por defecto
    if value < 0.5:
        color = "#dc3545" # Rojo
    elif value < 0.85:
        color = "#ffc107" # Amarillo

    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value * 100, # Convertir a porcentaje visual
        number = {'suffix': "%", 'font': {'size': 24}},
        title = {'text': title, 'font': {'size': 18}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 100], 'color': '#f0f2f6'} # Fondo gris suave
            ],
        }
    ))
    fig.update_layout(height=180, margin=dict(l=10, r=10, t=30, b=10))
    return fig

# -----------------------------------------------------------------------------
# 5. DASHBOARD PRINCIPAL
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown(f"<h3 style='text-align: center;'>Vista General: Todos los campus ({len(df_filtered)} registros)</h3>", unsafe_allow_html=True)

# CALCULAR PROMEDIOS GENERALES
avg_tareas = df_filtered['progreso_tareas'].mean()
avg_foros = df_filtered['progreso_foros'].mean()
avg_recursos = df_filtered['progreso_recursos'].mean()
avg_temas = df_filtered['progreso_temas'].mean()

# MOSTRAR 4 TARJETAS DE KPIs (Semáforos)
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1: st.plotly_chart(plot_gauge(avg_tareas, "Tareas"), use_container_width=True)
with kpi2: st.plotly_chart(plot_gauge(avg_foros, "Foros"), use_container_width=True)
with kpi3: st.plotly_chart(plot_gauge(avg_recursos, "Recursos"), use_container_width=True)
with kpi4: st.plotly_chart(plot_gauge(avg_temas, "Temas"), use_container_width=True)

# -----------------------------------------------------------------------------
# 6. TABLA INTERACTIVA (EL BOTÓN EN LA FILA)
# -----------------------------------------------------------------------------
col_tabla, col_metrics_side = st.columns([3, 1])

with col_tabla:
    st.subheader("Lista de profesores (Selecciona uno 👇)")
    
    # Agrupar datos por Profesor y Campus (Como en tu Looker)
    df_display = df_filtered.groupby(['profesor', 'campus'])[[
        'progreso_tareas', 'progreso_recursos', 'progreso_temas', 'progreso_foros'
    ]].mean().reset_index()

    # Configurar columnas para que se vean bonitas (Porcentajes)
    column_config = {
        "progreso_tareas": st.column_config.ProgressColumn("Tareas", format="%.1f%%", min_value=0, max_value=1),
        "progreso_recursos": st.column_config.ProgressColumn("Recursos", format="%.1f%%", min_value=0, max_value=1),
        "progreso_temas": st.column_config.ProgressColumn("Temas", format="%.1f%%", min_value=0, max_value=1),
        "progreso_foros": st.column_config.ProgressColumn("Foros", format="%.1f%%", min_value=0, max_value=1),
    }

    # LA MAGIA: selection_mode='single-row'
    selection = st.dataframe(
        df_display,
        use_container_width=True,
        column_config=column_config,
        hide_index=True,
        on_select="rerun", # Recarga la app cuando seleccionan
        selection_mode="single-row"
    )

with col_metrics_side:
    st.subheader("Tiempo Respuesta")
    # Calculamos promedios de respuesta
    horas_prom = df_filtered['horas_respuesta'].mean()
    min_prom = df_filtered['minutos_respuesta'].mean()
    pendientes = df_filtered['conversaciones_pendientes'].sum()

    st.metric(label="En horas", value=f"{horas_prom:.1f} h")
    st.metric(label="En minutos", value=f"{min_prom:.0f} min")
    st.metric(label="Conversaciones pendientes", value=f"{pendientes}")

# -----------------------------------------------------------------------------
# 7. VISTA DE DETALLE (SE ACTIVA AL SELECCIONAR FILA)
# -----------------------------------------------------------------------------
if selection.selection.rows:
    selected_index = selection.selection.rows[0]
    profesor_seleccionado = df_display.iloc[selected_index]['profesor']
    campus_seleccionado = df_display.iloc[selected_index]['campus']

    st.markdown("---")
    st.info(f"🔍 Viendo detalle de: **{profesor_seleccionado}** ({campus_seleccionado})")
    
    # Aquí puedes mostrar gráficas específicas de ese profesor
    # Filtramos el DF original solo para este profe
    df_profe = df_original[df_original['profesor'] == profesor_seleccionado]
    
    # Ejemplo: Mostrar desglose por materias
    st.write("Desglose por Materias:")
    st.dataframe(
        df_profe[['materia', 'grupo', 'progreso_tareas', 'conversaciones_pendientes']],
        use_container_width=True,
        column_config={
            "progreso_tareas": st.column_config.ProgressColumn("Avance", format="%.1f%%", min_value=0, max_value=1)
        }
    )
    
    # Botón para cerrar detalle
    if st.button("Cerrar Detalle"):
        st.rerun()