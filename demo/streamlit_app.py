"""Aplicación demo de Streamlit para db-agent-sql."""

import streamlit as st
import pandas as pd
import asyncio
import time
from datetime import datetime
from typing import Optional
import logging
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la página
st.set_page_config(
    page_title="Demo del Agente de Consultas a BD",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    
    /* Estilos de la interfaz de chat */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        padding: 1rem;
        max-height: 600px;
        overflow-y: auto;
    }
    
    .user-message {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 1rem;
    }
    
    .user-bubble {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 5px 20px;
        max-width: 70%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        font-size: 1rem;
        line-height: 1.5;
    }
    
    .ai-message {
        display: flex;
        justify-content: flex-start;
        margin-bottom: 1rem;
    }
    
    .ai-bubble {
        background: #f0f2f6;
        color: #262730;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 20px 5px;
        max-width: 70%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        font-size: 1rem;
        line-height: 1.5;
    }
    
    .ai-bubble-content {
        margin-bottom: 0.5rem;
    }
    
    .timestamp {
        font-size: 0.75rem;
        color: #888;
        margin-top: 0.25rem;
    }
    
    .confidence-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    .confidence-high {
        background-color: #d4edda;
        color: #155724;
    }
    
    .confidence-medium {
        background-color: #fff3cd;
        color: #856404;
    }
    
    .confidence-low {
        background-color: #f8d7da;
        color: #721c24;
    }
    
    /* Área de entrada en la parte inferior */
    .chat-input-container {
        position: sticky;
        bottom: 0;
        background: white;
        padding: 1rem;
        border-top: 1px solid #e0e0e0;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Inicializar variables del estado de sesión."""
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'connected' not in st.session_state:
        st.session_state.connected = False
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    if 'current_session' not in st.session_state:
        st.session_state.current_session = None
    if 'schema_cache' not in st.session_state:
        st.session_state.schema_cache = None
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'use_session' not in st.session_state:
        st.session_state.use_session = False
    if 'use_streaming' not in st.session_state:
        st.session_state.use_streaming = False
    if 'is_processing' not in st.session_state:
        st.session_state.is_processing = False


def connect_to_database(**kwargs) -> bool:
    """Conectarse a la base de datos e inicializar el agente usando configuración flexible.
    
    El agente cargará las credenciales desde .env por defecto, con posibles sobrescrituras desde kwargs.
    """
    try:
        from db_agent_sql import DatabaseQueryAgent      #db_agent_sql    db_agent_sql
        
        # Usar from_env() que carga desde .env y permite sobrescrituras
        st.session_state.agent = DatabaseQueryAgent.from_env(
            enable_statistics=True,  # Habilitar estadísticas de consultas
            **kwargs
        )
        
        # Probar conexión
        if st.session_state.agent.connection_manager.test_connection():
            st.session_state.connected = True
            
            # Cargar esquema
            st.session_state.schema_cache = st.session_state.agent.get_schema()
            
            return True
        else:
            st.error("❌ La prueba de conexión falló")
            return False
            
    except Exception as e:
        st.error(f"❌ La conexión falló: {str(e)}")
        logger.error(f"Error de conexión: {e}", exc_info=True)
        return False


def sidebar_config():
    """Renderizar la configuración de la barra lateral."""
    st.sidebar.markdown("## 🔧 Configuración")
    
    # Obtener credenciales desde el entorno
    database_url = os.getenv("DATABASE_URL")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Configuración de la base de datos
    with st.sidebar.expander("🗄️ Conexión a la Base de Datos", expanded=not st.session_state.connected):
        # Mostrar información de conexión (enmascarada)
        if database_url:
            # Ocultar partes sensibles de la URL
            display_url = database_url
            if "://" in display_url and "@" in display_url:
                # Ocultar contraseña en la URL
                parts = display_url.split("://")
                if len(parts) == 2 and "@" in parts[1]:
                    auth_and_host = parts[1].split("@")
                    if ":" in auth_and_host[0]:
                        user = auth_and_host[0].split(":")[0]
                        display_url = f"{parts[0]}://{user}:****@{auth_and_host[1]}"
            
            st.info(f"📍 **Base de datos:** `{display_url}`")
        else:
            st.error("❌ DATABASE_URL no se encontró en el archivo .env")
        
        if openai_api_key:
            st.info(f"🔑 **API Key:** `{openai_api_key[:8]}...{openai_api_key[-4:]}`")
        else:
            st.error("❌ OPENAI_API_KEY no se encontró en el archivo .env")
        
        # Opciones avanzadas
        with st.expander("Opciones avanzadas"):
            read_only = st.checkbox("Modo Solo Lectura", value=True, help="Permitir solo consultas SELECT")
            enable_cache = st.checkbox("Habilitar caché", value=True)
            model_strategy = st.selectbox(
                "Estrategia de modelo",
                ["adaptive", "fixed"],
                help="Adaptativo: elegir modelo según la complejidad de la consulta"
            )
        
        if st.button("🔌 Conectar", type="primary", width="stretch", disabled=not (database_url and openai_api_key)):
            if not database_url or not openai_api_key:
                st.error("❌ Por favor configura DATABASE_URL y OPENAI_API_KEY en el archivo demo/.env")
            else:
                with st.spinner("Conectando..."):
                    # Pasar sobrescrituras a from_env() - credenciales cargadas desde .env automáticamente
                    success = connect_to_database(
                        read_only=read_only,
                        enable_cache=enable_cache,
                        model_strategy=model_strategy
                    )
                    if success:
                        st.success("✅ ¡Conectado correctamente!")
                        st.rerun()
        
        if st.session_state.connected:
            if st.button("🔌 Desconectar", width="stretch"):
                st.session_state.agent = None
                st.session_state.connected = False
                st.session_state.schema_cache = None
                st.rerun()
    
    # Estadísticas
    if st.session_state.connected and st.session_state.agent:
        with st.sidebar.expander("📊 Estadísticas", expanded=True):
            stats = st.session_state.agent.get_stats()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Consultas totales", stats.get('total_queries', 0))
                st.metric("Aciertos de caché", stats.get('cache_hits', 0))
            with col2:
                st.metric("Exitosas", stats.get('successful_queries', 0))
                st.metric("Fallidas", stats.get('failed_queries', 0))
            
            if stats.get('total_queries', 0) > 0:
                hit_rate = (stats.get('cache_hits', 0) / stats['total_queries']) * 100
                st.metric("Tasa de aciertos de caché", f"{hit_rate:.1f}%")


def render_schema_browser():
    """Renderizar el explorador del esquema."""
    if not st.session_state.connected or not st.session_state.schema_cache:
        st.info("ℹ️ Conéctate a una base de datos para ver el esquema")
        return
    
    st.markdown("### 📚 Esquema de la Base de Datos")
    
    schema = st.session_state.schema_cache
    
    # Selector de tabla
    table_names = list(schema.keys())
    selected_table = st.selectbox("Seleccionar tabla", table_names)
    
    if selected_table:
        table_info = schema[selected_table]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"#### 📋 {selected_table}")
            
            # Columnas
            if 'columns' in table_info:
                columns_df = pd.DataFrame([
                    {
                        'Column': col['name'],
                        'Type': col['type'],
                        'Nullable': '✓' if col.get('nullable', True) else '✗',
                        'Primary Key': '✓' if col.get('primary_key', False) else '',
                    }
                    for col in table_info['columns']
                ])
                st.dataframe(columns_df, width="stretch", hide_index=True)
        
        with col2:
            # Estadísticas de la tabla
            st.markdown("#### 📊 Información de la Tabla")
            st.metric("Columnas", len(table_info.get('columns', [])))
            
            if 'foreign_keys' in table_info and table_info['foreign_keys']:
                st.metric("Claves Foráneas", len(table_info['foreign_keys']))
            
            if 'indexes' in table_info and table_info['indexes']:
                st.metric("Índices", len(table_info['indexes']))
        
        # Claves foráneas
        if 'foreign_keys' in table_info and table_info['foreign_keys']:
            with st.expander("🔗 Claves Foráneas"):
                for fk in table_info['foreign_keys']:
                    st.markdown(f"- `{fk.get('constrained_columns', [])}` → `{fk.get('referred_table')}.{fk.get('referred_columns', [])}`")


