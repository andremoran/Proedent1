# http://127.0.0.1:5000/

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
import pandas as pd
import pickle
import os
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
app.secret_key = "clave-secreta-para-flash"  # Clave para mensajes flash

# Configuración de Email
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_USER = os.getenv('EMAIL_USER')  # proedentventasecuador@gmail.com
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')  # password de aplicación

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bases de datos en memoria
patients_db = {}  # Mantener para clientes/pacientes odontológicos
products_db = {}  # Nueva base para catálogo de productos
courses_db = {}  # Nueva base para cursos
appointments_db = {}  # Para citas de demostración
leads_db = {}  # NUEVA: Para leads de lead magnets
sales_recruitment_db = {}

patient_id_counter = 1
product_id_counter = 1
course_id_counter = 1
appointment_id_counter = 1
lead_id_counter = 1
sales_recruitment_id_counter = 1


# Función para enviar correo de lead magnet
def send_lead_magnet_email(lead_data, magnet_type, interests):
    """Enviar correo con lead magnet"""
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD:
            logger.error("Credenciales de email no configuradas")
            return False

        # Mapeo de tipos de lead magnet
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

        # Crear mensaje de email
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
                    <h3 style="color: #2e7d32; margin-top: 0;">📎 Contenido Exclusivo</h3>
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

        # Enviar email
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


# Función para enviar correo de solicitud de demostración
def send_demo_request_email(form_data):
    """Enviar correo con solicitud de demostración/consulta"""
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD:
            logger.error("Credenciales de email no configuradas")
            return False

        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = "proedentventasecuador@gmail.com"
        msg['Subject'] = f"Nueva Solicitud - {form_data['nombre']}"

        # Crear contenido HTML del email
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

                <div style="text-align: center; margin-top: 30px;">
                    <p style="color: #666;">
                        Responde a esta solicitud contactando al cliente lo antes posible.
                    </p>
                </div>
            </div>

            <div style="background: #333; color: white; text-align: center; padding: 15px;">
                <p style="margin: 0;">PROEDENT - Distribuidora de Equipos Dentales</p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_content, 'html'))

        # Conectar y enviar
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


# Función para enviar correo de confirmación al cliente
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

                <div style="background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; color: #2e7d32;">
                        <strong>¿Qué sigue?</strong><br>
                        Nuestro equipo se contactará contigo en las próximas 24 horas para coordinar la demostración o resolver tu consulta.
                    </p>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <p>Si tienes alguna pregunta urgente, puedes contactarnos:</p>
                    <p>
                        📧 proedentventasecuador@gmail.com<br>
                        📱 WhatsApp: <a href="https://wa.me/593998745641" style="color: #5B21B6;">+593 99 874 5641</a>
                    </p>
                </div>
            </div>

            <div style="background: #333; color: white; text-align: center; padding: 15px;">
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

        return True

    except Exception as e:
        logger.error(f"Error enviando confirmación: {e}")
        return False


##############################

