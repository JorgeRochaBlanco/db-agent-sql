# 🤖 DB Query Agent - Demo de Streamlit

Aplicación de demostración interactiva para el paquete `db-agent-sql`.

## 🚀 Inicio rápido

### 1. Instalar dependencias

```bash
# Desde la raíz del proyecto
uv pip install -e ".[dev]"
```

### 2. Configurar el entorno

**Importante:** Crea un archivo `.env` en el directorio de la demo (las credenciales se leen desde aquí, no desde la UI):

```bash
# demo/.env
OPENAI_API_KEY=sk-your-openai-api-key-here
DATABASE_URL=sqlite:///./demo_database.db
```

**Nota:** La aplicación de demostración lee las credenciales desde el archivo `.env` por seguridad. No tendrás que introducirlas en la UI.

### 3. Crear base de datos de demostración (opcional)

```bash
python demo/create_demo_db.py
```

Esto crea una base de datos SQLite con datos de ejemplo (usuarios, pedidos, productos).

### 4. Ejecutar la demo

```bash
streamlit run demo/streamlit_app.py
```

La aplicación se abrirá en tu navegador en `http://localhost:8501`

---

## ✨ Características

### 💬 Interfaz de consultas en lenguaje natural
- Haz preguntas en inglés sencillo
- Obtén consultas SQL generadas automáticamente
- Visualiza los resultados en tablas
- Descarga los resultados como CSV

### 📚 Explorador de esquema
- Explora las tablas de la base de datos
- Visualiza tipos de columnas y restricciones
- Observa relaciones de claves foráneas
- Consulta índices

### 📊 Visualizaciones
- Generación automática de gráficos
- Gráficos de barras, líneas y áreas
- Exploración interactiva de datos

### 🕒 Historial de consultas
- Registra todas tus consultas
- Revisa resultados anteriores
- Reutiliza consultas exitosas

### 💬 Soporte de sesión
- Mantiene el contexto de la conversación
- Permite hacer preguntas de seguimiento
- Hace referencia a consultas anteriores

### 📈 Panel de estadísticas
- Total de consultas ejecutadas
- Tasa de aciertos de caché
- Métricas de éxito/fallo
- Estadísticas de rendimiento

---

## 🎯 Ejemplos de consultas

Prueba estas preguntas en lenguaje natural:

```
How many users do we have?
Show me the top 10 products by revenue
What's the average order value?
List all active customers
Find orders over $1000
Which users have never placed an order?
What are the most popular product categories?
Show me monthly revenue trends
```

---

## 🔧 Opciones de configuración

### Conexión a base de datos

Compatible con múltiples tipos de base de datos:

```bash
# SQLite
DATABASE_URL=sqlite:///./database.db

# PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# MySQL
DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/dbname

# SQL Server
DATABASE_URL=mssql+pyodbc://user:pass@localhost/dbname?driver=ODBC+Driver+17+for+SQL+Server
```

### Opciones avanzadas

- **Modo solo lectura**: Evita la modificación de datos (recomendado)
- **Caché**: Acelera consultas repetidas
- **Estrategia de modelo**: 
  - `adaptive`: Elige automáticamente el modelo según la complejidad
  - `fixed`: Usa el mismo modelo para todas las consultas

---

## 🔒 Seguridad

### Buenas prácticas

1. **Usar modo solo lectura** (habilitado por defecto)
2. **Usar un usuario de base de datos de solo lectura**
3. **No subir claves API al repositorio** (usa archivo `.env`)
4. **Restringir acceso a tablas** si es necesario
5. **Habilitar SSL** para bases de datos remotas

### Seguro por defecto

- Todas las consultas se validan antes de ejecutarse
- Palabras clave peligrosas bloqueadas (DROP, DELETE, etc.)
- El modo solo lectura evita modificaciones
- Soporte SSL/TLS para conexiones seguras

---

## 📸 Capturas de pantalla

### Interfaz principal de consulta
![Query Interface](./screenshots/query_interface.png)

### Explorador de esquema
![Schema Browser](./screenshots/schema_browser.png)

### Visualización de resultados
![Visualization](./screenshots/visualization.png)

---

## 🐛 Solución de problemas

### Problemas de conexión

**Problema**: "Connection failed"
- Comprueba el formato de la URL de la base de datos
- Verifica que la base de datos esté en ejecución
- Comprueba la conectividad de red
- Verifica las credenciales

**Problema**: "SSL connection failed"
- Añade `?sslmode=disable` para bases de datos locales
- Comprueba las rutas de los certificados SSL
- Consulta [SSL_CONFIGURATION.md](../SSL_CONFIGURATION.md)

### Problemas de consulta

**Problema**: "Query validation failed"
- Comprueba si la consulta es solo SELECT (modo solo lectura)
- Verifica que los nombres de tabla existan
- Comprueba si hay palabras clave peligrosas

**Problema**: "No results returned"
- Verifica que existan datos en las tablas
- Comprueba la lógica de la consulta
- Revisa el SQL generado

### Problemas de API

**Problema**: "OpenAI API error"
- Verifica que la clave API sea correcta
- Comprueba que la clave tenga créditos
- Comprueba la conectividad de red

---

## 🎨 Personalización

### Modificar el tema de la UI

Edita la sección CSS de `streamlit_app.py`:

```python
st.markdown("""
<style>
    .main-header {
        color: #your-color;
    }
</style>
""", unsafe_allow_html=True)
```

### Añadir funciones personalizadas

La demo es modular: añade tus propias pestañas o funciones:

```python
with st.tabs(["Query", "Schema", "History", "Your Feature"]):
    # Tu código personalizado
    pass
```

---

## 📚 Saber más

- [Main README](../README.md)
- [API Documentation](../docs/API.md)
- [SSL Configuration](../SSL_CONFIGURATION.md)
- [Phase 3 Plan](../PHASE_3_PLAN.md)

---

## 🤝 Contribuciones

¿Encontraste un bug o tienes una solicitud de funcionalidad? ¡Abre un issue!

---

## 📄 Licencia

La misma que el paquete principal.