# Nota: La conversación casual y la generación de respuestas naturales
# ahora son gestionadas por el propio agente (conversational_layer.py)
# ¡No es necesario duplicar la lógica aquí!


def render_chat_message(message: dict, idx: int):
    """Renderizar una única burbuja de mensaje del chat."""
    if message['type'] == 'thinking':
        # Mostrar indicador de pensamiento
        st.markdown(
            '<div style="text-align: left; margin: 10px 0;">'
            '<span style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
            'color: white; padding: 12px 20px; border-radius: 20px; display: inline-block; '
            'font-size: 14px;">🤔 Pensando...</span>'
            '</div>',
            unsafe_allow_html=True
        )
    elif message['type'] == 'user':
        # Burbuja de mensaje del usuario
        st.markdown(f"""
        <div class="user-message">
            <div class="user-bubble">
                {message['content']}
                <div class="timestamp">{message['timestamp'].strftime('%I:%M %p')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # Burbuja de mensaje de la IA
        result = message['result']
        is_casual = result.get('is_casual', False)
        
        # La respuesta natural ahora es generada por la capa conversacional del agente
        natural_response = result.get('natural_response', 'He ejecutado tu consulta.')
        
        # Mostrar burbuja de IA con respuesta natural
        st.markdown(f"""
        <div class="ai-message">
            <div class="ai-bubble">
                <div class="ai-bubble-content">
                    {natural_response}
                </div>
                <div class="timestamp">{message['timestamp'].strftime('%I:%M %p')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar detalles técnicos solo para consultas a la base de datos, no para conversación casual
        if is_casual:
            return
        
        # Indicador de confianza
        if 'confidence' in result:
            confidence = result['confidence']
            if confidence > 0.8:
                badge_class = "confidence-high"
                badge_text = f"✓ {confidence:.0%} de confianza"
            elif confidence > 0.5:
                badge_class = "confidence-medium"
                badge_text = f"⚠ {confidence:.0%} de confianza"
            else:
                badge_class = "confidence-low"
                badge_text = f"⚠ {confidence:.0%} de confianza"
            
            st.markdown(f'<span class="confidence-badge {badge_class}">{badge_text}</span>', unsafe_allow_html=True)


def render_query_interface():
    """Renderizar la interfaz de consultas estilo chat."""
    if not st.session_state.connected:
        st.info("ℹ️ Conéctate a una base de datos para empezar a consultar")
        return
    
    st.markdown("### 💬 Chatea con tu Base de Datos")
    
    # Controles de Sesión y Streaming
    col1, col2, col3 = st.columns([4, 1, 1])
    with col2:
        st.session_state.use_session = st.checkbox("💬 Sesión", value=st.session_state.use_session, help="Mantener el contexto de la conversación")
    with col3:
        # Interruptor de streaming - siempre visible, controla si usar streaming
        st.session_state.use_streaming = st.checkbox("⚡ Streaming", value=st.session_state.use_streaming, help="Transmitir respuestas token por token")
    
    # Contenedor de mensajes del chat
    chat_container = st.container()
    
    with chat_container:
        # Mostrar todos los mensajes del chat
        for idx, message in enumerate(st.session_state.chat_messages):
            render_chat_message(message, idx)
    
    # Área de entrada en la parte inferior
    st.markdown("---")
    
    # Entrada de consulta
    col1, col2 = st.columns([6, 1])
    with col1:
        query = st.text_input(
            "Escribe tu pregunta...",
            placeholder="p. ej., ¿Cuántos usuarios tenemos?",
            label_visibility="collapsed",
            key="query_input",
            disabled=st.session_state.is_processing
        )
    with col2:
        send_button = st.button(
            "📤 Enviar", 
            type="primary", 
            width="stretch",
            disabled=st.session_state.is_processing or not query
        )
    
    # Manejar envío de la consulta
    if send_button and query:
        # Establecer estado de procesamiento
        st.session_state.is_processing = True
        
        # Añadir mensaje del usuario
        st.session_state.chat_messages.append({
            'type': 'user',
            'content': query,
            'timestamp': datetime.now()
        })
        
        # Ejecutar consulta - el agente gestiona automáticamente la conversación casual
        try:
            # Determinar sesión
            session_obj = None
            if st.session_state.use_session:
                if not st.session_state.current_session:
                    st.session_state.current_session = st.session_state.agent.create_session(
                        f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    )
                session_obj = st.session_state.current_session.session
            
            # Usar streaming si el usuario lo activó
            if st.session_state.use_streaming:
                # Crear placeholder para texto en streaming en el área de chat
                streaming_placeholder = st.empty()
                
                # Transmitir la respuesta con visualización en tiempo real
                streamed_text = ""
                
                async def stream_response():
                    nonlocal streamed_text
                    async for chunk in st.session_state.agent.query_stream(query, session=session_obj):
                        streamed_text += chunk
                        # Mostrar texto acumulado en tiempo real
                        streaming_placeholder.markdown(
                            f'<div style="text-align: left; margin: 10px 0;">'
                            f'<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
                            f'color: white; padding: 15px 20px; border-radius: 20px; display: inline-block; '
                            f'max-width: 70%; font-size: 14px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">'
                            f'{streamed_text}'
                            f'</div></div>',
                            unsafe_allow_html=True
                        )
                        # Añadir retraso artificial para ralentizar el streaming (ajustar si es necesario)
                        await asyncio.sleep(0.03)  # 30ms de retraso por token
                    return streamed_text
                
                # Ejecutar streaming (las estadísticas se registran a nivel del agente)
                final_response = asyncio.run(stream_response())
                
                # Limpiar el placeholder de streaming
                streaming_placeholder.empty()
                
                # Crear diccionario de resultado
                result = {
                    "natural_response": final_response,
                    "final_output": final_response
                }
            else:
                # Consulta sin streaming
                with st.spinner("🤔 Pensando..."):
                    result = asyncio.run(st.session_state.agent.query(query, session=session_obj))
            
            # Añadir respuesta de la IA
            st.session_state.chat_messages.append({
                'type': 'ai',
                'result': result,
                'timestamp': datetime.now()
            })
            
            # Guardar en historial (solo si no es conversación casual)
            if not result.get('is_casual', False):
                st.session_state.query_history.insert(0, {
                    'timestamp': datetime.now(),
                    'question': query,
                    'result': result
                })
                
            # Restablecer estado de procesamiento
            st.session_state.is_processing = False
            
            # Reejecutar para mostrar nuevos mensajes
            st.rerun()
            
        except Exception as e:
            st.session_state.is_processing = False
            st.error(f"❌ Error: {str(e)}")
            logger.error(f"Error en la consulta: {e}", exc_info=True)
    
    # Botón para limpiar chat
    if len(st.session_state.chat_messages) > 0:
        if st.button("🗑️ Limpiar chat", disabled=st.session_state.is_processing):
            st.session_state.chat_messages = []
            st.session_state.is_processing = False
            st.rerun()


def display_query_result(result: dict):
    """Mostrar el resultado de la consulta."""
    st.markdown("---")
    st.markdown("### 📊 Resultados")
    
    # Consulta SQL
    with st.expander("🔍 SQL Generado", expanded=True):
        st.code(result.get('sql', 'N/A'), language='sql')
    
    # Explicación
    if 'explanation' in result:
        with st.expander("💡 Explicación"):
            st.markdown(result['explanation'])
    
    # Confianza
    if 'confidence' in result:
        confidence = result['confidence']
        color = "green" if confidence > 0.8 else "orange" if confidence > 0.5 else "red"
        st.markdown(f"**Confianza:** :{color}[{confidence:.1%}]")
    
    # Datos de resultados
    if 'results' in result and result['results']:
        st.markdown("#### 📋 Datos")
        
        # Convertir a DataFrame
        results_data = result['results']
        if results_data:
            # Obtener nombres de columnas de la primera fila o usar nombres genéricos
            if hasattr(results_data[0], '_fields'):
                columns = results_data[0]._fields
            else:
                columns = [f"col_{i}" for i in range(len(results_data[0]))]
            
            df = pd.DataFrame(results_data, columns=columns)
            
            # Mostrar tabla
            st.dataframe(df, width="stretch")
            
            # Botón de descarga
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # Opciones de visualización
            if len(df) > 0 and len(df.columns) > 0:
                with st.expander("📈 Visualizar"):
                    chart_type = st.selectbox("Tipo de gráfico", ["Bar Chart", "Line Chart", "Area Chart"])
                    
                    # Seleccionar columnas para la visualización
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    
                    if numeric_cols:
                        y_col = st.selectbox("Eje Y", numeric_cols)
                        x_col = st.selectbox("Eje X (opcional)", ["Index"] + df.columns.tolist())
                        
                        if x_col == "Index":
                            chart_data = df[[y_col]]
                        else:
                            chart_data = df.set_index(x_col)[[y_col]]
                        
                        if chart_type == "Bar Chart":
                            st.bar_chart(chart_data)
                        elif chart_type == "Line Chart":
                            st.line_chart(chart_data)
                        elif chart_type == "Area Chart":
                            st.area_chart(chart_data)
    
    # Respuesta en lenguaje natural
    if 'natural_response' in result:
        st.markdown("#### 💬 Respuesta")
        st.info(result['natural_response'])


def render_query_history():
    """Renderizar el historial de consultas."""
    if not st.session_state.query_history:
        st.info("ℹ️ Aún no hay consultas. ¡Empieza a hacer preguntas!")
        return
    
    st.markdown("### 🕒 Historial de Consultas")
    
    for idx, item in enumerate(st.session_state.query_history[:10]):  # Mostrar las últimas 10
        with st.expander(f"**{item['question'][:50]}...** - {item['timestamp'].strftime('%H:%M:%S')}"):
            st.markdown(f"**Pregunta:** {item['question']}")
            
            # Mostrar la respuesta natural del agente
            natural_response = item['result'].get('natural_response', 'No hay respuesta disponible')
            st.markdown(f"**Respuesta:** {natural_response}")
            
            # Mostrar tiempo de ejecución si está disponible
            if 'execution_time' in item['result']:
                st.caption(f"⚡ Ejecutado en {item['result']['execution_time']:.2f}s")


def main():
    """Aplicación principal."""
    init_session_state()
    
    # Encabezado
    st.markdown('<div class="main-header">🤖 Demo del Agente de Consultas a BD</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Consultas a bases de datos en lenguaje natural con IA</div>', unsafe_allow_html=True)
    
    # Barra lateral
    sidebar_config()
    
    # Contenido principal
    if st.session_state.connected:
        # Pestañas
        tab1, tab2, tab3 = st.tabs(["💬 Consulta", "📚 Esquema", "🕒 Historial"])
        
        with tab1:
            render_query_interface()
        
        with tab2:
            render_schema_browser()
        
        with tab3:
            render_query_history()
    else:
        # Pantalla de bienvenida
        st.markdown("""
        ## 👋 ¡Bienvenido!
        
        Esta demo muestra el paquete **db-query-agent** — una interfaz de lenguaje natural para bases de datos impulsada por IA.
        
        ### 🚀 Primeros pasos
        
        1. **Crea** un archivo `demo/.env` con tus credenciales:
           ```
           DATABASE_URL=sqlite:///./demo_database.db
           OPENAI_API_KEY=sk-your-key-here
           ```
        2. **Haz clic** en Conectar en la barra lateral
        3. **Empieza** a hacer preguntas en lenguaje natural
        
        ### ✨ Funcionalidades
        
        - 🤖 **Consultas en lenguaje natural** — Haz preguntas en lenguaje sencillo
        - 🔒 **Modo solo lectura** — Consultas seguras sin modificar datos
        - 💾 **Caché inteligente** — Consultas repetidas más rápidas
        - 📊 **Explorador de esquema** — Explora la estructura de tu base de datos
        - 📈 **Visualizaciones** — Generación automática de gráficos
        - 🕒 **Historial de consultas** — Seguimiento de tus consultas
        - 💬 **Soporte de sesión** — Contexto conversacional
        
        ### 📚 Ejemplos de preguntas
        
        - "¿Cuántos usuarios tenemos?"
        - "Muéstrame los 10 productos con mayor ingreso"
        - "¿Cuál es el valor promedio de pedido este mes?"
        - "Lista todos los clientes activos"
        - "Encuentra pedidos superiores a $1000"
        
        ### 🔐 Seguridad
        
        - Todas las consultas se validan antes de ejecutarse
        - El modo solo lectura evita la modificación de datos
        - Soporte SSL/TLS para conexiones seguras
        - Ningún dato se almacena ni se transmite fuera de tu entorno
        """)
        
        # Ejemplo de inicio rápido
        with st.expander("🎯 Inicio rápido - Crear demo/.env"):
            st.markdown("**1. Crea el archivo:**")
            st.code("demo/.env", language="bash")
            
            st.markdown("**2. Añade tus credenciales:**")
            st.code("""DATABASE_URL=sqlite:///./demo_database.db
OPENAI_API_KEY=sk-your-key-here""", language="bash")
            
            st.markdown("**3. ¡Reinicia la app y haz clic en Conectar!**")


if __name__ == "__main__":
    main()
cl