def send_sales_recruitment_email(candidate_data):
    """Enviar correo con guía de estudio para vendedores"""
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD:
            logger.error("Credenciales de email no configuradas")
            return False

        # Crear mensaje de email
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
                    <h3 style="color: #059669; margin-top: 0;">📎 Archivo Adjunto:</h3>
                    <p style="color: #047857; margin: 0;"><strong>GUIAvendedores.pdf</strong> - Catálogo completo de productos PROEDENT</p>
                </div>

                <div style="background: #fef3c7; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #f59e0b;">
                    <h3 style="color: #92400e; margin-top: 0;">📋 Próximos Pasos:</h3>
                    <ul style="color: #92400e;">
                        <li>Descarga y estudia la guía PDF adjunta</li>
                        <li>Prepárate para el cuestionario presencial en Quito</li>
                        <li>Tienes 2 oportunidades para aprobar</li>
                    </ul>
                </div>

                <div style="background: white; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #5B21B6;">
                    <h3 style="color: #5B21B6; margin-top: 0;">💰 Comisiones:</h3>
                    <p><strong>Hasta el 15% de comisión por cada venta realizada</strong></p>
                    <p>Ciudad: {candidate_data.get('ciudad', 'No especificada')}</p>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <h3 style="color: #5B21B6;">¿Necesitas capacitación adicional?</h3>
                    <p style="margin: 5px 0;"><strong>📧 Email:</strong> proedentorg@gmail.com, proedentventasecuador@gmail.com</p>
                    <p style="margin: 5px 0;"><strong>📱 WhatsApp:</strong> <a href="https://wa.me/593998745641" style="color: #5B21B6;">+593 98 755 3634, +593 99 874 5641</a></p>
                    <p style="margin: 5px 0;"><strong>💵 Capacitación Adicional Opcional:</strong> Solo $10 USD</p>
                </div>
            </div>

            <div style="background: #333; color: white; text-align: center; padding: 20px;">
                <p style="margin: 0;">PROEDENT - Tu oportunidad de generar ingresos extraordinarios</p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_content, 'html'))

        # ADJUNTAR EL PDF DE LA GUÍA
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
            else:
                logger.warning(f"Archivo PDF no encontrado en: {pdf_path}")
        except Exception as pdf_error:
            logger.error(f"Error adjuntando PDF: {pdf_error}")

        # Enviar email
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
        msg['To'] = "proedentorg@gmail.com"  # Email principal
        msg['Cc'] = "proedentventasecuador@gmail.com"  # Email secundario
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

                <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h4 style="color: #856404; margin-top: 0;">⚡ Acciones Requeridas:</h4>
                    <ul style="color: #856404; margin: 0;">
                        <li>Contactar al candidato para coordinar cuestionario presencial</li>
                        <li>Verificar si requiere capacitación de $10</li>
                        <li>Programar evaluación en oficinas de Quito</li>
                    </ul>
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

##############################

