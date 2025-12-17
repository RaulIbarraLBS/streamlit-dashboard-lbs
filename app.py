import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode

# Configuración de la página
st.set_page_config(
    layout="wide", 
    page_title="Analítica LBS+",
    initial_sidebar_state="collapsed"
)

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
    /* FORZAR FONDO BLANCO */
    .stApp {
        background-color: #F5F5F5 !important;
    }
    
    [data-testid="stAppViewContainer"] {
        background-color: #F5F5F5 !important;
    }
    
    [data-testid="stHeader"] {
        background-color: #FFFFFF !important;
    }
    
    /* Forzar textos oscuros */
    .stApp, .stApp * {
        color: #333 !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Reducir padding superior */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1500px !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    /* Métricas más compactas */
    div[data-testid="stMetric"] {
        background-color: white !important;
        border: 1px solid #d0d0d0 !important;
        border-radius: 12px !important;
        padding: 16px 12px !important;
        text-align: center !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08) !important;
    }
    
    div[data-testid="stMetric"] label {
        font-size: 13px !important;
        font-weight: 400 !important;
        color: #666 !important;
    }
    
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 38px !important;
        font-weight: 400 !important;
        color: #333 !important;
    }

    /* Botones */
    div.stButton > button {
        background-color: #5F6B75 !important;
        color: white !important;
        border: none !important;
        border-radius: 24px !important;
        padding: 10px 28px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    
    div.stButton > button p {
        color: white !important;
    }
    
    div.stButton > button:hover {
        background-color: #4b545c !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
    }
    
    /* Filtros multiselect - MÁS CLAROS */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1px solid #d0d0d0 !important;
        min-height: 42px !important;
        color: #333 !important;
    }
    
    /* Placeholder visible */
    div[data-baseweb="select"] input::placeholder {
        color: #666 !important;
        opacity: 1 !important;
    }
    
    /* Texto dentro del input */
    div[data-baseweb="select"] input {
        color: #333 !important;
        background-color: white !important;
    }
    
    /* Chips seleccionados - claros y legibles */
    div[data-baseweb="select"] span[data-baseweb="tag"] {
        background-color: #e3f2fd !important;
        color: #1976d2 !important;
        border: 1px solid #90caf9 !important;
        border-radius: 16px !important;
        padding: 4px 12px !important;
        font-size: 13px !important;
    }
    
    /* Botón X en chips */
    div[data-baseweb="select"] span[data-baseweb="tag"] svg {
        fill: #1976d2 !important;
    }
    
    /* Dropdown menu */
    ul[role="listbox"] {
        background-color: white !important;
        border: 1px solid #d0d0d0 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        padding: 8px 0 !important;
    }
    
    li[role="option"] {
        background-color: white !important;
        color: #333 !important;
        padding: 10px 16px !important;
    }
    
    li[role="option"]:hover {
        background-color: #f5f5f5 !important;
    }
    
    li[role="option"][aria-selected="true"] {
        background-color: #e3f2fd !important;
        color: #1976d2 !important;
        font-weight: 500 !important;
    }
    
    /* Checkmarks en opciones seleccionadas */
    li[role="option"][aria-selected="true"]::before {
        content: "✓ ";
        margin-right: 8px;
        color: #1976d2;
        font-weight: bold;
    }
    
    /* Títulos */
    h1 {
        font-size: 28px !important;
        font-weight: 700 !important;
        margin-bottom: 1rem !important;
        color: #333 !important;
    }
    
    h3 {
        font-size: 18px !important;
        font-weight: 700 !important;
        margin: 1rem 0 0.5rem 0 !important;
        color: #333 !important;
    }
    
    h4 {
        font-size: 16px !important;
        font-weight: 700 !important;
        color: #5F6B75 !important;
    }
    
    /* Labels de filtros VISIBLES */
    label[data-testid="stWidgetLabel"] {
        font-size: 13px !important;
        color: #444 !important;
        font-weight: 500 !important;
    }
    
    /* Caption */
    .stCaption {
        color: #666 !important;
    }
    
    /* DataFrame */
    [data-testid="stDataFrame"] {
        background-color: white !important;
        border: 1px solid #d0d0d0 !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08) !important;
    }
    
    /* Gráficas Plotly */
    div[data-testid="stPlotlyChart"] > div {
        border-radius: 12px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        overflow: hidden !important;
        background-color: white !important;
    }
    
    /* Spinner de carga mejorado */
    div[data-testid="stSpinner"] > div {
        border-color: #1976d2 !important;
    }
    
    div[data-testid="stSpinner"] {
        text-align: center;
        padding: 3rem;
    }
    
    div[data-testid="stStatusWidget"] {
        background-color: white !important;
        padding: 2rem !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES ---
@st.cache_resource
def get_bigquery_client():
    """Establece conexión a BigQuery"""
    try:
        key_dict = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(key_dict)
        client = bigquery.Client(credentials=creds, project=key_dict["project_id"])
        return client
    except Exception as e:
        st.error(f"Error conectando a BigQuery: {e}")
        return None

@st.cache_data(ttl=300)
def get_data():
    """Carga datos de la vista maestra"""
    try:
        client = get_bigquery_client()
        if client is None:
            return pd.DataFrame()
        
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
        
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

def get_actividades_reales(profesores: list, tipo_actividad: str, periodos: list = None):
    """Obtiene datos REALES de actividades de BigQuery"""
    try:
        client = get_bigquery_client()
        if client is None or not profesores:
            return pd.DataFrame()
        
        # Convertir lista de profesores a formato SQL
        profesores_str = "', '".join(profesores)
        
        # Construir filtro de fecha/periodo
        if periodos and len(periodos) > 0:
            # Si hay periodo(s) seleccionado(s), usar esos periodos completos
            periodos_str = "', '".join(periodos)
            periodo_filter = f"AND periodo IN ('{periodos_str}')"
            date_filter = ""
        else:
            # Si no hay periodo, limitar a últimos 30 días
            periodo_filter = ""
            date_filter = "AND fecha_actividad >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)"
        
        query = f"""
        SELECT 
            fecha_actividad,
            COUNT(*) as cantidad
        FROM `dashboard-app-lbs.dashboard_dataset.reporte_tareas_completo`
        WHERE profesor IN ('{profesores_str}')
            AND tipo_actividad = '{tipo_actividad}'
            {date_filter}
            {periodo_filter}
        GROUP BY fecha_actividad
        ORDER BY fecha_actividad
        """
        
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        st.error(f"Error obteniendo actividades: {e}")
        return pd.DataFrame()

def get_gauge_color(value):
    """Determina color del gauge"""
    if value >= 0.85:
        return "#4CD07D"  # Verde
    elif value >= 0.50:
        return "#FFC845"  # Amarillo
    else:
        return "#dc3545"  # Rojo

def plot_gauge(value, title):
    """Crea gauge semicircular"""
    color = get_gauge_color(value)
    
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

def plot_activity_timeline(profesores: list, tipo_actividad: str = 'Tarea', periodos: list = None):
    """Crea gráfica de BARRAS de actividades con datos REALES"""
    
    # Si no hay profesores, mostrar mensaje
    if not profesores:
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
    
    # Obtener datos reales
    df_actividades = get_actividades_reales(profesores, tipo_actividad, periodos)
    
    # Si no hay datos
    if df_actividades.empty:
        fig = go.Figure()
        mensaje = f"No hay datos de {tipo_actividad}s"
        if periodos and len(periodos) > 0:
            mensaje += f" para el periodo seleccionado"
        else:
            mensaje += " en los últimos 30 días"
            
        fig.add_annotation(
            text=mensaje,
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
    
    # Crear gráfica DE BARRAS (MODIFICADO)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_actividades['fecha_actividad'],
        y=df_actividades['cantidad'],
        marker_color='#5F6B75', # Mismo color gris
        name='Actividades',
        hovertemplate='<b>%{x|%d %b}</b><br>Cantidad: %{y}<extra></extra>'
    ))
    
    max_cantidad = df_actividades['cantidad'].max() if not df_actividades.empty else 10
    
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
            tickangle=-45 # Inclinado para que las barras no se amontonen con las etiquetas
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            title='Cantidad',
            range=[0, max_cantidad * 1.1]
        ),
        showlegend=False,
        font={'family': "Arial, sans-serif", 'size': 11},
        hovermode='x unified'
    )
    
    return fig

