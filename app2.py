# http://127.0.0.1:5000/

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
import pandas as pd
import pickle
import os
import json
from datetime import datetime
import random
from io import BytesIO
import uuid
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
from functools import wraps
import logging

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = "clave-secreta-para-flash"

# Configuración de Email
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SISTEMA DE PERSISTENCIA CON JSON
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Archivos de datos
LEADS_FILE = os.path.join(DATA_DIR, 'leads.json')
APPOINTMENTS_FILE = os.path.join(DATA_DIR, 'appointments.json')
SALES_CANDIDATES_FILE = os.path.join(DATA_DIR, 'sales_candidates.json')
PATIENTS_FILE = os.path.join(DATA_DIR, 'patients.json')
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products.json')
COURSES_FILE = os.path.join(DATA_DIR, 'courses.json')
COUNTERS_FILE = os.path.join(DATA_DIR, 'counters.json')

def load_json_data(filename, default_data=None):
    """Cargar datos desde archivo JSON"""
    if default_data is None:
        default_data = {}
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return default_data
    except Exception as e:
        logger.error(f"Error cargando {filename}: {e}")
        return default_data

def save_json_data(data, filename):
    """Guardar datos a archivo JSON"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error guardando {filename}: {e}")
        return False

def load_counters():
    """Cargar contadores desde archivo"""
    default_counters = {
        'patient_id_counter': 1,
        'product_id_counter': 22,
        'course_id_counter': 3,
        'appointment_id_counter': 1,
        'lead_id_counter': 1,
        'sales_recruitment_id_counter': 1
    }
    return load_json_data(COUNTERS_FILE, default_counters)

def save_counters(counters):
    """Guardar contadores a archivo"""
    return save_json_data(counters, COUNTERS_FILE)

def get_next_id(counter_type):
    """Obtener el siguiente ID y actualizar contadores"""
    global counters
    if counter_type in counters:
        current_id = counters[counter_type]
        counters[counter_type] += 1
        save_counters(counters)
        return current_id
    return 1

# Cargar todos los datos al iniciar
print("Cargando datos persistentes...")
patients_db = load_json_data(PATIENTS_FILE, {})
products_db = load_json_data(PRODUCTS_FILE, {})
courses_db = load_json_data(COURSES_FILE, {})
appointments_db = load_json_data(APPOINTMENTS_FILE, {})
leads_db = load_json_data(LEADS_FILE, {})
sales_recruitment_db = load_json_data(SALES_CANDIDATES_FILE, {})

# Cargar contadores
counters = load_counters()

print(f"Datos cargados exitosamente:")
print(f"  - Leads: {len(leads_db)}")
print(f"  - Citas: {len(appointments_db)}")
print(f"  - Candidatos vendedores: {len(sales_recruitment_db)}")
print(f"  - Pacientes: {len(patients_db)}")
print(f"  - Productos: {len(products_db)}")

# Función para enviar correo de lead magnet
def send_lead_magnet_email(lead_data, magnet_type, interests):
    """Enviar correo con lead magnet"""
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD:
            logger.error("Credenciales de email no configuradas")
            return False

        magnet_info = {
            'secretos': {
                'subject': '🔥 Los 10 Secretos de las Mejores Clínicas Dentales',
                'title': 'Los 10 Secretos Están Aquí!'
            },
            'errores': {
                'subject': '⚠️ URGENTE: 10 Errores MORTALES que Destruyen Clínicas',
                'title': '¡Tu Clínica Ahora Está Protegida!'
            },
            'guia_rx': {
                'subject': '📋 LEGAL: Guía Completa de Cumplimiento RX Ecuador',
                'title': '¡Tu Guía Legal Completa!'
            }
        }

        info = magnet_info.get(magnet_type, magnet_info['secretos'])
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = lead_data['email']
        msg['Subject'] = info['subject']

        interests_text = ', '.join(interests) if interests else 'No especificados'

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #5B21B6, #ef4444); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 2rem;">{info['title']}</h1>
                <p style="color: white; margin: 10px 0 0 0; font-size: 1.1rem;">PROEDENT Ecuador</p>
            </div>

            <div style="padding: 30px; background: #f9f9f9;">
                <h2 style="color: #5B21B6;">Hola {lead_data['nombre']},</h2>

                <p style="font-size: 1.1rem; line-height: 1.6;">
                    ¡Perfecto! Tu guía especializada está lista. Hemos preparado este contenido 
                    exclusivo basado en tus intereses específicos.
                </p>

                <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #5B21B6;">
                    <h3 style="color: #5B21B6; margin-top: 0;">Tus intereses seleccionados:</h3>
                    <p><strong>{interests_text}</strong></p>
                </div>

                <div style="background: #e8f5e8; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3 style="color: #2e7d32; margin-top: 0;">🔎 Contenido Exclusivo</h3>
                    <p style="margin: 0;">
                        Este contenido normalmente cuesta $200+ en consultoría especializada.
                        Es tuyo completamente GRATIS.
                    </p>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <h3 style="color: #5B21B6;">¿Necesitas una demostración personalizada?</h3>
                    <p style="margin: 5px 0;"><strong>📧 Email:</strong> proedentventasecuador@gmail.com</p>
                    <p style="margin: 5px 0;"><strong>📱 WhatsApp:</strong> <a href="https://wa.me/593998745641" style="color: #5B21B6;">+593 99 874 5641</a></p>
                    <p style="margin: 5px 0;"><strong>🌐 Web:</strong> <a href="https://proedent1.onrender.com" style="color: #5B21B6;">proedent1.onrender.com</a></p>
                </div>
            </div>

            <div style="background: #333; color: white; text-align: center; padding: 20px;">
                <p style="margin: 0;">PROEDENT - Innovación y calidad al servicio de la odontología moderna</p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_content, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        logger.info(f"Lead magnet '{magnet_type}' enviado exitosamente a: {lead_data['email']}")
        return True

    except Exception as e:
        logger.error(f"Error enviando lead magnet: {e}")
        return False

def send_lead_notification_to_proedent(lead_data, magnet_type, interests):
    """Enviar notificación de nuevo lead a PROEDENT"""
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD:
            return False

        magnet_names = {
            'secretos': '10 Secretos de las Mejores Clínicas Dentales',
            'errores': '10 Errores Mortales de Clínicas Dentales',
            'guia_rx': 'Guía Legal de Cumplimiento RX'
        }

        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = "proedentventasecuador@gmail.com"
        msg['Subject'] = f"🎯 Nuevo Lead: {magnet_names.get(magnet_type, 'Lead Magnet')} - {lead_data['nombre']}"

        interests_text = ', '.join(interests) if interests else 'No especificados'

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #5B21B6, #ef4444); padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">🎯 Nuevo Lead Generado</h1>
                <p style="color: white; margin: 10px 0 0 0;">{magnet_names.get(magnet_type, 'Lead Magnet')}</p>
            </div>

            <div style="padding: 30px; background: #f9f9f9;">
                <table style="width: 100%; margin: 20px 0;">
                    <tr>
                        <td style="padding: 10px; background: white; border-left: 4px solid #5B21B6; font-weight: bold;">
                            Nombre:
                        </td>
                        <td style="padding: 10px; background: white;">
                            {lead_data['nombre']}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background: #f0f0f0; border-left: 4px solid #ef4444; font-weight: bold;">
                            Email:
                        </td>
                        <td style="padding: 10px; background: #f0f0f0;">
                            {lead_data['email']}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background: white; border-left: 4px solid #5B21B6; font-weight: bold;">
                            Teléfono:
                        </td>
                        <td style="padding: 10px; background: white;">
                            {lead_data.get('telefono', 'No proporcionado')}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background: #f0f0f0; border-left: 4px solid #ef4444; font-weight: bold;">
                            Intereses:
                        </td>
                        <td style="padding: 10px; background: #f0f0f0;">
                            {interests_text}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background: white; border-left: 4px solid #5B21B6; font-weight: bold;">
                            Lead Magnet:
                        </td>
                        <td style="padding: 10px; background: white;">
                            {magnet_names.get(magnet_type, 'Lead Magnet')}
                        </td>
                    </tr>
                </table>

                <div style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; color: #1565c0;">
                        <strong>Fecha de descarga:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_content, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        return True

    except Exception as e:
        logger.error(f"Error enviando notificación de lead: {e}")
        return False

def send_demo_request_email(form_data):
    """Enviar correo con solicitud de demostración/consulta"""
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD:
            logger.error("Credenciales de email no configuradas")
            return False

        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = "proedentventasecuador@gmail.com"
        msg['Subject'] = f"Nueva Solicitud - {form_data['nombre']}"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #5B21B6, #ef4444); padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">Nueva Solicitud de Demostración/Consulta</h1>
            </div>

            <div style="padding: 30px; background: #f9f9f9;">
                <h2 style="color: #5B21B6; border-bottom: 2px solid #5B21B6; padding-bottom: 10px;">
                    Información del Cliente
                </h2>

                <table style="width: 100%; margin: 20px 0;">
                    <tr>
                        <td style="padding: 10px; background: white; border-left: 4px solid #5B21B6; font-weight: bold;">
                            Nombre:
                        </td>
                        <td style="padding: 10px; background: white;">
                            {form_data['nombre']}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background: #f0f0f0; border-left: 4px solid #ef4444; font-weight: bold;">
                            Correo:
                        </td>
                        <td style="padding: 10px; background: #f0f0f0;">
                            {form_data['correo']}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background: white; border-left: 4px solid #5B21B6; font-weight: bold;">
                            Teléfono:
                        </td>
                        <td style="padding: 10px; background: white;">
                            {form_data.get('telefono', 'No proporcionado')}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background: #f0f0f0; border-left: 4px solid #ef4444; font-weight: bold;">
                            Representante/Área:
                        </td>
                        <td style="padding: 10px; background: #f0f0f0;">
                            {form_data['representante']}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background: white; border-left: 4px solid #5B21B6; font-weight: bold;">
                            Fecha Preferida:
                        </td>
                        <td style="padding: 10px; background: white;">
                            {form_data.get('fecha', 'No especificada')}
                        </td>
                    </tr>
                </table>

                {f'''
                <h3 style="color: #ef4444; margin-top: 30px;">Mensaje/Consulta:</h3>
                <div style="background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #ef4444;">
                    {form_data.get('mensaje', 'Sin mensaje adicional').replace(chr(10), '<br>')}
                </div>
                ''' if form_data.get('mensaje') else ''}

                <div style="margin-top: 30px; padding: 15px; background: #e3f2fd; border-radius: 5px;">
                    <p style="margin: 0; color: #1565c0;">
                        <strong>Fecha de solicitud:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_content, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        logger.info(f"Correo enviado exitosamente para: {form_data['nombre']}")
        return True

    except Exception as e:
        logger.error(f"Error enviando correo: {e}")
        return False

def send_confirmation_email(client_data):
    """Enviar correo de confirmación al cliente"""
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD or not client_data.get('correo'):
            return False

        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = client_data['correo']
        msg['Subject'] = "Confirmación de Solicitud - PROEDENT"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #5B21B6, #ef4444); padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">¡Solicitud Recibida!</h1>
            </div>

            <div style="padding: 30px; background: #f9f9f9;">
                <p style="font-size: 18px;">Hola <strong>{client_data['nombre']}</strong>,</p>

                <p>Hemos recibido tu solicitud de demostración/consulta y nos pondremos en contacto contigo muy pronto.</p>

                <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #5B21B6;">
                    <h3 style="color: #5B21B6; margin-top: 0;">Resumen de tu solicitud:</h3>
                    <p><strong>Representante asignado:</strong> {client_data['representante']}</p>
                    {f"<p><strong>Fecha preferida:</strong> {client_data.get('fecha', 'No especificada')}</p>" if client_data.get('fecha') else ''}
                    {f"<p><strong>Tu consulta:</strong> {client_data.get('mensaje', 'Sin mensaje')}</p>" if client_data.get('mensaje') else ''}
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <p>Si tienes alguna pregunta urgente, puedes contactarnos:</p>
                    <p>
                        📧 proedentventasecuador@gmail.com<br>
                        📱 WhatsApp: <a href="https://wa.me/593998745641" style="color: #5B21B6;">+593 99 874 5641</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_content, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        return True

    except Exception as e:
        logger.error(f"Error enviando confirmación: {e}")
        return False

def send_sales_recruitment_email(candidate_data):
    """Enviar correo con guía de estudio para vendedores"""
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD:
            logger.error("Credenciales de email no configuradas")
            return False

        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = candidate_data['email']
        msg['Subject'] = "🎯 Tu Guía de Estudio - Vendedor PROEDENT"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #5B21B6, #ef4444); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 2rem;">¡Tu Guía de Estudio Está Aquí!</h1>
                <p style="color: white; margin: 10px 0 0 0; font-size: 1.1rem;">PROEDENT - Equipo de Ventas</p>
            </div>

            <div style="padding: 30px; background: #f9f9f9;">
                <h2 style="color: #5B21B6;">Hola {candidate_data['nombre']},</h2>

                <p style="font-size: 1.1rem; line-height: 1.6;">
                    ¡Perfecto! Hemos recibido tu postulación para unirte a nuestro equipo de vendedores.
                    Tu guía de estudio con el catálogo completo de equipos CT y RX está adjunta en formato PDF.
                </p>

                <div style="background: #e8f5e8; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #10b981;">
                    <h3 style="color: #059669; margin-top: 0;">🔎 Archivo Adjunto:</h3>
                    <p style="color: #047857; margin: 0;"><strong>GUIAvendedores.pdf</strong> - Catálogo completo de productos PROEDENT</p>
                </div>

                <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #5B21B6;">
                    <h3 style="color: #5B21B6; margin-top: 0;">💰 Comisiones:</h3>
                    <p><strong>10% - 15% por cada venta realizada</strong></p>
                    <p>Ciudad: {candidate_data.get('ciudad', 'No especificada')}</p>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <h3 style="color: #5B21B6;">¿Necesitas capacitación adicional?</h3>
                    <p style="margin: 5px 0;"><strong>📧 Email:</strong> proedentorg@gmail.com</p>
                    <p style="margin: 5px 0;"><strong>📱 WhatsApp:</strong> <a href="https://wa.me/593998745641" style="color: #5B21B6;">+593 99 874 5641</a></p>
                    <p style="margin: 5px 0;"><strong>💵 Capacitación:</strong> Solo $10 USD</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_content, 'html'))

        # Adjuntar PDF si existe
        try:
            pdf_path = os.path.join('static', 'pdfs', 'GUIAvendedores.pdf')
            if os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as f:
                    attach = MIMEBase('application', 'octet-stream')
                    attach.set_payload(f.read())
                    encoders.encode_base64(attach)
                    attach.add_header(
                        'Content-Disposition',
                        'attachment; filename= "GUIA_Vendedores_PROEDENT.pdf"'
                    )
                    msg.attach(attach)
                logger.info("PDF adjuntado exitosamente")
        except Exception as pdf_error:
            logger.error(f"Error adjuntando PDF: {pdf_error}")

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        logger.info(f"Guía de vendedores enviada exitosamente a: {candidate_data['email']}")
        return True

    except Exception as e:
        logger.error(f"Error enviando guía de vendedores: {e}")
        return False

def send_sales_candidate_notification_to_proedent(candidate_data):
    """Enviar notificación de nuevo candidato a vendedor"""
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD:
            return False

        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = "proedentorg@gmail.com"
        msg['Cc'] = "proedentventasecuador@gmail.com"
        msg['Subject'] = f"🎯 Nuevo Candidato a Vendedor: {candidate_data['nombre']} - {candidate_data.get('ciudad', 'Ecuador')}"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #5B21B6, #ef4444); padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">🎯 Nuevo Candidato a Vendedor</h1>
                <p style="color: white; margin: 10px 0 0 0;">Solicitud de Unirse al Equipo de Ventas</p>
            </div>

            <div style="padding: 30px; background: #f9f9f9;">
                <table style="width: 100%; margin: 20px 0;">
                    <tr>
                        <td style="padding: 10px; background: white; border-left: 4px solid #5B21B6; font-weight: bold;">
                            Nombre Completo:
                        </td>
                        <td style="padding: 10px; background: white;">
                            {candidate_data['nombre']}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background: #f0f0f0; border-left: 4px solid #ef4444; font-weight: bold;">
                            Email:
                        </td>
                        <td style="padding: 10px; background: #f0f0f0;">
                            {candidate_data['email']}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background: white; border-left: 4px solid #5B21B6; font-weight: bold;">
                            Teléfono/WhatsApp:
                        </td>
                        <td style="padding: 10px; background: white;">
                            {candidate_data['telefono']}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background: #f0f0f0; border-left: 4px solid #ef4444; font-weight: bold;">
                            Ciudad:
                        </td>
                        <td style="padding: 10px; background: #f0f0f0;">
                            {candidate_data.get('ciudad', 'No especificada')}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background: white; border-left: 4px solid #5B21B6; font-weight: bold;">
                            Experiencia:
                        </td>
<td style="padding: 10px; background: white;">
                            {candidate_data.get('experiencia_sector', 'No especificada')}
                        </td>
                    </tr>
                </table>

                <div style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; color: #1565c0;">
                        <strong>Fecha de postulación:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_content, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        return True

    except Exception as e:
        logger.error(f"Error enviando notificación de candidato: {e}")
        return False


# Función para autenticación admin
def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash("Acceso restringido. Inicia sesión como administrador.", "warning")
            return redirect(url_for('patients'))
        return view_func(*args, **kwargs)

    return wrapper


# Datos iniciales del catálogo
def initialize_catalog():
    if not products_db:  # Solo inicializar si está vacío
        products = [
            {
                "id": 1,
                "name": "Tomógrafo Dental 3D",
                "category": "Diagnóstico por Imagen",
                "brand": "Proedent",
                "description": "Tecnología avanzada de imagen 3D para diagnósticos precisos",
                "price": "Consultar precio",
                "image": "Picture2.png",
                "specifications": "Resolución: 150 micras, Campo de visión: 16x13cm"
            },
            {
                "id": 2,
                "name": "Sillón Odontológico Premium",
                "category": "Equipos Principales",
                "brand": "Proedent",
                "description": "Equipamiento de última generación para máximo confort",
                "price": "Desde $15,000",
                "image": "Picture4.png",
                "specifications": "Motor eléctrico, LED integrado, Sistema de aspiración"
            }
        ]

        for product in products:
            products_db[str(product["id"])] = product

        save_json_data(products_db, PRODUCTS_FILE)
        logger.info("Catálogo inicializado")


def initialize_courses():
    if not courses_db:  # Solo inicializar si está vacío
        courses = [
            {
                "id": 1,
                "name": "Introducción a la Radiología Digital",
                "duration": "8 horas",
                "instructor": "Dr. Carlos Mendoza",
                "description": "Curso completo sobre el uso de sensores digitales",
                "price": "$150",
                "date": "2025-09-15",
                "available_spots": 15
            }
        ]

        for course in courses:
            courses_db[str(course["id"])] = course

        save_json_data(courses_db, COURSES_FILE)
        logger.info("Cursos inicializados")


# Inicializar datos si es necesario
initialize_catalog()
initialize_courses()


# ==================== RUTAS PRINCIPALES ====================

@app.route("/")
def index():
    return render_template("index.html")


# ==================== RUTAS PARA LEAD MAGNETS ====================

@app.route("/lead_magnet_secretos", methods=["GET", "POST"])
def lead_magnet_secretos():
    if request.method == "GET":
        return render_template("LM-10Secretos.html")

    try:
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        telefono = request.form.get("telefono", "")
        intereses = request.form.getlist("intereses")

        if not all([nombre, email]):
            return jsonify({"success": False, "error": "Nombre y email son requeridos"}), 400

        lead_data = {
            'nombre': nombre,
            'email': email,
            'telefono': telefono,
            'magnet_type': 'secretos',
            'intereses': intereses,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Guardar con persistencia
        current_id = get_next_id('lead_id_counter')
        leads_db[str(current_id)] = lead_data
        save_json_data(leads_db, LEADS_FILE)

        email_success = send_lead_magnet_email(lead_data, 'secretos', intereses)
        send_lead_notification_to_proedent(lead_data, 'secretos', intereses)

        if email_success:
            return redirect(url_for('thankyou'))
        else:
            return jsonify({"success": False, "error": "Error enviando la guía"}), 500

    except Exception as e:
        logger.error(f"Error en lead_magnet_secretos: {e}")
        return jsonify({"success": False, "error": "Error interno"}), 500


@app.route("/lead_magnet_errores", methods=["GET", "POST"])
def lead_magnet_errores():
    if request.method == "GET":
        return render_template("LM-10Errores.html")

    try:
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        telefono = request.form.get("telefono", "")
        intereses = request.form.getlist("intereses")

        if not all([nombre, email]):
            return jsonify({"success": False, "error": "Nombre y email son requeridos"}), 400

        lead_data = {
            'nombre': nombre,
            'email': email,
            'telefono': telefono,
            'magnet_type': 'errores',
            'intereses': intereses,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        current_id = get_next_id('lead_id_counter')
        leads_db[str(current_id)] = lead_data
        save_json_data(leads_db, LEADS_FILE)

        email_success = send_lead_magnet_email(lead_data, 'errores', intereses)
        send_lead_notification_to_proedent(lead_data, 'errores', intereses)

        if email_success:
            return redirect(url_for('thankyou'))
        else:
            return jsonify({"success": False, "error": "Error enviando la guía"}), 500

    except Exception as e:
        logger.error(f"Error en lead_magnet_errores: {e}")
        return jsonify({"success": False, "error": "Error interno"}), 500


@app.route("/lead_magnet_guia_rx", methods=["GET", "POST"])
def lead_magnet_guia_rx():
    if request.method == "GET":
        return render_template("LM-10GuiaCompleta.html")

    try:
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        telefono = request.form.get("telefono", "")
        intereses = request.form.getlist("intereses")

        if not all([nombre, email]):
            return jsonify({"success": False, "error": "Nombre y email son requeridos"}), 400

        lead_data = {
            'nombre': nombre,
            'email': email,
            'telefono': telefono,
            'magnet_type': 'guia_rx',
            'intereses': intereses,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        current_id = get_next_id('lead_id_counter')
        leads_db[str(current_id)] = lead_data
        save_json_data(leads_db, LEADS_FILE)

        email_success = send_lead_magnet_email(lead_data, 'guia_rx', intereses)
        send_lead_notification_to_proedent(lead_data, 'guia_rx', intereses)

        if email_success:
            return redirect(url_for('thankyou'))
        else:
            return jsonify({"success": False, "error": "Error enviando la guía"}), 500

    except Exception as e:
        logger.error(f"Error en lead_magnet_guia_rx: {e}")
        return jsonify({"success": False, "error": "Error interno"}), 500


@app.route("/sales_recruitment", methods=["GET", "POST"])
def sales_recruitment():
    if request.method == "GET":
        return render_template("LM-Vendedores.html")

    try:
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        telefono = request.form.get("telefono")
        ciudad = request.form.get("ciudad")
        experiencia_sector = request.form.get("experiencia_sector", "")

        if not all([nombre, email, telefono, ciudad]):
            return jsonify({"success": False, "error": "Todos los campos requeridos deben completarse"}), 400

        candidate_data = {
            'nombre': nombre,
            'email': email,
            'telefono': telefono,
            'ciudad': ciudad,
            'experiencia_sector': experiencia_sector,
            'status': 'Pendiente',
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        current_id = get_next_id('sales_recruitment_id_counter')
        sales_recruitment_db[str(current_id)] = candidate_data
        save_json_data(sales_recruitment_db, SALES_CANDIDATES_FILE)

        email_success = send_sales_recruitment_email(candidate_data)
        send_sales_candidate_notification_to_proedent(candidate_data)

        if email_success:
            return redirect(url_for('sales_thankyou'))
        else:
            return jsonify({"success": False, "error": "Error enviando la guía"}), 500

    except Exception as e:
        logger.error(f"Error en sales_recruitment: {e}")
        return jsonify({"success": False, "error": "Error interno"}), 500


@app.route("/sales-thankyou")
def sales_thankyou():
    return render_template("thankyouVendedor.html")


@app.route("/thankyou")
def thankyou():
    return render_template("thankyou.html")


# ==================== RUTA PARA AGENDAMIENTO DE DEMOS ====================

@app.route("/agendar_demo", methods=["POST"])
def agendar_demo():
    try:
        nombre = request.form.get("nombre")
        correo = request.form.get("correo")
        telefono = request.form.get("telefono", "")
        fecha = request.form.get("fecha", "")
        representante = request.form.get("representante")
        mensaje = request.form.get("mensaje", "")

        if not all([nombre, correo, representante]):
            flash("Por favor complete todos los campos requeridos.", "error")
            return redirect(url_for("index"))

        form_data = {
            'nombre': nombre,
            'correo': correo,
            'telefono': telefono,
            'fecha': fecha,
            'representante': representante,
            'mensaje': mensaje
        }

        current_id = get_next_id('appointment_id_counter')
        appointment_data = {
            "id": current_id,
            "nombre": nombre,
            "correo": correo,
            "telefono": telefono,
            "fecha": fecha,
            "representante": representante,
            "mensaje": mensaje,
            "status": "Pendiente",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        appointments_db[str(current_id)] = appointment_data
        save_json_data(appointments_db, APPOINTMENTS_FILE)

        email_success = send_demo_request_email(form_data)
        confirmation_success = send_confirmation_email(form_data)

        if email_success:
            success_msg = f"¡Solicitud recibida exitosamente! Nos pondremos en contacto contigo pronto, {nombre}."
            if confirmation_success:
                success_msg += " También te enviamos un correo de confirmación."
            flash(success_msg, "success")
        else:
            flash(
                f"Solicitud recibida para {nombre}. Sin embargo, hubo un problema enviando la notificación por correo.",
                "warning")

        return redirect(url_for("index"))

    except Exception as e:
        logger.error(f"Error procesando solicitud de demostración: {e}")
        flash("Error procesando tu solicitud. Por favor intenta nuevamente.", "error")
        return redirect(url_for("index"))


# ==================== RUTA PATIENTS CON AUTENTICACIÓN ====================

@app.route("/patients", methods=["GET", "POST"])
def patients():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "admin_login":
            employee_id = request.form.get("employee_id")
            password = request.form.get("password")

            if employee_id == "admin" and password == "admin":
                session['admin_logged_in'] = True
                flash("Acceso administrativo concedido", "success")
                return redirect(url_for("admin_panel"))
            else:
                flash("Credenciales incorrectas", "danger")
                return redirect(url_for("patients"))

        elif action == "register":
            name = request.form.get("name")
            phone = request.form.get("phone")
            email = request.form.get("email")
            clinic = request.form.get("clinic")
            specialty = request.form.get("specialty")

            current_id = get_next_id('patient_id_counter')
            data = {
                "id": current_id,
                "name": name,
                "phone": phone,
                "email": email,
                "clinic": clinic,
                "specialty": specialty
            }
            patients_db[str(current_id)] = data
            save_json_data(patients_db, PATIENTS_FILE)
            flash("Cliente registrado correctamente ✅", "success")

        elif action == "update":
            patient_id = request.form.get("patient_id")
            if patient_id not in patients_db:
                flash("Error: Cliente no encontrado", "danger")
            else:
                name = request.form.get("name")
                phone = request.form.get("phone")
                email = request.form.get("email")
                clinic = request.form.get("clinic")
                specialty = request.form.get("specialty")

                data = {
                    "id": int(patient_id),
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "clinic": clinic,
                    "specialty": specialty
                }
                patients_db[patient_id] = data
                save_json_data(patients_db, PATIENTS_FILE)
                flash("Cliente actualizado correctamente ✅", "success")

        elif action == "delete":
            patient_id = request.form.get("patient_id")
            if patient_id not in patients_db:
                flash("Error: Cliente no encontrado", "danger")
            else:
                del patients_db[patient_id]
                save_json_data(patients_db, PATIENTS_FILE)
                flash("Cliente eliminado correctamente ✅", "success")

        return redirect(url_for("patients"))
    else:
        patients_list = list(patients_db.values())
        return render_template("patients.html", patients=patients_list)


@app.route("/admin_panel")
def admin_panel():
    if not session.get('admin_logged_in'):
        flash("Acceso denegado. Inicie sesión como administrador.", "danger")
        return redirect(url_for("patients"))

    # Estadísticas
    leads_stats = {
        'total_leads': len(leads_db),
        'leads_secretos': len([l for l in leads_db.values() if l.get('magnet_type') == 'secretos']),
        'leads_errores': len([l for l in leads_db.values() if l.get('magnet_type') == 'errores']),
        'leads_guia_rx': len([l for l in leads_db.values() if l.get('magnet_type') == 'guia_rx']),
        'total_appointments': len(appointments_db),
        'total_sales_candidates': len(sales_recruitment_db)
    }

    # Preparar datos para el template
    all_leads = list(leads_db.values())
    all_leads.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    all_appointments = list(appointments_db.values())
    all_appointments.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    all_sales_candidates = list(sales_recruitment_db.values())
    all_sales_candidates.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    return render_template("admin_panel.html",
                           leads=all_leads,
                           appointments=all_appointments,
                           sales_candidates=all_sales_candidates,
                           stats=leads_stats)


@app.route("/admin_logout")
def admin_logout():
    session.pop('admin_logged_in', None)
    flash("Sesión de administrador cerrada", "info")
    return redirect(url_for("patients"))


@app.route("/lm/secretos")
@admin_required
def lm_secretos():
    return render_template("LM-10Secretos.html")


@app.route("/lm/errores")
@admin_required
def lm_errores():
    return render_template("LM-10Errores.html")


@app.route("/lm/guia")
@admin_required
def lm_guia():
    return render_template("LM-GuiaCompleta.html")


# ==================== RUTAS ADICIONALES ====================

@app.route("/solicitudes_demo")
def solicitudes_demo():
    solicitudes = list(appointments_db.values())
    solicitudes.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return render_template("solicitudes_demo.html", solicitudes=solicitudes)


@app.route("/catalogo")
def catalogo():
    category_filter = request.args.get('category', '')
    if category_filter:
        filtered_products = {k: v for k, v in products_db.items() if v['category'] == category_filter}
    else:
        filtered_products = products_db

    categories = list(set([product['category'] for product in products_db.values()]))
    return render_template("catalogo.html", products=filtered_products.values(),
                           categories=categories, current_category=category_filter)


@app.route("/vatech_catalog")
def vatech_catalog():
    return render_template("vatech_catalog.html")


@app.route("/acteon_catalog")
def acteon_catalog():
    return render_template("acteon_catalog.html")


@app.route("/euronda_catalog")
def euronda_catalog():
    return render_template("euronda_catalog.html")


@app.route("/faro_catalog")
def faro_catalog():
    return render_template("faro_catalog.html")


@app.route("/frasaco_catalog")
def frasaco_catalog():
    return render_template("frasaco_catalog.html")


@app.route("/dmg_catalog")
def dmg_catalog():
    return render_template("dmg_catalog.html")


@app.route("/nufona_catalog")
def nufona_catalog():
    return render_template("nufona_catalog.html")


@app.route("/cursos", methods=["GET", "POST"])
def cursos():
    if request.method == "POST":
        course_id = request.form.get("course_id")
        student_name = request.form.get("student_name")
        student_email = request.form.get("student_email")

        if course_id in courses_db:
            if courses_db[course_id]["available_spots"] > 0:
                courses_db[course_id]["available_spots"] -= 1
                save_json_data(courses_db, COURSES_FILE)
                flash(f"Inscripción exitosa para {student_name}", "success")
            else:
                flash("No hay cupos disponibles para este curso", "danger")
        else:
            flash("Curso no encontrado", "danger")
        return redirect(url_for("cursos"))

    return render_template("cursos.html", courses=courses_db.values())


@app.route("/chatindex")
def chatindex():
    return render_template("chatindex.html")


@app.route("/video_conferencia", methods=["GET", "POST"])
def video_conferencia():
    if request.method == "POST":
        pin = request.form.get("pin")
        if pin == "0404":
            client_name = request.form.get("client_name")
            meeting_type = request.form.get("meeting_type")
            return render_template("video_conferencia.html", authorized=True,
                                   client_name=client_name, meeting_type=meeting_type)
        else:
            flash("PIN incorrecto. Intenta nuevamente.", "danger")
            return redirect(url_for("video_conferencia"))
    else:
        return render_template("video_conferencia.html", authorized=False)


@app.route('/download_catalog')
def download_catalog():
    data = []
    for product in products_db.values():
        data.append({
            'Producto': product['name'],
            'Categoría': product['category'],
            'Descripción': product['description'],
            'Precio': product['price'],
            'Especificaciones': product['specifications']
        })

    df = pd.DataFrame(data)
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False, engine='openpyxl')
    excel_file.seek(0)
    return send_file(excel_file, download_name="catalogo_proedent.xlsx", as_attachment=True)


@app.route("/test_email")
def test_email():
    test_data = {
        'nombre': 'Test Cliente',
        'correo': 'test@example.com',
        'telefono': '+593 99 999 9999',
        'representante': 'Byron Velasco (Gerente)- Tomografos, RX, Equipos Dentales',
        'fecha': '2025-01-15',
        'mensaje': 'Este es un mensaje de prueba del sistema.'
    }

    success = send_demo_request_email(test_data)

    return jsonify({
        "status": "success" if success else "error",
        "message": "Email de prueba enviado correctamente" if success else "Error enviando email de prueba",
        "smtp_config": {
            "server": SMTP_SERVER,
            "port": SMTP_PORT,
            "user": EMAIL_USER,
            "password_configured": bool(EMAIL_PASSWORD)
        }
    })


if __name__ == "__main__":
    print("🚀 Iniciando aplicación PROEDENT con persistencia JSON")
    print(f"📧 Email configurado: {'✅' if EMAIL_USER and EMAIL_PASSWORD else '❌'}")
    print(f"🎯 Lead Magnets disponibles:")
    print(f"   - /lead_magnet_secretos")
    print(f"   - /lead_magnet_errores")
    print(f"   - /lead_magnet_guia_rx")
    print(f"   - /sales_recruitment")
    print(f"📊 Panel Admin: /patients (login: admin/admin)")
    print(f"💾 Datos persistentes en carpeta: {DATA_DIR}")

    if EMAIL_USER:
        print(f"📬 Email user: {EMAIL_USER}")

    app.run(host="127.0.0.1", debug=True, port=5000)