# Datos iniciales del catálogo
def initialize_catalog():
    global product_id_counter
    products = [
        # Productos originales
        {
            "id": 1,
            "name": "Tomógrafo Dental 3D",
            "category": "Diagnóstico por Imagen",
            "brand": "Proedent",
            "description": "Tecnología avanzada de imagen 3D para diagnósticos precisos y planificación de tratamientos",
            "price": "Consultar precio",
            "image": "Picture2.png",
            "specifications": "Resolución: 150 micras, Campo de visión: 16x13cm, Tiempo de escaneo: 8.9 seg"
        },
        {
            "id": 2,
            "name": "Sillón Odontológico Premium",
            "category": "Equipos Principales",
            "brand": "Proedent",
            "description": "Equipamiento de última generación para máximo confort del paciente y eficiencia del profesional",
            "price": "Desde $15,000",
            "image": "Picture4.png",
            "specifications": "Motor eléctrico, LED integrado, Sistema de aspiración, Bandeja flotante"
        },
        {
            "id": 3,
            "name": "Sensor Digital X-Line",
            "category": "Radiología Digital",
            "brand": "Proedent",
            "description": "Radiografía digital instantánea con sensores de alta resolución y mínima radiación",
            "price": "Desde $3,500",
            "image": "Picture3.png",
            "specifications": "Resolución: 20 lp/mm, Conectividad USB, Compatible con todos los software"
        },

        # Productos Vatech
        {
            "id": 4,
            "name": "Vatech A9",
            "category": "Tomografía 3D",
            "brand": "VATECH",
            "description": "A New Dimension Beyond Your Expectations",
            "price": "Consultar precio",
            "image": "vatech/v1.png",
            "specifications": "Tomógrafo CBCT de última generación con tecnología avanzada de imagen 3D"
        },
        {
            "id": 5,
            "name": "Green X",
            "category": "Tomografía 3D",
            "brand": "VATECH",
            "description": "The Next Green Innovation",
            "price": "Consultar precio",
            "image": "vatech/v2.png",
            "specifications": "Sistema de tomografía con tecnología verde y eficiencia energética"
        },
        {
            "id": 6,
            "name": "EzRay Air Portable",
            "category": "Radiología Digital",
            "brand": "VATECH",
            "description": "Lightweight, Portable Innovation",
            "price": "Consultar precio",
            "image": "vatech/v3.png",
            "specifications": "Equipo de rayos X portátil con tecnología inalámbrica avanzada"
        },
        {
            "id": 7,
            "name": "EzRay Air Wall",
            "category": "Radiología Digital",
            "brand": "VATECH",
            "description": "The Smart Essentials For Your Clinic",
            "price": "Consultar precio",
            "image": "vatech/v4.png",
            "specifications": "Sistema de rayos X montado en pared con tecnología inteligente"
        },
        {
            "id": 8,
            "name": "EzRay Chair",
            "category": "Radiología Digital",
            "brand": "VATECH",
            "description": "Standard Intraoral X-ray",
            "price": "Consultar precio",
            "image": "vatech/v5.png",
            "specifications": "Equipo de rayos X intraoral estándar para sillón dental"
        },
        {
            "id": 9,
            "name": "EzSensor HD",
            "category": "Sensores Digitales",
            "brand": "VATECH",
            "description": "Make Your Operation Easier, Faster and More Professional",
            "price": "Consultar precio",
            "image": "vatech/v6.png",
            "specifications": "Sensor digital HD de alta resolución para radiografía intraoral"
        },
        {
            "id": 10,
            "name": "EzSensor Soft",
            "category": "Sensores Digitales",
            "brand": "VATECH",
            "description": "Better Is Not Enough, Be Different",
            "price": "Consultar precio",
            "image": "vatech/v7.png",
            "specifications": "Sensor digital suave y flexible para mayor comodidad del paciente"
        },
        {
            "id": 11,
            "name": "PaX-i Insight",
            "category": "Radiología Panorámica",
            "brand": "VATECH",
            "description": "Beyond 2D, Depth Added Panorama",
            "price": "Consultar precio",
            "image": "vatech/v8.png",
            "specifications": "Equipo panorámico con capacidades de imagen en profundidad"
        },
        {
            "id": 12,
            "name": "PaX-i Plus",
            "category": "Radiología Panorámica",
            "brand": "VATECH",
            "description": "Premium Panoramic Image Quality",
            "price": "Consultar precio",
            "image": "vatech/v9.png",
            "specifications": "Sistema panorámico premium con calidad de imagen superior"
        },
        {
            "id": 13,
            "name": "Green 21",
            "category": "Tomografía 3D",
            "brand": "VATECH",
            "description": "Raising The Bar For Excellence",
            "price": "Consultar precio",
            "image": "vatech/v10.png",
            "specifications": "Tomógrafo CBCT de excelencia con tecnología Green"
        },
        {
            "id": 14,
            "name": "Green 18",
            "category": "Tomografía 3D",
            "brand": "VATECH",
            "description": "Green Innovation For The Next Generation",
            "price": "Consultar precio",
            "image": "vatech/v11.png",
            "specifications": "Sistema de tomografía de nueva generación con innovación verde"
        },
        {
            "id": 15,
            "name": "PaX-i3D Green",
            "category": "Tomografía 3D",
            "brand": "VATECH",
            "description": "The New Digital Environment",
            "price": "Consultar precio",
            "image": "vatech/v12.png",
            "specifications": "Entorno digital 3D con tecnología verde avanzada"
        },
        {
            "id": 16,
            "name": "Green 16",
            "category": "Tomografía 3D",
            "brand": "VATECH",
            "description": "The Next Green Innovation",
            "price": "Consultar precio",
            "image": "vatech/v13.png",
            "specifications": "Innovación verde de próxima generación en tomografía"
        },
        {
            "id": 17,
            "name": "EzSensor Classic",
            "category": "Sensores Digitales",
            "brand": "VATECH",
            "description": "Your Partner For Digital Clinic",
            "price": "Consultar precio",
            "image": "vatech/v14.png",
            "specifications": "Sensor digital clásico confiable para clínicas digitales"
        },
        {
            "id": 18,
            "name": "PaX-i",
            "category": "Radiología Panorámica",
            "brand": "VATECH",
            "description": "Your Partner In Digital Success",
            "price": "Consultar precio",
            "image": "vatech/v15.png",
            "specifications": "Sistema panorámico líder para el éxito digital - PRODUCTO DESTACADO"
        },
        {
            "id": 19,
            "name": "Smart Plus",
            "category": "Tomografía 3D",
            "brand": "VATECH",
            "description": "The innovative FOV of Smart Plus provides an arch-shaped volume",
            "price": "Consultar precio",
            "image": "vatech/v16.png",
            "specifications": "FOV innovador con volumen en forma de arco para diagnósticos precisos"
        },
        {
            "id": 20,
            "name": "PaX-i3D Smart",
            "category": "Tomografía 3D",
            "brand": "VATECH",
            "description": "No More than what you want, No Less than what you need",
            "price": "Consultar precio",
            "image": "vatech/v17.png",
            "specifications": "Sistema 3D inteligente optimizado para necesidades específicas"
        },
        {
            "id": 21,
            "name": "PaX-i3D",
            "category": "Tomografía 3D",
            "brand": "VATECH",
            "description": "Your First Partner For 3D Diagnosis",
            "price": "Consultar precio",
            "image": "vatech/v18.png",
            "specifications": "Primer socio confiable para diagnósticos 3D profesionales"
        }
    ]

    for product in products:
        products_db[product["id"]] = product
    product_id_counter = 22