# ==================== INICIALIZACIÓN ====================

if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'dashboard'

# Limpiar filtro de profesor si se solicita
if "clear_profesor" in st.query_params:
    st.session_state['filter_profesor'] = []
    st.query_params.clear()

# Aplicar selección temporal
if '_temp_selected_profs' in st.session_state and st.session_state['_temp_selected_profs']:
    st.session_state['filter_profesor'] = st.session_state['_temp_selected_profs']
    del st.session_state['_temp_selected_profs']

# Inicializar filtros
filter_keys = ['filter_profesor', 'filter_campus', 'filter_escolaridad', 
               'filter_grado', 'filter_grupo', 'filter_materia', 'filter_periodo']

for key in filter_keys:
    if key not in st.session_state:
        st.session_state[key] = []

# ==================== CARGAR DATOS ====================

with st.spinner("🔄 Cargando datos del dashboard..."):
    df = get_data()

if df.empty:
    st.error("No se pudieron cargar los datos. Verifica la conexión a BigQuery.")
    st.stop()

# Establecer periodo más reciente por defecto SOLO en primera carga
if 'initialized' not in st.session_state:
    periodos_disponibles = sorted(df['periodo'].unique(), reverse=True)
    if periodos_disponibles:
        st.session_state['filter_periodo'] = [periodos_disponibles[0]]
    st.session_state['initialized'] = True

