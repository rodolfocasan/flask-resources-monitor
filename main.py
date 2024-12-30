# main.py
import os
import json
import time
import uuid
import psutil
import socket
import logging
import platform
import threading
from pathlib import Path
from flask_sock import Sock
from flask import Flask, send_file

from rich.box import SIMPLE
from rich.panel import Panel
from rich.table import Table
from rich.console import Console





'''
>>> Definición de constantes
'''
VERSION = "1.0"

# Configuración básica de logging
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
sock = Sock(app)

# Cache para almacenar las métricas
metrics_cache = {
    'cpu_percent': 0,
    'cpu_name': '',
    'memory_percent': 0,
    'memory_total': '',
    'disk_usage': 0,
    'disk_name': '',
    'disk_total': '',
    'hostname': socket.gethostname(),
    'os_info': f"{platform.system()} {platform.release()}",
    'uptime': 0,
    'power_info': {},
    'network_info': {},
    'top_processes': [],
    'last_update': 0
}





'''
>>> Definición de funciones
'''
def get_system_drive():
    """ Obtiene la unidad principal del sistema de manera multiplataforma """
    if platform.system() == 'Windows':
        return os.environ.get('SystemDrive', 'C:')
    return '/'

def get_processor_name():
    """ Obtiene el nombre del procesador de manera multiplataforma """
    if platform.system() == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Hardware\Description\System\CentralProcessor\0")
            processor_name = winreg.QueryValueEx(key, "ProcessorNameString")[0]
            winreg.CloseKey(key)
            return processor_name
        except:
            return platform.processor() or "Desconocido"
    elif platform.system() == "Darwin":
        try:
            os.environ['PATH'] = os.environ['PATH'] + os.pathsep + '/usr/sbin'
            command = "sysctl -n machdep.cpu.brand_string"
            return os.popen(command).read().strip()
        except:
            return platform.processor() or "Desconocido"
    elif platform.system() == "Linux":
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":")[1].strip()
            return platform.processor() or "Desconocido"
        except:
            return platform.processor() or "Desconocido"
    return platform.processor() or "Desconocido"

def get_uptime():
    """ Obtiene el tiempo de actividad del sistema en formato legible """
    try:
        uptime_seconds = time.time() - psutil.boot_time()
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return f"{days}d {hours}h {minutes}m"
    except:
        return "No disponible"

def get_size(bytes):
    """ Convierte bytes a formato legible """
    try:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024
    except:
        return "0 B"

def get_power_info():
    """ Obtiene información sobre la energía del sistema de manera multiplataforma """
    power_info = {'type': 'AC', 'battery_percent': None, 'status': None}
    try:
        if hasattr(psutil, 'sensors_battery'):
            battery = psutil.sensors_battery()
            if battery:
                power_info['type'] = 'Battery'
                power_info['battery_percent'] = f"{battery.percent}%"
                power_info['status'] = 'Charging' if battery.power_plugged else 'Discharging'
    except:
        pass
    return power_info

def get_network_info():
    """ Obtiene información de red de manera multiplataforma """
    network_info = {'ip': 'No disponible', 'mac': 'No disponible'}
    try:
        # Obtener direcciones IP no-loopback
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET and not addr.address.startswith('127.'):
                    network_info['ip'] = addr.address
                    break
            if network_info['ip'] != 'No disponible':
                break
        
        # Obtener MAC address
        mac_num = hex(uuid.getnode()).replace('0x', '').upper()
        mac = '-'.join(mac_num[i: i + 2] for i in range(0, 11, 2))
        if len(mac) == 17:  # Verificar que sea una MAC válida
            network_info['mac'] = mac
    except:
        pass
    return network_info

def get_top_processes(max_processes=10):
    """ Obtiene los procesos que más recursos consumen de manera multiplataforma """
    processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                if pinfo['cpu_percent'] > 0:  # Solo incluir procesos activos
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'cpu_percent': round(pinfo['cpu_percent'], 1),
                        'memory_percent': round(pinfo['memory_percent'], 1)
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception as e:
        logger.error(f"Error al obtener procesos: {str(e)}")
        return []
    
    return sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:max_processes]

def update_metrics():
    """ Actualiza las métricas en segundo plano """
    last_cpu_update = 0
    update_interval = 5  # Segundos entre actualizaciones
    
    while True:
        try:
            current_time = time.time()
            
            # Actualizar CPU solo cada 5 segundos para reducir el consumo
            if current_time - last_cpu_update >= update_interval:
                metrics_cache['cpu_percent'] = psutil.cpu_percent(interval=1)
                metrics_cache['cpu_name'] = get_processor_name()
                last_cpu_update = current_time
            
            # Memory info
            memory = psutil.virtual_memory()
            metrics_cache['memory_percent'] = memory.percent
            metrics_cache['memory_total'] = get_size(memory.total)
            
            # Disk info
            system_drive = get_system_drive()
            disk = psutil.disk_usage(system_drive)
            metrics_cache['disk_usage'] = disk.percent
            metrics_cache['disk_total'] = get_size(disk.total)
            metrics_cache['disk_name'] = f"Disco Principal ({system_drive})"
            
            # System info
            metrics_cache['uptime'] = get_uptime()
            metrics_cache['power_info'] = get_power_info()
            metrics_cache['network_info'] = get_network_info()
            metrics_cache['top_processes'] = get_top_processes()
            metrics_cache['last_update'] = current_time
            
            time.sleep(1)  # Actualización más frecuente para datos que no consumen muchos recursos
        except Exception as e:
            logger.error(f"Error actualizando métricas: {str(e)}")
            time.sleep(5)