# Datos iniciales de cursos
def initialize_courses():
    global course_id_counter
    courses = [
        {
            "id": 1,
            "name": "Introducción a la Radiología Digital",
            "duration": "8 horas",
            "instructor": "Dr. Carlos Mendoza",
            "description": "Curso completo sobre el uso de sensores digitales y software de radiología",
            "price": "$150",
            "date": "2025-09-15",
            "available_spots": 15
        },
        {
            "id": 2,
            "name": "Mantenimiento de Equipos Dentales",
            "duration": "12 horas",
            "instructor": "Ing. Roberto Silva",
            "description": "Aprenda a mantener y calibrar sus equipos dentales para máximo rendimiento",
            "price": "$200",
            "date": "2025-09-22",
            "available_spots": 10
        }
    ]

    for course in courses:
        courses_db[course["id"]] = course
    course_id_counter = 3


# Inicializar datos
initialize_catalog()
initialize_courses()


# ----- Rutas principales -----

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

        global lead_id_counter
        leads_db[lead_id_counter] = lead_data
        lead_id_counter += 1

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

        global lead_id_counter
        leads_db[lead_id_counter] = lead_data
        lead_id_counter += 1

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

        global lead_id_counter
        leads_db[lead_id_counter] = lead_data
        lead_id_counter += 1

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

        global sales_recruitment_id_counter
        sales_recruitment_db[sales_recruitment_id_counter] = candidate_data
        sales_recruitment_id_counter += 1

        # Enviar emails
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
    """Página de agradecimiento para candidatos a vendedores"""
    return render_template("thankyouVendedor.html")


@app.route("/thankyou")
def thankyou():
    """Página de agradecimiento después de descargar lead magnet"""
    return render_template("thankyou.html")

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash("Acceso restringido. Inicia sesión como administrador.", "warning")
            return redirect(url_for('patients'))
        return view_func(*args, **kwargs)
    return wrapper

# --- en cualquier lugar después de crear 'app' ---
@app.route("/lm/secretos")
@admin_required
def lm_secretos():
    return render_template("LM-10Secretos.html")

@app.route("/lm/errores")
@admin_required
def lm_errores():
    # Si prefieres, puedes reutilizar 'LM-10Errores.html' tal cual
    return render_template("LM-10Errores.html")

@app.route("/lm/guia")
@admin_required
def lm_guia():
    return render_template("LM-GuiaCompleta.html")