# ==================== HEADER ====================

col_title, col_spacer, col_clear = st.columns([5, 3, 1.1])

with col_title:
    st.markdown("<h1 style='margin-bottom: 0;'>Reporte de estadísticas de app LBS+</h1>", unsafe_allow_html=True)

with col_clear:
    if st.button("Borrar filtros", width="stretch", key="btn_clear"):
        for key in filter_keys:
            st.session_state[key] = []
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ==================== FILTROS DINÁMICOS (CASCADA) ====================

# 1. Definir qué columnas usa cada filtro para mapear
# (Clave del session_state : Nombre real de la columna en el DataFrame)
mapa_filtros = {
    'filter_profesor': 'profesor',
    'filter_campus': 'campus',
    'filter_escolaridad': 'escolaridad',
    'filter_grado': 'grado',
    'filter_grupo': 'grupo',
    'filter_materia': 'materia',
    'filter_periodo': 'periodo'
}

# 2. Función para calcular opciones disponibles
def obtener_opciones_validas(df_total, columna_objetivo, mapa_filtros):
    """
    Filtra el DF basándose en TODAS las selecciones actuales EXCEPTO
    la de la columna que estamos calculando (para no restringirse a sí mismo).
    """
    df_temp = df_total.copy()
    
    for key, col in mapa_filtros.items():
        # Si no es la columna actual Y hay algo seleccionado en ese filtro
        if col != columna_objetivo and st.session_state[key]:
            df_temp = df_temp[df_temp[col].isin(st.session_state[key])]
            
    lista_opciones = sorted(df_temp[columna_objetivo].unique())
    return lista_opciones

# 3. Renderizar Filtros con opciones inteligentes
filter_cols = st.columns(7)

# --- FILTRO PROFESOR ---
with filter_cols[0]:
    # Calculamos opciones válidas según lo que hayas elegido en Campus, Materia, etc.
    opciones = obtener_opciones_validas(df, 'profesor', mapa_filtros)
    
    # TRUCO ANTIGUO ERROR: Asegurar que lo seleccionado siga en las opciones
    # (Si filtras algo que excluye tu selección actual, la agregamos para que no truene)
    seleccion_actual = st.session_state['filter_profesor']
    opciones_finales = sorted(list(set(opciones + seleccion_actual)))
    
    selected_profesor = st.multiselect(
        "Profesor",
        options=opciones_finales,
        default=seleccion_actual,
        placeholder="Profesor",
        label_visibility="collapsed",
        key='filter_profesor'
    )

# --- FILTRO CAMPUS ---
with filter_cols[1]:
    opciones = obtener_opciones_validas(df, 'campus', mapa_filtros)
    seleccion_actual = st.session_state['filter_campus']
    opciones_finales = sorted(list(set(opciones + seleccion_actual)))
    
    selected_campus = st.multiselect(
        "Campus",
        options=opciones_finales,
        default=seleccion_actual,
        placeholder="Campus",
        label_visibility="collapsed",
        key='filter_campus'
    )

