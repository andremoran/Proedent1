# config.py
class Config:
    DEBUG = True
    PORT = 5000
    HOST = "127.0.0.1"

    # Clave secreta para Flask (generada aleatoriamente para mayor seguridad)
    SECRET_KEY = "clave-secreta-para-flash"  # Considera cambiar esto en producción

    # Configuración de la base de datos
    # En este caso usamos bases de datos en memoria, pero podría extenderse a una BD real
    DB_CONFIG = {
        'in_memory': True  # Si se cambia a False, habría que configurar una base de datos
    }

    # Configuración de archivos
    MODEL_PATH = "modelo.pkl"
    DIAGNOSES_FILE = "diagnosticos.csv"

    # Configuración de teleconsulta
    TELECONSULTA_PIN = "0404"

    # Variables para configuración de WhatsApp
    # Tiempo de espera para enviar mensajes (en segundos)
    WHATSAPP_WAIT_TIME = 3