def find_available_port(start_port=5000, max_attempts=100):
    """ Busca un puerto disponible """
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(('0.0.0.0', port))
                return port
            except OSError:
                continue
    return None

def get_local_ips():
    """ Obtiene todas las IPs locales válidas """
    ips = set()
    try:
        # Obtener el hostname local
        hostname = socket.gethostname()
        
        # Añadir localhost
        ips.add('127.0.0.1')
        
        # Obtener IP del hostname
        try:
            host_ip = socket.gethostbyname(hostname)
            if host_ip and not host_ip.startswith('127.'):
                ips.add(host_ip)
        except:
            pass
        
        # Obtener todas las IPs de las interfaces
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    ip = addr.address
                    # Filtrar IPs privadas válidas
                    if (ip.startswith('192.168.') or 
                        ip.startswith('10.') or 
                        ip.startswith('172.') and 
                        not ip.startswith('127.')):
                        ips.add(ip)
    except Exception as e:
        logger.error(f"Error obteniendo IPs locales: {str(e)}")
        ips.add('127.0.0.1')  # Fallback a localhost
    
    return sorted(list(ips))

@app.route('/')
def home():
    """ HOME (Sitio principal) """
    try:
        return send_file(str(Path('web/index.html').absolute()))
    except Exception as e:
        logger.error(f"Error al servir index.html: {str(e)}")
        return "Error: No se encuentra la página principal", 404

@app.after_request
def after_request(response):
    """Configurar headers para permitir conexiones desde cualquier origen"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST')
    return response

@sock.route('/ws')
def metrics_socket(ws):
    """WebSocket para enviar actualizaciones en tiempo real"""
    try:
        while True:
            ws.send(json.dumps(metrics_cache))
            time.sleep(1)
    except Exception as e:
        logger.error(f"Error en WebSocket: {str(e)}")

def print_banner(port, addresses):
    """Imprime el banner de inicio con las URLs de acceso usando Rich"""
    console = Console()
    title = f"[bold green]Monitor de Sistema v{VERSION} - Desarrollado por Rodolfo Casan[/bold green]"
    subtitle = "[cyan]Servidor iniciado correctamente![/cyan]\n"

    # Crear una tabla para las URLs de acceso
    table = Table(title="[bold cyan]URLs de acceso[/bold cyan]", box=SIMPLE)
    table.add_column("Dirección", style="magenta", justify="center")
    
    for addr in addresses:
        table.add_row(f"http://{addr}:{port}")
    
    # Mostrar un panel con el título y la tabla
    panel_content = (
        f"{subtitle}\n"
        f"[white]Presiona [bold red]Ctrl+C[/bold red] para detener el servidor[/white]"
    )
    panel = Panel(
        panel_content,
        title=title,
        border_style="green",
    )
    
    console.print(panel)
    console.print(table)

if __name__ == '__main__':
    console = Console()
    try:
        # Verificar que existe el archivo de template
        template_path = Path('web/index.html')
        if not template_path.isfile():
            console.print(f"[bold red]Error:[/bold red] No se encuentra el archivo {template_path.absolute()}", style="red")
            exit(1)
        
        # Encontrar un puerto disponible
        port = find_available_port()
        if not port:
            console.print("[bold red]Error:[/bold red] No se encontró un puerto disponible", style="red")
            exit(1)
        
        # Obtener IPs locales válidas
        addresses = get_local_ips()
        
        # Mostrar banner con información
        print_banner(port, addresses)
        
        # Iniciar el thread de actualización de métricas
        metrics_thread = threading.Thread(target=update_metrics, daemon=True)
        metrics_thread.start()
        
        # Iniciar el servidor Flask con configuración para conexiones remotas
        app.run(
            host = '0.0.0.0',  # Esto permite conexiones desde cualquier IP
            port = port,
            # threaded=True,
            # debug=False,         # Importante: debug debe estar desactivado en producción
            # use_reloader=False   # Evita problemas con el thread de métricas
        )
        
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Servidor detenido por el usuario[/bold yellow]", style="yellow")
    except Exception as e:
        console.print(f"[bold red]Error fatal:[/bold red] {str(e)}", style="red")
        console.print("\n[bold red]Error:[/bold red] No se pudo iniciar el servidor", style="red")
        console.print(f"[bold red]Razón:[/bold red] {str(e)}", style="red")
        exit(1)