# --- FILTRO ESCOLARIDAD ---
with filter_cols[2]:
    opciones = obtener_opciones_validas(df, 'escolaridad', mapa_filtros)
    seleccion_actual = st.session_state['filter_escolaridad']
    opciones_finales = sorted(list(set(opciones + seleccion_actual)))
    
    selected_escolaridad = st.multiselect(
        "Escolaridad",
        options=opciones_finales,
        default=seleccion_actual,
        placeholder="Escolaridad",
        label_visibility="collapsed",
        key='filter_escolaridad'
    )

# --- FILTRO GRADO ---
with filter_cols[3]:
    opciones = obtener_opciones_validas(df, 'grado', mapa_filtros)
    seleccion_actual = st.session_state['filter_grado']
    opciones_finales = sorted(list(set(opciones + seleccion_actual)))
    
    selected_grado = st.multiselect(
        "Grado",
        options=opciones_finales,
        default=seleccion_actual,
        placeholder="Grado",
        label_visibility="collapsed",
        key='filter_grado'
    )

# --- FILTRO GRUPO ---
with filter_cols[4]:
    opciones = obtener_opciones_validas(df, 'grupo', mapa_filtros)
    seleccion_actual = st.session_state['filter_grupo']
    opciones_finales = sorted(list(set(opciones + seleccion_actual)))
    
    selected_grupo = st.multiselect(
        "Grupo",
        options=opciones_finales,
        default=seleccion_actual,
        placeholder="Grupo",
        label_visibility="collapsed",
        key='filter_grupo'
    )

# --- FILTRO MATERIA ---
with filter_cols[5]:
    opciones = obtener_opciones_validas(df, 'materia', mapa_filtros)
    seleccion_actual = st.session_state['filter_materia']
    opciones_finales = sorted(list(set(opciones + seleccion_actual)))
    
    selected_materia = st.multiselect(
        "Materia",
        options=opciones_finales,
        default=seleccion_actual,
        placeholder="Materia",
        label_visibility="collapsed",
        key='filter_materia'
    )

# --- FILTRO PERIODO ---
with filter_cols[6]:
    # El periodo tiene un tratamiento especial para mantener el orden reverso (más nuevo arriba)
    opciones = obtener_opciones_validas(df, 'periodo', mapa_filtros)
    seleccion_actual = st.session_state.get('filter_periodo', [])
    opciones_finales = sorted(list(set(opciones + seleccion_actual)), reverse=True)
    
    selected_periodo = st.multiselect(
        "Periodo",
        options=opciones_finales,
        default=seleccion_actual,
        placeholder="Periodo",
        label_visibility="collapsed",
        key='filter_periodo'
    )

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

# Título campus
campus_titulo = "Todos los campus"
if len(selected_campus) == 1:
    campus_titulo = f"Campus: {selected_campus[0]}"
elif len(selected_campus) > 1:
    campus_titulo = f"{len(selected_campus)} campus seleccionados"

