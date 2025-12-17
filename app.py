import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Configuración de la página
st.set_page_config(
    layout="wide", 
    page_title="Analítica LBS+",
    initial_sidebar_state="collapsed"
)

# --- CSS PERSONALIZADO PARA IGUALAR LOOKER ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .stApp { 
        background-color: #f8f9fa !important;
    }
    
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    .stApp { 
        background-color: #f8f9fa !important;
    }
    
    /* Reducir padding superior y configurar ancho máximo */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1500px !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    /* Estilo de las tarjetas laterales (blancas con borde suave) */
    div[data-testid="stMetric"] {
        background-color: white !important;
        border: 1px solid #d0d0d0 !important;
        border-radius: 12px !important;
        padding: 20px !important;
        text-align: center !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08) !important;
    }
    
    /* Etiquetas de métricas */
    div[data-testid="stMetric"] label {
        font-size: 13px !important;
        color: #888 !important;
        font-weight: 400 !important;
        text-transform: none !important;
    }
    
    /* Valores de métricas */
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 42px !important;
        font-weight: 400 !important;
        color: #333 !important;
    }

    /* Encabezado de tabla - más claro y suave */
    thead tr th {
        background-color: #E8EAED !important;
        color: #5F6B75 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 14px 12px !important;
        border: none !important;
        text-align: left !important;
        letter-spacing: 0.3px !important;
    }
    
    /* Celdas de tabla - texto más oscuro para mejor contraste */
    tbody tr td {
        font-size: 13px !important;
        padding: 12px 12px !important;
        color: #333 !important;
        border: none !important;
        font-weight: 400 !important;
    }
    
    /* Todas las filas con fondo blanco */
    tbody tr td {
        background-color: #FFFFFF !important;
    }
    
    /* Hover en filas de tabla - azul muy claro */
    tbody tr:hover td {
        background-color: #F0F7FA !important;
        cursor: pointer;
    }
    
    /* Primera columna (checkbox) más estrecha */
    tbody tr td:first-child,
    thead tr th:first-child {
        width: 50px !important;
        text-align: center !important;
    }
    
    /* Contenedor de dataframe con sombra y BORDE VISIBLE */
    [data-testid="stDataFrame"] {
        background-color: white !important;
        border: 1px solid #d0d0d0 !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08) !important;
    }
    
    /* Forzar que el dataframe sea visible */
    [data-testid="stDataFrame"] > div {
        background-color: white !important;
    }
    
    /* Asegurar que la tabla tenga fondo blanco */
    table {
        background-color: white !important;
    }

    /* Botones estilo Looker */
    div.stButton > button {
        background-color: #5F6B75 !important;
        border: none !important;
        border-radius: 24px !important;
        padding: 10px 28px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    
    div.stButton > button:hover {
        background-color: #4b545c !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
    }
    
    /* ==================== FILTROS MULTISELECT ==================== */
    
    /* Contenedor principal del multiselect - fondo blanco con borde gris */
    div[data-baseweb="select"] > div {
        background-color: white !important;
        border-radius: 24px !important;
        border: 1px solid #d0d0d0 !important;
        color: #666 !important;
        min-height: 42px !important;
    }
    
    /* Texto del placeholder */
    div[data-baseweb="select"] input {
        color: #666 !important;
    }
    
    /* Dropdown menu (la lista de opciones) */
    ul[role="listbox"] {
        background-color: white !important;
        border: 1px solid #d0d0d0 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }
    
    /* Opciones individuales en el dropdown */
    li[role="option"] {
        background-color: white !important;
        color: #333 !important;
        padding: 10px 16px !important;
    }
    
    li[role="option"]:hover {
        background-color: #f0f0f0 !important;
    }
    
    /* Opciones seleccionadas en el dropdown (con checkmark) */
    li[role="option"][aria-selected="true"] {
        background-color: #e8f4f8 !important;
    }
    
    /* CHIPS de elementos seleccionados - GRIS CLARO */
    span[data-baseweb="tag"] {
        background-color: #e8e8e8 !important;
        color: #333 !important;
        border: 1px solid #d0d0d0 !important;
        border-radius: 16px !important;
        padding: 4px 12px !important;
        font-size: 13px !important;
    }
    
    /* Botón X en los chips */
    span[data-baseweb="tag"] svg {
        fill: #666 !important;
    }
    
    span[data-baseweb="tag"]:hover {
        background-color: #d8d8d8 !important;
    }
    
    /* Ocultar chips individuales cuando hay múltiples seleccionados */
    div[data-baseweb="select"] > div > div:first-child {
        max-width: 100%;
        overflow: hidden;
    }
    
    /* Texto dentro del multiselect */
    div[data-baseweb="select"] span {
        color: #666 !important;
    }
    
    /* Íconos de dropdown */
    div[data-baseweb="select"] svg {
        fill: #666 !important;
    }
    
    /* ==================== FIN FILTROS ==================== */
    
    /* Títulos */
    h1 {
        color: #333 !important;
        font-size: 22px !important;
        font-weight: 400 !important;
        margin-bottom: 1rem !important;
    }
    
    h3 {
        color: #888 !important;
        font-size: 18px !important;
        font-weight: 400 !important;
        margin: 1rem 0 !important;
    }
    
    h4 {
        color: #5F6B75 !important;
        font-size: 15px !important;
        font-weight: 400 !important;
    }
    
    /* Contenedor de dataframe */
    [data-testid="stDataFrame"] {
        background-color: white !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    
    /* Ocultar toolbar de plotly */
    .modebar {
        display: none !important;
    }
    
    /* Labels de los filtros */
    label[data-testid="stWidgetLabel"] {
        font-size: 13px !important;
        color: #666 !important;
        font-weight: 400 !important;
    }
    
    /* Sombra para los KPIs (gráficos plotly) */
    div[data-testid="stPlotlyChart"] > div {
        border-radius: 12px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        overflow: hidden !important;
        background-color: white !important;
    }
</style>
""", unsafe_allow_html=True)

def format_selection_text(selected_items, item_type="items"):
    """Formatea el texto de selección para mostrar 'n seleccionados' en lugar de chips."""
    if not selected_items:
        return None
    elif len(selected_items) == 1:
        return selected_items[0]
    else:
        return f"{len(selected_items)} seleccionados"

# --- FUNCIONES ---
@st.cache_data(ttl=300)
def get_data():
    """Establece conexión a BigQuery usando secretos."""
    try:
        key_dict = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(key_dict)
        client = bigquery.Client(credentials=creds, project=key_dict["project_id"])
        query = """
        SELECT 
            profesor_id,
            profesor,
            campus,
            periodo,
            horas_semana,
            materia,
            grado,
            grupo,
            escolaridad,
            num_filas_duplicadas,
            total_actividades,
            cant_tareas,
            cant_temas,
            cant_foros,
            cant_recursos,
            cumplio_tareas,
            cumplio_temas,
            cumplio_foros,
            cumplio_recursos,
            progreso_tareas,
            progreso_temas,
            progreso_foros,
            progreso_recursos,
            conversaciones_pendientes,
            horas_respuesta,
            minutos_respuesta
        FROM `dashboard-app-lbs.dashboard_dataset.vista_dashboard_maestra`
        """
        return client.query(query).to_dataframe()
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

def plot_gauge(value, title):
    """Genera semáforo estilo gauge semicírculo con los colores exactos de Looker."""
    # Colores extraídos de Looker
    if value >= 0.85:
        color = "#4CD07D"  # Verde
    elif value >= 0.5:
        color = "#FFC845"  # Amarillo
    else:
        color = "#dc3545"  # Rojo

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value * 100,
        number={
            'suffix': " %", 
            'font': {'size': 32, 'color': color, 'family': 'Arial', 'weight': 600}
        },
        gauge={
            'axis': {
                'range': [None, 100], 
                'tickwidth': 0,
                'tickcolor': "white",
                'visible': False
            },
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': "#e9ecef",
            'borderwidth': 0,
            'bordercolor': "white",
            'steps': [
                {'range': [0, 100], 'color': '#e9ecef'}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 0},
                'thickness': 0.75,
                'value': 100
            }
        },
        domain={'x': [0, 1], 'y': [0, 1]}
    ))
    
    fig.update_layout(
        height=140,
        margin=dict(l=20, r=20, t=10, b=10),
        paper_bgcolor='white',
        plot_bgcolor='white',
        font={'family': "Arial, sans-serif"}
    )
    return fig

def plot_activity_timeline(df_filtered, activity_type='Tareas'):
    """Genera gráfica de actividades a lo largo del tiempo (simulada por ahora)."""
    import numpy as np
    from datetime import datetime, timedelta
    
    # Si no hay datos filtrados, retornar gráfica vacía con mensaje
    if df_filtered.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Selecciona un profesor para ver las actividades",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#999")
        )
        fig.update_layout(
            height=350,
            margin=dict(l=40, r=20, t=30, b=40),
            paper_bgcolor='white',
            plot_bgcolor='white',
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False)
        )
        return fig
    
    # Generar datos simulados de actividades por fecha
    # En producción, estos datos vendrían de una columna de fecha en tu base de datos
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Simular conteos basados en el tipo de actividad
    np.random.seed(42)
    counts = np.random.randint(50, 200, size=len(dates))
    
    df_timeline = pd.DataFrame({
        'fecha': dates,
        'count': counts
    })
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_timeline['fecha'],
        y=df_timeline['count'],
        mode='lines',
        fill='tozeroy',
        line=dict(color='#5F6B75', width=2),
        fillcolor='rgba(95, 107, 117, 0.2)',
        name='Actividades'
    ))
    
    fig.update_layout(
        height=350,
        margin=dict(l=40, r=20, t=30, b=60),
        paper_bgcolor='white',
        plot_bgcolor='white',
        xaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            title='',
            tickformat='%d %b',
            tickangle=0
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            title='Cantidad',
            range=[0, df_timeline['count'].max() * 1.1]
        ),
        showlegend=False,
        font={'family': "Arial, sans-serif", 'size': 11}
    )
    
    return fig

# --- LÓGICA PRINCIPAL ---
df = get_data()
if df.empty: 
    st.warning("No se pudieron cargar los datos. Usando datos de ejemplo...")
    # Crear datos de ejemplo con el esquema correcto
    num_rows = 30
    df = pd.DataFrame({
        'profesor_id': range(1, num_rows + 1),
        'profesor': ['ABIGAIL LOYA DOMINGUEZ', 'ABIGAIL RAMIREZ MANZANERA', 'ADIANEZ ARHELY GAMBOA RIVAS'] * 10,
        'campus': ['CID Chihuahua', 'CID Aguascalientes', 'CID Saltillo'] * 10,
        'periodo': ['2025-10'] * num_rows,
        'horas_semana': [5, 4, 3] * 10,
        'materia': ['Matemáticas', 'Español', 'Ciencias'] * 10,
        'grado': ['1°', '2°', '3°'] * 10,
        'grupo': ['A', 'B', 'C'] * 10,
        'escolaridad': ['Primaria'] * num_rows,
        'num_filas_duplicadas': [0] * num_rows,
        'total_actividades': [15, 12, 10] * 10,
        'cant_tareas': [5, 4, 3] * 10,
        'cant_temas': [4, 3, 2] * 10,
        'cant_foros': [3, 2, 3] * 10,
        'cant_recursos': [3, 3, 2] * 10,
        'cumplio_tareas': [1, 1, 0] * 10,
        'cumplio_temas': [1, 0, 0] * 10,
        'cumplio_foros': [1, 0, 1] * 10,
        'cumplio_recursos': [1, 1, 0] * 10,
        'progreso_tareas': [1.0, 1.0, 0.0] * 10,
        'progreso_temas': [1.0, 0.0, 0.0] * 10,
        'progreso_foros': [1.0, 0.0, 1.0] * 10,
        'progreso_recursos': [1.0, 0.5, 0.75] * 10,
        'conversaciones_pendientes': [2, 5, 1] * 10,
        'horas_respuesta': [7.5, 5.2, 9.1] * 10,
        'minutos_respuesta': [406, 350, 500] * 10,
    })

# Inicializar estado de sesión para la vista
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'dashboard'  # 'dashboard' o 'actividades'

# Verificar si se debe limpiar el filtro de profesor
if "clear_profesor" in st.query_params:
    st.session_state['filter_profesor'] = []
    st.query_params.clear()

# Aplicar selección temporal de tabla si existe
if '_temp_selected_profs' in st.session_state and st.session_state['_temp_selected_profs']:
    st.session_state['filter_profesor'] = st.session_state['_temp_selected_profs']
    del st.session_state['_temp_selected_profs']

# Inicializar filtros en session_state si no existen
if 'filter_profesor' not in st.session_state:
    st.session_state['filter_profesor'] = []
if 'filter_campus' not in st.session_state:
    st.session_state['filter_campus'] = []
if 'filter_escolaridad' not in st.session_state:
    st.session_state['filter_escolaridad'] = []
if 'filter_grado' not in st.session_state:
    st.session_state['filter_grado'] = []
if 'filter_grupo' not in st.session_state:
    st.session_state['filter_grupo'] = []
if 'filter_materia' not in st.session_state:
    st.session_state['filter_materia'] = []
if 'filter_periodo' not in st.session_state:
    st.session_state['filter_periodo'] = []

# Header con título y botones
col_title, col_spacer, col_clear = st.columns([5, 3, 1.1])

with col_title:
    st.markdown("<h1 style='margin-bottom: 0;'>Reporte de estadísticas de app LBS+</h1>", unsafe_allow_html=True)

with col_clear:
    if st.button("Borrar filtros", use_container_width=True, key="btn_clear"):
        # Limpiar los valores de los filtros en session_state
        st.session_state['filter_profesor'] = []
        st.session_state['filter_campus'] = []
        st.session_state['filter_escolaridad'] = []
        st.session_state['filter_grado'] = []
        st.session_state['filter_grupo'] = []
        st.session_state['filter_materia'] = []
        st.session_state['filter_periodo'] = []
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# Filtros - Layout más compacto
filter_cols = st.columns([1, 1, 1.1, 0.8, 0.8, 1, 1.3], gap="small")

with filter_cols[0]:
    selected_profesor = st.multiselect(
        "Profesor", 
        df['profesor'].unique(), 
        key='filter_profesor', 
        placeholder="Profesor",
        default=st.session_state['filter_profesor'],
        label_visibility="visible"
    )
    if len(selected_profesor) > 1:
        st.caption(f"✓ {len(selected_profesor)} seleccionados")
    elif len(selected_profesor) == 1:
        st.caption(f"✓ {selected_profesor[0]}")
        
with filter_cols[1]:
    selected_campus = st.multiselect(
        "Campus", 
        df['campus'].unique(), 
        key='filter_campus', 
        placeholder="Campus",
        default=st.session_state['filter_campus'],
        label_visibility="visible"
    )
    if len(selected_campus) > 1:
        st.caption(f"✓ {len(selected_campus)} seleccionados")
    elif len(selected_campus) == 1:
        st.caption(f"✓ {selected_campus[0]}")
        
with filter_cols[2]:
    selected_escolaridad = st.multiselect(
        "Escolaridad", 
        df['escolaridad'].unique(), 
        key='filter_escolaridad', 
        placeholder="Escolaridad",
        default=st.session_state['filter_escolaridad'],
        label_visibility="visible"
    )
    if len(selected_escolaridad) > 1:
        st.caption(f"✓ {len(selected_escolaridad)} seleccionados")
    elif len(selected_escolaridad) == 1:
        st.caption(f"✓ {selected_escolaridad[0]}")
        
with filter_cols[3]:
    selected_grado = st.multiselect(
        "Grado", 
        df['grado'].unique(), 
        key='filter_grado', 
        placeholder="Grado",
        default=st.session_state['filter_grado'],
        label_visibility="visible"
    )
    if len(selected_grado) > 1:
        st.caption(f"✓ {len(selected_grado)} seleccionados")
    elif len(selected_grado) == 1:
        st.caption(f"✓ {selected_grado[0]}")
        
with filter_cols[4]:
    selected_grupo = st.multiselect(
        "Grupo", 
        df['grupo'].unique(), 
        key='filter_grupo', 
        placeholder="Grupo",
        default=st.session_state['filter_grupo'],
        label_visibility="visible"
    )
    if len(selected_grupo) > 1:
        st.caption(f"✓ {len(selected_grupo)} seleccionados")
    elif len(selected_grupo) == 1:
        st.caption(f"✓ {selected_grupo[0]}")
        
with filter_cols[5]:
    selected_materia = st.multiselect(
        "Materia", 
        df['materia'].unique(), 
        key='filter_materia', 
        placeholder="Materia",
        default=st.session_state['filter_materia'],
        label_visibility="visible"
    )
    if len(selected_materia) > 1:
        st.caption(f"✓ {len(selected_materia)} seleccionados")
    elif len(selected_materia) == 1:
        st.caption(f"✓ {selected_materia[0]}")
        
with filter_cols[6]:
    selected_periodo = st.multiselect(
        "Periodo: 2025-10", 
        df['periodo'].unique(), 
        key='filter_periodo', 
        placeholder="Periodo",
        default=st.session_state['filter_periodo'],
        label_visibility="visible"
    )
    if len(selected_periodo) > 1:
        st.caption(f"✓ {len(selected_periodo)} seleccionados")
    elif len(selected_periodo) == 1:
        st.caption(f"✓ {selected_periodo[0]}")

# Aplicar filtros
df_filtered = df.copy()
if selected_profesor: df_filtered = df_filtered[df_filtered['profesor'].isin(selected_profesor)]
if selected_campus: df_filtered = df_filtered[df_filtered['campus'].isin(selected_campus)]
if selected_escolaridad: df_filtered = df_filtered[df_filtered['escolaridad'].isin(selected_escolaridad)]
if selected_grado: df_filtered = df_filtered[df_filtered['grado'].isin(selected_grado)]
if selected_grupo: df_filtered = df_filtered[df_filtered['grupo'].isin(selected_grupo)]
if selected_materia: df_filtered = df_filtered[df_filtered['materia'].isin(selected_materia)]
if selected_periodo: df_filtered = df_filtered[df_filtered['periodo'].isin(selected_periodo)]

st.markdown("<br>", unsafe_allow_html=True)

# Título dinámico del campus
campus_titulo = "Todos los campus"
if len(selected_campus) == 1:
    campus_titulo = f"Campus: {selected_campus[0]}"
elif len(selected_campus) > 1:
    campus_titulo = f"{len(selected_campus)} campus seleccionados"

st.markdown(f"<h3 style='text-align: center; color: #888; font-weight: 400;'>{campus_titulo}</h3>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# --- VISTA CONDICIONAL ---
if st.session_state.view_mode == 'dashboard':
    # KPIs Semáforos con títulos arriba
    k1, k2, k3, k4 = st.columns(4, gap="medium")
    
    with k1: 
        st.markdown("<h4 style='text-align: center; color: #5F6B75; margin-bottom: 0.5rem;'>Tareas</h4>", unsafe_allow_html=True)
        st.plotly_chart(
            plot_gauge(df_filtered['progreso_tareas'].mean(), "Tareas"), 
            use_container_width=True, 
            config={'displayModeBar': False},
            key="gauge_tareas"
        )
    with k2: 
        st.markdown("<h4 style='text-align: center; color: #5F6B75; margin-bottom: 0.5rem;'>Foros</h4>", unsafe_allow_html=True)
        st.plotly_chart(
            plot_gauge(df_filtered['progreso_foros'].mean(), "Foros"), 
            use_container_width=True,
            config={'displayModeBar': False},
            key="gauge_foros"
        )
    with k3: 
        st.markdown("<h4 style='text-align: center; color: #5F6B75; margin-bottom: 0.5rem;'>Recursos</h4>", unsafe_allow_html=True)
        st.plotly_chart(
            plot_gauge(df_filtered['progreso_recursos'].mean(), "Recursos"), 
            use_container_width=True,
            config={'displayModeBar': False},
            key="gauge_recursos"
        )
    with k4: 
        st.markdown("<h4 style='text-align: center; color: #5F6B75; margin-bottom: 0.5rem;'>Temas</h4>", unsafe_allow_html=True)
        st.plotly_chart(
            plot_gauge(df_filtered['progreso_temas'].mean(), "Temas"), 
            use_container_width=True,
            config={'displayModeBar': False},
            key="gauge_temas"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Sección Inferior - Cambia según si hay profesor seleccionado
    if selected_profesor:
        # Vista con gráfica de actividades
        col_chart_main, col_side = st.columns([3.2, 1], gap="medium")
        
        with col_chart_main:
            # Mostrar profesores seleccionados con botón para limpiar
            st.markdown("<h3 style='color: #888; margin-bottom: 0.8rem;'>Actividades a lo largo del tiempo</h3>", unsafe_allow_html=True)
            
            # Info de profesores seleccionados
            col_info, col_btn_clear = st.columns([3, 1])
            with col_info:
                if len(selected_profesor) == 1:
                    st.markdown(f"<p style='color: #666; font-size: 14px;'>📊 Mostrando actividades de: <strong>{selected_profesor[0]}</strong></p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<p style='color: #666; font-size: 14px;'>📊 Mostrando actividades de <strong>{len(selected_profesor)} profesores</strong></p>", unsafe_allow_html=True)
            
            with col_btn_clear:
                if st.button("← Ver todos", key="btn_ver_todos", use_container_width=True):
                    # Usar query params para evitar el error de session_state
                    st.query_params.clear_profesor = "true"
                    st.rerun()
            
            # Selector de tipo de actividad
            activity_type = st.selectbox(
                "Tipo de actividad",
                ['Tareas', 'Temas', 'Foros', 'Recursos'],
                key="select_activity_type",
                label_visibility="collapsed"
            )
            
            # Gráfica de actividades
            st.plotly_chart(
                plot_activity_timeline(df_filtered, activity_type),
                use_container_width=True,
                config={'displayModeBar': False},
                key="chart_actividades_dashboard"
            )
        
        with col_side:
            st.markdown("<h4 style='text-align: center; color: #888; font-size: 13px; font-weight: 400; margin-bottom: 1rem;'>Tiempo promedio para<br>responder mensajes</h4>", unsafe_allow_html=True)
            
            st.metric("En horas", f"{int(df_filtered['horas_respuesta'].mean())}")
            st.markdown("<div style='margin: 0.8rem 0;'></div>", unsafe_allow_html=True)
            
            st.metric("En minutos", f"{int(df_filtered['minutos_respuesta'].mean())}")
            st.markdown("<div style='margin: 0.8rem 0;'></div>", unsafe_allow_html=True)
            
            st.metric("Conversaciones pendientes", f"{int(df_filtered['conversaciones_pendientes'].sum())}")
    
    else:
        # Vista normal con tabla de profesores
        col_table, col_side = st.columns([3.2, 1], gap="medium")

        with col_table:
            st.markdown("<h3 style='color: #888; margin-bottom: 0.8rem;'>Lista de profesores</h3>", unsafe_allow_html=True)
            st.caption("Haz clic en el checkbox para ver actividades del profesor")
            
            # Agrupar y formatear datos
            df_display = df_filtered.groupby(['profesor', 'campus']).agg({
                'progreso_tareas': 'mean',
                'progreso_recursos': 'mean',
                'progreso_temas': 'mean',
                'progreso_foros': 'mean'
            }).reset_index()
            
            # Convertir a porcentajes
            df_display['Tareas'] = (df_display['progreso_tareas'] * 100).round(0).astype(int).astype(str) + ' %'
            df_display['Recursos'] = (df_display['progreso_recursos'] * 100).round(0).astype(int).astype(str) + ' %'
            df_display['Temas'] = (df_display['progreso_temas'] * 100).round(0).astype(int).astype(str) + ' %'
            df_display['Foros'] = (df_display['progreso_foros'] * 100).round(0).astype(int).astype(str) + ' %'
            
            # Renombrar columnas
            df_display = df_display.rename(columns={
                'profesor': 'Profesor',
                'campus': 'Campus'
            })
            
            # Agregar columna de selección
            df_display.insert(0, '✓', False)
            
            # Seleccionar columnas finales
            df_display = df_display[['✓', 'Profesor', 'Campus', 'Tareas', 'Recursos', 'Temas', 'Foros']]
            
            # Usar data_editor para permitir selección con checkbox
            edited_df = st.data_editor(
                df_display,
                use_container_width=True,
                hide_index=True,
                height=280,
                key="tabla_profesores_editor",
                column_config={
                    "✓": st.column_config.CheckboxColumn(
                        "Seleccionar",
                        help="Selecciona para ver actividades",
                        default=False,
                    )
                },
                disabled=["Profesor", "Campus", "Tareas", "Recursos", "Temas", "Foros"]
            )
            
            # Si hay algún profesor seleccionado en la tabla, usar query params para actualizar
            selected_from_table = edited_df[edited_df['✓'] == True]['Profesor'].tolist()
            if selected_from_table and selected_from_table != selected_profesor:
                # Usar session_state con un key diferente para evitar conflictos
                st.session_state['_temp_selected_profs'] = selected_from_table
                st.rerun()

        with col_side:
            st.markdown("<h4 style='text-align: center; color: #888; font-size: 13px; font-weight: 400; margin-bottom: 1rem;'>Tiempo promedio para<br>responder mensajes</h4>", unsafe_allow_html=True)
            
            st.metric("En horas", f"{int(df_filtered['horas_respuesta'].mean())}")
            st.markdown("<div style='margin: 0.8rem 0;'></div>", unsafe_allow_html=True)
            
            st.metric("En minutos", f"{int(df_filtered['minutos_respuesta'].mean())}")
            st.markdown("<div style='margin: 0.8rem 0;'></div>", unsafe_allow_html=True)
            
            st.metric("Conversaciones pendientes", f"{int(df_filtered['conversaciones_pendientes'].sum())}")