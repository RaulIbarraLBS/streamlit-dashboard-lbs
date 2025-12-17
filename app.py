import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(layout="wide", page_title="Analítica LBS+")

# CSS personalizado para limpiar la interfaz
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #f8f9fa; }
    div[data-testid="metric-container"] {
        background-color: white;
        border-radius: 8px;
        padding: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def get_data():
    """Establece conexión a BigQuery usando secretos de Streamlit."""
    try:
        # Cargar credenciales desde secrets.toml explícitamente
        key_dict = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(key_dict)
        
        # Inicializar cliente con el ID del proyecto correcto
        client = bigquery.Client(credentials=creds, project=key_dict["project_id"])
        
        query = """
        SELECT 
            profesor, campus, periodo, grado, grupo, materia, escolaridad,
            progreso_tareas, progreso_temas, progreso_foros, progreso_recursos,
            horas_respuesta, minutos_respuesta, conversaciones_pendientes
        FROM `dashboard-app-lbs.dashboard_dataset.vista_dashboard_maestra`
        """
        return client.query(query).to_dataframe()
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

def plot_gauge(value, title):
    """Genera gráfico de medidor con lógica de semáforo."""
    color = "#28a745"  # Verde
    if value < 0.5:
        color = "#dc3545"  # Rojo
    elif value < 0.85:
        color = "#ffc107"  # Amarillo

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value * 100,
        number={'suffix': "%", 'font': {'size': 24}},
        title={'text': title, 'font': {'size': 18}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#e6e6e6",
            'steps': [{'range': [0, 100], 'color': '#f8f9fa'}],
        }
    ))
    fig.update_layout(height=180, margin=dict(l=10, r=10, t=30, b=10))
    return fig

# Cargar datos
df = get_data()

if df.empty:
    st.stop()

# Encabezado
st.title("Reporte de estadísticas LBS+")

# Filtros laterales
with st.container():
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        selected_profesor = st.multiselect("Profesor", options=df['profesor'].unique())
    with col2:
        selected_campus = st.multiselect("Campus", options=df['campus'].unique())
    with col3:
        selected_materia = st.multiselect("Materia", options=df['materia'].unique())
    with col4:
        if st.button("Limpiar Filtros", type="primary"):
            st.rerun()

    # Lógica de filtrado
    df_filtered = df.copy()
    if selected_profesor: 
        df_filtered = df_filtered[df_filtered['profesor'].isin(selected_profesor)]
    if selected_campus: 
        df_filtered = df_filtered[df_filtered['campus'].isin(selected_campus)]
    if selected_materia: 
        df_filtered = df_filtered[df_filtered['materia'].isin(selected_materia)]

st.divider()

# Sección de KPIs
st.subheader(f"Vista General ({len(df_filtered)} registros)")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1: st.plotly_chart(plot_gauge(df_filtered['progreso_tareas'].mean(), "Tareas"), use_container_width=True)
with kpi2: st.plotly_chart(plot_gauge(df_filtered['progreso_foros'].mean(), "Foros"), use_container_width=True)
with kpi3: st.plotly_chart(plot_gauge(df_filtered['progreso_recursos'].mean(), "Recursos"), use_container_width=True)
with kpi4: st.plotly_chart(plot_gauge(df_filtered['progreso_temas'].mean(), "Temas"), use_container_width=True)

# Área principal de interacción
col_table, col_metrics = st.columns([3, 1])

with col_table:
    st.write("### Desglose por Profesor")
    
    # Agrupación de datos para la tabla
    df_display = df_filtered.groupby(['profesor', 'campus'])[[
        'progreso_tareas', 'progreso_recursos', 'progreso_temas', 'progreso_foros'
    ]].mean().reset_index()

    # Configuración de columnas
    column_config = {
        "progreso_tareas": st.column_config.ProgressColumn("Tareas", format="%.1f%%", min_value=0, max_value=1),
        "progreso_recursos": st.column_config.ProgressColumn("Recursos", format="%.1f%%", min_value=0, max_value=1),
        "progreso_temas": st.column_config.ProgressColumn("Temas", format="%.1f%%", min_value=0, max_value=1),
        "progreso_foros": st.column_config.ProgressColumn("Foros", format="%.1f%%", min_value=0, max_value=1),
    }

    selection = st.dataframe(
        df_display,
        use_container_width=True,
        column_config=column_config,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )

with col_metrics:
    st.write("### Respuesta")
    st.metric("Promedio (Horas)", f"{df_filtered['horas_respuesta'].mean():.1f} h")
    st.metric("Promedio (Minutos)", f"{df_filtered['minutos_respuesta'].mean():.0f} min")
    st.metric("Pendientes", f"{df_filtered['conversaciones_pendientes'].sum()}")

# Vista detallada (Drill-down)
if selection.selection.rows:
    idx = selection.selection.rows[0]
    selected_row = df_display.iloc[idx]
    
    st.markdown("---")
    st.info(f"Detalle: **{selected_row['profesor']}** - {selected_row['campus']}")
    
    # Filtrar datos específicos para el detalle seleccionado
    detail_mask = (df['profesor'] == selected_row['profesor']) & (df['campus'] == selected_row['campus'])
    df_detail = df[detail_mask]
    
    st.dataframe(
        df_detail[['grupo', 'materia', 'progreso_tareas', 'conversaciones_pendientes']],
        use_container_width=True,
        column_config={
            "progreso_tareas": st.column_config.ProgressColumn("Avance Tareas", format="%.1f%%")
        }
    )
    
    if st.button("Cerrar detalle"):
        st.rerun()