st.markdown(f"<h3 style='text-align: center; color: #888; font-weight: 400;'>{campus_titulo}</h3>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ==================== KPIS ====================

k1, k2, k3, k4 = st.columns(4, gap="medium")

with k1:
    st.markdown("<h4 style='text-align: center; color: #5F6B75; margin-bottom: 0.5rem;'>Tareas</h4>", unsafe_allow_html=True)
    st.plotly_chart(
        plot_gauge(df_filtered['progreso_tareas'].mean(), "Tareas"),
        width="stretch",
        config={'displayModeBar': False},
        key="gauge_tareas"
    )

with k2:
    st.markdown("<h4 style='text-align: center; color: #5F6B75; margin-bottom: 0.5rem;'>Foros</h4>", unsafe_allow_html=True)
    st.plotly_chart(
        plot_gauge(df_filtered['progreso_foros'].mean(), "Foros"),
        width="stretch",
        config={'displayModeBar': False},
        key="gauge_foros"
    )

with k3:
    st.markdown("<h4 style='text-align: center; color: #5F6B75; margin-bottom: 0.5rem;'>Recursos</h4>", unsafe_allow_html=True)
    st.plotly_chart(
        plot_gauge(df_filtered['progreso_recursos'].mean(), "Recursos"),
        width="stretch",
        config={'displayModeBar': False},
        key="gauge_recursos"
    )

with k4:
    st.markdown("<h4 style='text-align: center; color: #5F6B75; margin-bottom: 0.5rem;'>Temas</h4>", unsafe_allow_html=True)
    st.plotly_chart(
        plot_gauge(df_filtered['progreso_temas'].mean(), "Temas"),
        width="stretch",
        config={'displayModeBar': False},
        key="gauge_temas"
    )

st.markdown("<br>", unsafe_allow_html=True)

# ==================== CONTENIDO PRINCIPAL ====================

# Si hay profesor seleccionado: mostrar gráfica
if selected_profesor:
    col_chart_main, col_side = st.columns([3.2, 1], gap="medium")
    
    with col_chart_main:
        st.markdown("<h3 style='margin-bottom: 0.8rem;'>Actividades a lo largo del tiempo</h3>", unsafe_allow_html=True)
        
        col_info, col_tipo, col_btn_clear = st.columns([2, 1.5, 1])
        
        with col_info:
            if len(selected_profesor) == 1:
                st.markdown(f"<p style='font-size: 14px; line-height: 38px;'>📊 Mostrando: <strong>{selected_profesor[0]}</strong></p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='font-size: 14px; line-height: 38px;'>📊 Mostrando: <strong>{len(selected_profesor)} profesores</strong></p>", unsafe_allow_html=True)
        
        with col_tipo:
            # Selector de tipo de actividad
            activity_type = st.selectbox(
                "Tipo",
                ['Tarea', 'Foro', 'Recurso', 'Tema'],
                key="select_activity_type",
                label_visibility="collapsed"
            )
        
        with col_btn_clear:
            if st.button("← Ver todos", key="btn_ver_todos", width="stretch"):
                st.query_params.clear_profesor = "true"
                st.rerun()
        
        # Gráfica con datos REALES usando periodos seleccionados
        st.plotly_chart(
            plot_activity_timeline(selected_profesor, activity_type, selected_periodo),
            width="stretch",
            config={'displayModeBar': False},
            key="chart_actividades"
        )
    
    with col_side:
        st.markdown("<h3 style='text-align: center; font-size: 15px; font-weight: 700; margin-bottom: 0.8rem; margin-top: 0;'>Tiempo promedio para responder mensajes</h3>", unsafe_allow_html=True)
        
        st.metric("En horas", f"{int(df_filtered['horas_respuesta'].mean())}")
        st.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)
        
        st.metric("En minutos", f"{int(df_filtered['minutos_respuesta'].mean())}")
        st.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)
        
        # Calcular conversaciones pendientes correctamente
        # Dividir cada fila por sus duplicadas ANTES de sumar
        df_conversaciones = df_filtered[['conversaciones_pendientes', 'num_filas_duplicadas']].copy()
        df_conversaciones['conversaciones_reales'] = df_conversaciones['conversaciones_pendientes'] / df_conversaciones['num_filas_duplicadas']
        conversaciones_reales = int(df_conversaciones['conversaciones_reales'].sum())
        st.metric("Conversaciones pendientes", f"{conversaciones_reales}")

