# DB Query Agent 🤖💬

> **Sistema de consultas a bases de datos en lenguaje natural impulsado por IA usando OpenAI Agents SDK**

[![PyPI version](https://badge.fury.io/py/db-query-agent.svg)](https://badge.fury.io/py/db-query-agent)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://pepy.tech/badge/db-query-agent)](https://pepy.tech/project/db-query-agent)

Un potente paquete de Python listo para producción que te permite consultar bases de datos usando lenguaje natural. Construido con OpenAI Agents SDK, incluye guardrails de seguridad inteligentes, respuestas en streaming y está optimizado para velocidad.

## ✨ Características

- 🗣️ **Consultas en lenguaje natural** - Haz preguntas en inglés sencillo y obtén SQL y resultados
- ⚡ **Extremadamente rápido** - Respuestas en streaming, selección adaptativa de modelos y caché multinivel
- 🔒 **Seguridad lista para producción** - Modo solo lectura, prevención de inyección SQL y validación de consultas
- 💬 **Gestión de sesiones** - Mantiene el contexto de conversación entre múltiples consultas
- 🎯 **Carga inteligente de esquemas** - Solo carga las tablas relevantes para respuestas más rápidas
- 🔌 **Soporte universal de bases de datos** - PostgreSQL, MySQL, SQLite, SQL Server
- 📦 **Integración sencilla** - Funciona con Django, Flask, FastAPI o cualquier aplicación Python

## 🚀 Inicio rápido

### Instalación

```bash
pip install db-query-agent

# Con drivers específicos de base de datos
pip install db-query-agent[postgres]  # PostgreSQL
pip install db-query-agent[mysql]     # MySQL
pip install db-query-agent[all]       # Todos los drivers
```

### Uso básico

**Opción 1: Cargar desde .env (Recomendado)**

```bash
# Crear archivo .env
DATABASE_URL=postgresql://user:pass@localhost/mydb
OPENAI_API_KEY=sk-...
FAST_MODEL=gpt-4o-mini
READ_ONLY=true
```

```python
from db_agent_sql import DatabaseQueryAgent

# Cargar todo desde .env
agent = DatabaseQueryAgent.from_env()

# O sobrescribir valores específicos
agent = DatabaseQueryAgent.from_env(
    fast_model="gpt-4.1",
    enable_statistics=True
)
```

**Opción 2: Configuración directa**

```python
from db_agent_sql import DatabaseQueryAgent

# Pasar todos los parámetros directamente
agent = DatabaseQueryAgent(
    database_url="postgresql://user:pass@localhost/mydb",
    openai_api_key="sk-...",
    fast_model="gpt-4o-mini",
    read_only=True,
    enable_cache=True
)
```

### Consultar la base de datos

```python
# Consulta en lenguaje natural (async)
result = await agent.query("How many users signed up last month?")

print(result["natural_response"])
# Output: "245 users signed up last month"

print(result["sql"])
# Output: "SELECT COUNT(*) FROM users WHERE created_at >= '2025-09-01'"
```

### Con Streaming (Recomendado)

```python
# Streaming de respuestas para mejor UX
async for chunk in agent.query_stream("Show me top 10 customers by revenue"):
    print(chunk, end="", flush=True)
```

### Chat basado en sesiones

```python
# Crear una sesión para conversaciones de múltiples turnos
session = agent.create_session(session_id="user_123")

# Primera consulta
response1 = await session.ask("Show me all products")

# Consulta de seguimiento (mantiene contexto)
response2 = await session.ask("Filter those by category=electronics")

# Otro seguimiento
response3 = await session.ask("Sort by price descending")
```

## 🔧 Métodos de utilidad

### Gestión de sesiones

```python
# Listar todas las sesiones activas
sessions = agent.list_sessions()

# Obtener historial de conversación
history = agent.get_session_history("user_123")

# Limpiar historial de sesión
agent.clear_session("user_123")

# Eliminar sesión
agent.delete_session("user_123")
```

### Exploración del esquema

```python
# Obtener esquema básico
schema = agent.get_schema()

# Obtener esquema detallado con relaciones
schema_info = agent.get_schema_info(include_foreign_keys=True)
print(f"Total tables: {schema_info['total_tables']}")
print(f"Relationships: {len(schema_info['relationships'])}")
```

### Estadísticas y monitoreo

```python
# Obtener estadísticas completas
stats = agent.get_stats()

print(f"Total queries: {stats['total_queries']}")
print(f"Cache hit rate: {stats['cache_hits'] / stats['total_queries'] * 100:.1f}%")
print(f"Active connections: {stats['pool']['checked_out']}")
print(f"Total sessions: {stats['sessions']['total_sessions']}")
```

## 🎯 Integración con frameworks

### Django

```python
# views.py
from django.conf import settings
from db_agent_sql import DatabaseQueryAgent

agent = DatabaseQueryAgent(
    database_url=settings.DATABASES['default']['URL'],
    openai_api_key=settings.OPENAI_API_KEY
)

def query_database(request):
    question = request.POST.get('question')
    result = agent.query(question)
    return JsonResponse(result)
```

### FastAPI

```python
# main.py
from fastapi import FastAPI
from db_agent_sql import DatabaseQueryAgent

app = FastAPI()
agent = DatabaseQueryAgent(database_url=os.getenv("DATABASE_URL"))

@app.post("/query")
async def query_db(question: str):
    return agent.query(question)
```

### Flask

```python
# app.py
from flask import Flask, request
from db_agent_sql import DatabaseQueryAgent

app = Flask(__name__)
agent = DatabaseQueryAgent(database_url=os.getenv("DATABASE_URL"))

@app.route('/query', methods=['POST'])
def query():
    return agent.query(request.json['question'])
```

## ⚙️ Configuración

### Variables de entorno (Recomendado)

Crea un archivo `.env` con toda la configuración:

```bash
# Required
OPENAI_API_KEY=sk-your-api-key
DATABASE_URL=postgresql://user:pass@localhost/db

# Model Configuration
MODEL_STRATEGY=adaptive
FAST_MODEL=gpt-4o-mini
BALANCED_MODEL=gpt-4.1-mini
COMPLEX_MODEL=gpt-4.1

# Cache Configuration
CACHE_ENABLED=true
CACHE_BACKEND=memory
CACHE_SCHEMA_TTL=3600
CACHE_QUERY_TTL=300
CACHE_LLM_TTL=3600

# Safety Configuration
READ_ONLY=true
QUERY_TIMEOUT=30
MAX_RESULT_ROWS=10000

# Connection Configuration
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Performance Configuration
LAZY_SCHEMA_LOADING=true
ENABLE_STREAMING=true
WARMUP_ON_INIT=false
```

Luego cárgalo con una sola línea:

```python
agent = DatabaseQueryAgent.from_env()
```

## 📊 Rendimiento

| Escenario | Tiempo de respuesta | Cache Hit |
|----------|---------------|-----------|
| Consulta simple (cache) | **0.5s** | ✅ |
| Consulta simple (sin cache) | **1.5s** | ❌ |
| Consulta compleja (cache) | **2s** | ✅ |
| Consulta compleja (sin cache) | **5s** | ❌ |

- **El 90% de las consultas** se completan en < 3 segundos
- **El primer token** aparece en < 500ms con streaming
- **La tasa de aciertos de caché** suele ser > 60% en producción

## 🔒 Características de seguridad

- ✅ **Modo solo lectura** por defecto (solo consultas SELECT)
- ✅ **Prevención de inyección SQL** mediante análisis y validación de consultas
- ✅ **Control de acceso a tablas** con allowlist/blocklist
- ✅ **Límites de tiempo de consulta**
- ✅ **Detección de palabras clave peligrosas** (DROP, DELETE, etc.)
- ✅ **Guardrails de entrada/salida** con OpenAI Agents SDK

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Puedes ayudar de las siguientes maneras:

1. **Reportar bugs** — Abre un issue con detalles del problema
2. **Sugerir nuevas funcionalidades** — Comparte ideas de mejora
3. **Enviar PRs** — Corrige bugs o añade funcionalidades
4. **Mejorar la documentación** — Ayuda a hacerla más clara
5. **Compartir feedback** — Cuéntanos cómo usas el paquete

## 📄 Licencia

Este proyecto está licenciado bajo la licencia MIT — consulta el archivo [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- Construido con [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
- Abstracción de base de datos mediante [SQLAlchemy](https://www.sqlalchemy.org/)
- Análisis de SQL con [sqlparse](https://github.com/andialbrecht/sqlparse)

---

**Hecho con ❤️ para desarrolladores que quieren consultar bases de datos usando lenguaje natural**