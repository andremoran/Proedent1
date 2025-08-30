import multiprocessing
import os

# Configuración básica de Gunicorn para Render
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}" # Render asigna dinámicamente el puerto mediante la variable de entorno PORT
workers = multiprocessing.cpu_count() * 2 + 1  # Fórmula recomendada: (2 x núm_CPUs) + 1
worker_class = "sync"  # Usa gevent para mejor rendimiento con aplicaciones Flask
timeout = 120  # Aumentado para operaciones que pueden tomar más tiempo (como envío de WhatsApp)
keepalive = 5  # Tiempo que un worker permanecerá inactivo esperando conexiones

# Configuración de logging
loglevel = "info"
accesslog = "-"  # Envía logs de acceso a stdout (Render captura estos logs)
errorlog = "-"   # Envía logs de error a stderr (Render captura estos logs)

# Gunicorn reiniciará los workers que excedan este límite de memoria (en bytes)
# 250 MB es un buen punto de partida
max_requests = 1000
max_requests_jitter = 50  # Añade variación aleatoria para evitar que todos los workers se reinicien al mismo tiempo