# Sin profesor: mostrar tabla
else:
    col_table, col_side = st.columns([3.2, 1], gap="medium")
    
    with col_table:
        st.markdown("<h3 style='margin-bottom: 0.8rem;'>Lista de profesores</h3>", unsafe_allow_html=True)
        st.caption("Selecciona uno o más profesores para ver sus actividades")
        
        # Preparar datos
        df_display = df_filtered.groupby(['profesor', 'campus']).agg({
            'progreso_tareas': 'mean',
            'progreso_recursos': 'mean',
            'progreso_temas': 'mean',
            'progreso_foros': 'mean'
        }).reset_index()
        
        df_display['Tareas'] = (df_display['progreso_tareas'] * 100).round(0).astype(int).astype(str) + ' %'
        df_display['Recursos'] = (df_display['progreso_recursos'] * 100).round(0).astype(int).astype(str) + ' %'
        df_display['Temas'] = (df_display['progreso_temas'] * 100).round(0).astype(int).astype(str) + ' %'
        df_display['Foros'] = (df_display['progreso_foros'] * 100).round(0).astype(int).astype(str) + ' %'
        
        df_display = df_display.rename(columns={
            'profesor': 'Profesor',
            'campus': 'Campus'
        })
        
        df_display.insert(0, 'Seleccionar', False)
        df_display = df_display[['Seleccionar', 'Profesor', 'Campus', 'Tareas', 'Recursos', 'Temas', 'Foros']]
        
        # Configurar AgGrid
        gb = GridOptionsBuilder.from_dataframe(df_display)
        gb.configure_selection(
            selection_mode='multiple',
            use_checkbox=True,
            header_checkbox=False,
            pre_selected_rows=[],
            rowMultiSelectWithClick=False,
            suppressRowDeselection=False
        )
        gb.configure_column("Seleccionar", hide=True)
        gb.configure_column("Profesor", checkboxSelection=True, headerCheckboxSelection=False, width=280)
        gb.configure_column("Campus", width=200)
        gb.configure_column("Tareas", width=100)
        gb.configure_column("Recursos", width=100)
        gb.configure_column("Temas", width=100)
        gb.configure_column("Foros", width=100)
        gb.configure_default_column(resizable=True, filterable=False, sortable=True, editable=False)
        gb.configure_grid_options(
            domLayout='normal',
            enableRangeSelection=False,
            rowHeight=42,
            headerHeight=45,
            suppressRowClickSelection=True
        )
        
        grid_options = gb.build()
        
        # Estilos personalizados estilo Looker Studio
        custom_css = {
            ".ag-root-wrapper": {
                "border": "1px solid #d0d0d0",
                "border-radius": "8px",
                "overflow": "hidden"
            },
            ".ag-header": {
                "background-color": "#6B7680",
                "border-bottom": "1px solid #5a6269"
            },
            ".ag-header-cell": {
                "background-color": "#6B7680",
                "color": "white",
                "font-weight": "600",
                "font-size": "13px",
                "border": "none",
                "padding": "12px"
            },
            ".ag-row": {
                "border": "none"
            },
            ".ag-row-odd": {
                "background-color": "#FFFFFF"
            },
            ".ag-row-even": {
                "background-color": "#F8F9FA"
            },
            ".ag-cell": {
                "color": "#5F6368",
                "font-size": "13px",
                "border": "none",
                "line-height": "42px"
            },
            ".ag-row-hover": {
                "background-color": "#E8F4F8 !important"
            },
            ".ag-row-selected": {
                "background-color": "#D4E9F7 !important"
            }
        }
        
        # Renderizar tabla
        grid_response = AgGrid(
            df_display,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=True,
            theme='alpine',
            custom_css=custom_css,
            height=280,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=False
        )
        
        # Obtener seleccionados
        selected_rows = grid_response['selected_rows']
        selected_from_table = []
        
        if isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty:
            selected_from_table = selected_rows['Profesor'].tolist()
        elif isinstance(selected_rows, list) and len(selected_rows) > 0:
            selected_from_table = [row['Profesor'] for row in selected_rows if 'Profesor' in row]
        
        # Botón - Centrado debajo de la tabla
        st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
        
        if len(selected_from_table) > 0:
            col_info, col_btn = st.columns([2, 1])
            with col_info:
                st.markdown(f"<p style='font-size: 13px; color: #666; line-height: 38px;'>{len(selected_from_table)} profesor{'es' if len(selected_from_table) > 1 else ''} seleccionado{'s' if len(selected_from_table) > 1 else ''}</p>", unsafe_allow_html=True)
            with col_btn:
                if st.button("Ver actividades", key="btn_ver_actividades", width="stretch", type="primary"):
                    # Usar session state temporal que se aplica ANTES de crear widgets
                    st.session_state['_temp_selected_profs'] = selected_from_table
                    st.rerun()
        else:
            st.button("Seleccione uno o más profesores", key="btn_ver_actividades_disabled", width="stretch", disabled=True)
    
    with col_side:
        st.markdown("<h3 style='text-align: center; font-size: 15px; font-weight: 700; margin-bottom: 0.8rem; margin-top: 0;'>Tiempo promedio para responder mensajes</h3>", unsafe_allow_html=True)
        
        st.metric("En horas", f"{int(df_filtered['horas_respuesta'].mean())}")
        st.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)
        
        st.metric("En minutos", f"{int(df_filtered['minutos_respuesta'].mean())}")
        st.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)
        
        # Calcular conversaciones pendientes correctamente
        # Dividir cada fila por sus duplicadas ANTES de sumar
        df_conversaciones = df_filtered[['conversaciones_pendientes', 'num_filas_duplicadas']].copy()
        df_conversaciones['conversaciones_reales'] = df_conversaciones['conversaciones_pendientes'] / df_conversaciones['num_filas_duplicadas']
        conversaciones_reales = int(df_conversaciones['conversaciones_reales'].sum())
        st.metric("Conversaciones pendientes", f"{conversaciones_reales}")