# Endpoint ACTUALIZADO para solicitud de demostración con envío de correo
@app.route("/agendar_demo", methods=["POST"])
def agendar_demo():
    try:
        # Obtener datos del formulario (incluyendo nuevos campos)
        nombre = request.form.get("nombre")
        correo = request.form.get("correo")
        telefono = request.form.get("telefono", "")  # Nuevo campo
        fecha = request.form.get("fecha", "")
        representante = request.form.get("representante")
        mensaje = request.form.get("mensaje", "")  # Nuevo campo

        # Validar campos requeridos
        if not all([nombre, correo, representante]):
            flash("Por favor complete todos los campos requeridos.", "error")
            return redirect(url_for("index"))

        # Preparar datos para el correo
        form_data = {
            'nombre': nombre,
            'correo': correo,
            'telefono': telefono,
            'fecha': fecha,
            'representante': representante,
            'mensaje': mensaje
        }

        # Guardar en base de datos local
        global appointment_id_counter
        appointment_data = {
            "id": appointment_id_counter,
            "nombre": nombre,
            "correo": correo,
            "telefono": telefono,
            "fecha": fecha,
            "representante": representante,
            "mensaje": mensaje,
            "status": "Pendiente",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        appointments_db[appointment_id_counter] = appointment_data
        appointment_id_counter += 1

        # Intentar enviar correo
        email_success = send_demo_request_email(form_data)
        confirmation_success = send_confirmation_email(form_data)

        if email_success:
            # Mostrar mensaje de éxito
            success_msg = f"¡Solicitud recibida exitosamente! Nos pondremos en contacto contigo pronto, {nombre}."
            if confirmation_success:
                success_msg += " También te enviamos un correo de confirmación."

            flash(success_msg, "success")
            logger.info(f"Solicitud procesada para {nombre} - Email enviado: {email_success}")
        else:
            # Aún así guardar la solicitud, pero advertir sobre el email
            flash(
                f"Solicitud recibida para {nombre}. Sin embargo, hubo un problema enviando la notificación por correo.",
                "warning")
            logger.warning(f"Solicitud guardada pero email falló para {nombre}")

        return redirect(url_for("index"))

    except Exception as e:
        logger.error(f"Error procesando solicitud de demostración: {e}")
        flash("Error procesando tu solicitud. Por favor intenta nuevamente.", "error")
        return redirect(url_for("index"))


# ==================== RUTA PATIENTS MODIFICADA CON AUTENTICACIÓN ADMIN ====================
@app.route("/patients", methods=["GET", "POST"])
def patients():
    if request.method == "POST":
        action = request.form.get("action")

        # NUEVO: Manejar login de admin
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

        # Resto de acciones existentes para patients
        elif action == "register":
            name = request.form.get("name")
            phone = request.form.get("phone")
            email = request.form.get("email")
            clinic = request.form.get("clinic")
            specialty = request.form.get("specialty")

            data = {
                "name": name,
                "phone": phone,
                "email": email,
                "clinic": clinic,
                "specialty": specialty
            }
            global patient_id_counter
            data["id"] = patient_id_counter
            patients_db[patient_id_counter] = data
            patient_id_counter += 1
            flash("Cliente registrado correctamente ✅", "success")
        elif action == "update":
            patient_id = int(request.form.get("patient_id"))
            if patient_id not in patients_db:
                flash("Error: Cliente no encontrado", "danger")
            else:
                name = request.form.get("name")
                phone = request.form.get("phone")
                email = request.form.get("email")
                clinic = request.form.get("clinic")
                specialty = request.form.get("specialty")

                data = {
                    "id": patient_id,
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "clinic": clinic,
                    "specialty": specialty
                }
                patients_db[patient_id] = data
                flash("Cliente actualizado correctamente ✅", "success")
        elif action == "delete":
            patient_id = int(request.form.get("patient_id"))
            if patient_id not in patients_db:
                flash("Error: Cliente no encontrado", "danger")
            else:
                del patients_db[patient_id]
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

    # Estadísticas actualizadas
    leads_stats = {
        'total_leads': len(leads_db),
        'leads_secretos': len([l for l in leads_db.values() if l.get('magnet_type') == 'secretos']),
        'leads_errores': len([l for l in leads_db.values() if l.get('magnet_type') == 'errores']),
        'leads_guia_rx': len([l for l in leads_db.values() if l.get('magnet_type') == 'guia_rx']),
        'total_appointments': len(appointments_db),
        'total_sales_candidates': len(sales_recruitment_db)  # NUEVA
    }

    # Datos existentes
    all_leads = list(leads_db.values())
    all_leads.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    all_appointments = list(appointments_db.values())
    all_appointments.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    # NUEVOS: Candidatos a vendedores
    all_sales_candidates = list(sales_recruitment_db.values())
    all_sales_candidates.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    return render_template("admin_panel.html",
                           leads=all_leads,
                           appointments=all_appointments,
                           sales_candidates=all_sales_candidates,  # NUEVA
                           stats=leads_stats)


# NUEVA: Ruta para cerrar sesión de admin
@app.route("/admin_logout")
def admin_logout():
    session.pop('admin_logged_in', None)
    flash("Sesión de administrador cerrada", "info")
    return redirect(url_for("patients"))


# Nueva ruta para ver las solicitudes de demostración
@app.route("/solicitudes_demo")
def solicitudes_demo():
    """Ver todas las solicitudes de demostración recibidas"""
    solicitudes = list(appointments_db.values())
    # Ordenar por fecha de creación (más recientes primero)
    solicitudes.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return render_template("solicitudes_demo.html", solicitudes=solicitudes)


@app.route("/catalogo")
def catalogo():
    category_filter = request.args.get('category', '')
    if category_filter:
        filtered_products = {k: v for k, v in products_db.items() if v['category'] == category_filter}
    else:
        filtered_products = products_db

    # Obtener todas las categorías para el filtro
    categories = list(set([product['category'] for product in products_db.values()]))

    return render_template("catalogo.html", products=filtered_products.values(), categories=categories,
                           current_category=category_filter)


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
        course_id = int(request.form.get("course_id"))
        student_name = request.form.get("student_name")
        student_email = request.form.get("student_email")

        if course_id in courses_db:
            if courses_db[course_id]["available_spots"] > 0:
                courses_db[course_id]["available_spots"] -= 1
                flash(f"Inscripción exitosa para {student_name} en el curso {courses_db[course_id]['name']}", "success")
            else:
                flash("Lo sentimos, no hay cupos disponibles para este curso", "danger")
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
            return render_template("video_conferencia.html", authorized=True, client_name=client_name,
                                   meeting_type=meeting_type)
        else:
            flash("PIN incorrecto. Intenta nuevamente.", "danger")
            return redirect(url_for("video_conferencia"))
    else:
        return render_template("video_conferencia.html", authorized=False)


@app.route('/download_catalog')
def download_catalog():
    # Crear un Excel con el catálogo completo
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


# Endpoint para probar configuración de email
@app.route("/test_email")
def test_email():
    """Endpoint para probar la configuración de email"""
    test_data = {
        'nombre': 'Test Cliente',
        'correo': 'test@example.com',
        'telefono': '+593 99 999 9999',
        'representante': 'Byron Velasco (Gerente)- Tomografos, RX, Equipos Dentales',
        'fecha': '2025-01-15',
        'mensaje': 'Este es un mensaje de prueba del sistema.'
    }

    success = send_demo_request_email(test_data)

    if success:
        return jsonify({
            "status": "success",
            "message": "Email de prueba enviado correctamente",
            "smtp_config": {
                "server": SMTP_SERVER,
                "port": SMTP_PORT,
                "user": EMAIL_USER,
                "password_configured": bool(EMAIL_PASSWORD)
            }
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Error enviando email de prueba",
            "smtp_config": {
                "server": SMTP_SERVER,
                "port": SMTP_PORT,
                "user": EMAIL_USER,
                "password_configured": bool(EMAIL_PASSWORD)
            }
        }), 500


if __name__ == "__main__":
    print("Iniciando aplicación Proedent en http://127.0.0.1:5000")
    print(f"Email configurado: {'✅' if EMAIL_USER and EMAIL_PASSWORD else '❌'}")
    print(f"🎯 Lead Magnets disponibles:")
    print(f"   - /lead_magnet_secretos")
    print(f"   - /lead_magnet_errores")
    print(f"   - /lead_magnet_guia_rx")
    print(f"📊 Panel Admin: /patients (login: admin/admin)")
    if EMAIL_USER:
        print(f"Email user: {EMAIL_USER}")
    app.run(host="127.0.0.1", debug=True, port=5000)