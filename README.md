# Flask Resources Monitor

Un servidor web desarrollado en Python que proporciona un monitor de sistema en tiempo real mediante WebSocket. Permite al usuario visualizar el consumo de recursos de su PC en tiempo real desde cualquier dispositivo conectado a la misma red.

## Características

- **Monitoreo de Recursos del Sistema**:
  - Uso de CPU y nombre del procesador.
  - Uso de memoria RAM y total disponible.
  - Espacio en disco principal.
  - Información de red (IP y dirección MAC).
  - Procesos que más recursos consumen.
  - Tiempo de actividad del sistema (uptime).
  - Estado de la batería (si aplica).

- **Interfaz Web**:
  - Proporciona métricas del sistema mediante WebSocket.
  - Incluye un archivo HTML inicial como página principal.

- **Multiplataforma**:
  - Compatible con Windows, Linux y macOS.

- **Diseño Extensible**:
  - Fácil de configurar y expandir según las necesidades del usuario.

## Requisitos

- Python 3.8 o superior
- Dependencias adicionales (ver sección de instalación)

## Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/rodolfocasan/flask-resources-monitor.git
   cd flask-resources-monitor
   ```

2. **Instalar dependencias**:
   Se recomienda usar un entorno virtual.
   ```bash
   python -m venv venv
   source venv/bin/activate      # Linux/MacOS
   venv\Scripts\activate         # Windows
   pip install -r DOCs/requirements.txt
   ```

3. **Asegúrate de tener el archivo `index.html`**:
   - Verifica que `web/index.html` exista en el directorio raíz.

## Uso

1. **Ejecutar el servidor**:
   ```bash
   python main.py
   ```

2. **Acceder a la aplicación**:
   - El servidor imprimirá las direcciones IP disponibles en la consola.
   - Abre una de las URLs mostradas en tu navegador.

