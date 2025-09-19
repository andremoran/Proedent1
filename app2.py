# app2.py con integración Supabase
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
import pandas as pd
import os
import json
from datetime import datetime
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
from functools import wraps
import logging

# NUEVA IMPORTACIÓN PARA SUPABASE
from supabase import create_client, Client

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = "clave-secreta-para-flash"

# Configuración de Email
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# CONFIGURACIÓN SUPABASE
SUPABASE_URL = os.getenv('SUPABASE_URL')  # Tu Project URL
SUPABASE_KEY = os.getenv('SUPABASE_KEY')  # Tu API Key
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# CLASE PARA MANEJAR OPERACIONES DE BASE DE DATOS
class DatabaseManager:
    def __init__(self):
        self.supabase = supabase

    # LEADS OPERATIONS
    def create_lead(self, lead_data):
        try:
            result = self.supabase.table('leads').insert(lead_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating lead: {e}")
            return None

    def get_all_leads(self):
        try:
            result = self.supabase.table('leads').select('*').order('created_at', desc=True).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching leads: {e}")
            return []

    def get_leads_stats(self):
        try:
            all_leads = self.get_all_leads()
            return {
                'total_leads': len(all_leads),
                'leads_secretos': len([l for l in all_leads if l.get('magnet_type') == 'secretos']),
                'leads_errores': len([l for l in all_leads if l.get('magnet_type') == 'errores']),
                'leads_guia_rx': len([l for l in all_leads if l.get('magnet_type') == 'guia_rx']),
            }
        except Exception as e:
            logger.error(f"Error getting leads stats: {e}")
            return {'total_leads': 0, 'leads_secretos': 0, 'leads_errores': 0, 'leads_guia_rx': 0}

    # APPOINTMENTS OPERATIONS
    def create_appointment(self, appointment_data):
        try:
            result = self.supabase.table('appointments').insert(appointment_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            return None

    def get_all_appointments(self):
        try:
            result = self.supabase.table('appointments').select('*').order('created_at', desc=True).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching appointments: {e}")
            return []

    # SALES CANDIDATES OPERATIONS
    def create_sales_candidate(self, candidate_data):
        try:
            result = self.supabase.table('sales_candidates').insert(candidate_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating sales candidate: {e}")
            return None

    def get_all_sales_candidates(self):
        try:
            result = self.supabase.table('sales_candidates').select('*').order('created_at', desc=True).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching sales candidates: {e}")
            return []

    # PATIENTS OPERATIONS
    def create_patient(self, patient_data):
        try:
            result = self.supabase.table('patients').insert(patient_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating patient: {e}")
            return None

    def get_all_patients(self):
        try:
            result = self.supabase.table('patients').select('*').order('created_at', desc=True).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching patients: {e}")
            return []

    def update_patient(self, patient_id, patient_data):
        try:
            result = self.supabase.table('patients').update(patient_data).eq('id', patient_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating patient: {e}")
            return None

    def delete_patient(self, patient_id):
        try:
            result = self.supabase.table('patients').delete().eq('id', patient_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting patient: {e}")
            return False

    # PRODUCTS OPERATIONS
    def get_all_products(self):
        try:
            result = self.supabase.table('products').select('*').execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            return []

    # COURSES OPERATIONS
    def get_all_courses(self):
        try:
            result = self.supabase.table('courses').select('*').execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching courses: {e}")
            return []

    def update_course_spots(self, course_id, spots):
        try:
            result = self.supabase.table('courses').update({'available_spots': spots}).eq('id', course_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating course spots: {e}")
            return None


# Instancia global del manejador de base de datos
db = DatabaseManager()


# [Mantener todas las funciones de email existentes sin cambios]
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
                    ¡Perfecto! Tu guía especializada está lista. 
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <h3 style="color: #5B21B6;">¿Necesitas una demostración personalizada?</h3>
                    <p style="margin: 5px 0;"><strong>📧 Email:</strong> proedentventasecuador@gmail.com</p>
                    <p style="margin: 5px 0;"><strong>📱 WhatsApp:</strong> <a href="https://wa.me/593998745641" style="color: #5B21B6;">+593 99 874 5641</a></p>
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
        logger.error(f"Error enviando email: {e}")
        return False


def send_lead_notification_to_proedent(lead_data, magnet_type, interests):
    """Enviar notificación de nuevo lead a PROEDENT"""
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD:
            return False

        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = "proedentventasecuador@gmail.com"
        msg['Subject'] = f"🎯 Nuevo Lead: {lead_data['nombre']}"

        html_content = f"""
        <p>Nuevo lead capturado:</p>
        <p><strong>Nombre:</strong> {lead_data['nombre']}</p>
        <p><strong>Email:</strong> {lead_data['email']}</p>
        <p><strong>Tipo:</strong> {magnet_type}</p>
        """

        msg.attach(MIMEText(html_content, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        return True
    except Exception as e:
        logger.error(f"Error enviando notificación: {e}")
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


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash("Acceso restringido. Inicia sesión como administrador.", "warning")
            return redirect(url_for('patients'))
        return view_func(*args, **kwargs)

    return wrapper


# RUTAS PRINCIPALES
@app.route("/")
def index():
    return render_template("index.html")


# RUTAS LEAD MAGNETS - ACTUALIZADAS CON SUPABASE
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
            'intereses': intereses
        }

        # GUARDAR EN SUPABASE
        created_lead = db.create_lead(lead_data)

        if created_lead:
            email_success = send_lead_magnet_email(lead_data, 'secretos', intereses)
            send_lead_notification_to_proedent(lead_data, 'secretos', intereses)

            if email_success:
                return redirect(url_for('thankyou'))
            else:
                return jsonify({"success": False, "error": "Error enviando la guía"}), 500
        else:
            return jsonify({"success": False, "error": "Error guardando lead"}), 500

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
            'intereses': intereses
        }

        created_lead = db.create_lead(lead_data)

        if created_lead:
            email_success = send_lead_magnet_email(lead_data, 'errores', intereses)
            send_lead_notification_to_proedent(lead_data, 'errores', intereses)

            if email_success:
                return redirect(url_for('thankyou'))

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
            'intereses': intereses
        }

        created_lead = db.create_lead(lead_data)

        if created_lead:
            email_success = send_lead_magnet_email(lead_data, 'guia_rx', intereses)
            send_lead_notification_to_proedent(lead_data, 'guia_rx', intereses)

            if email_success:
                return redirect(url_for('thankyou'))

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

        # GUARDAR EN SUPABASE (esto ya funciona según los logs)
        try:
            response = supabase.table('sales_candidates').insert(candidate_data).execute()
            logger.info(f"Candidato guardado en Supabase: {nombre}")
        except Exception as db_error:
            logger.error(f"Error guardando en Supabase: {db_error}")
            return jsonify({"success": False, "error": "Error guardando datos"}), 500

        # ENVIAR EMAILS - ESTA PARTE FALTA EN TU CÓDIGO ACTUAL
        logger.info(f"Intentando enviar email a candidato: {email}")
        email_success = send_sales_recruitment_email(candidate_data)

        logger.info(f"Intentando enviar notificación a PROEDENT")
        notification_success = send_sales_candidate_notification_to_proedent(candidate_data)

        if email_success:
            logger.info(f"Email enviado exitosamente a: {email}")
            return redirect(url_for('sales_thankyou'))
        else:
            logger.error(f"Error enviando email a: {email}")
            return jsonify({"success": False, "error": "Error enviando la guía"}), 500

    except Exception as e:
        logger.error(f"Error en sales_recruitment: {e}")
        return jsonify({"success": False, "error": "Error interno"}), 500

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

        appointment_data = {
            "nombre": nombre,
            "correo": correo,
            "telefono": telefono,
            "fecha": fecha if fecha else None,
            "representante": representante,
            "mensaje": mensaje,
            "status": "Pendiente"
        }

        created_appointment = db.create_appointment(appointment_data)

        if created_appointment:
            flash(f"¡Solicitud recibida exitosamente! Nos pondremos en contacto contigo pronto, {nombre}.", "success")
        else:
            flash("Error procesando tu solicitud. Por favor intenta nuevamente.", "error")

        return redirect(url_for("index"))

    except Exception as e:
        logger.error(f"Error procesando solicitud: {e}")
        flash("Error procesando tu solicitud. Por favor intenta nuevamente.", "error")
        return redirect(url_for("index"))


# RUTAS DE ADMINISTRACIÓN - ACTUALIZADAS CON SUPABASE
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

        elif action == "register":
            patient_data = {
                "name": request.form.get("name"),
                "phone": request.form.get("phone"),
                "email": request.form.get("email"),
                "clinic": request.form.get("clinic"),
                "specialty": request.form.get("specialty")
            }

            created_patient = db.create_patient(patient_data)
            if created_patient:
                flash("Cliente registrado correctamente ✅", "success")
            else:
                flash("Error registrando cliente", "danger")

        elif action == "update":
            patient_id = int(request.form.get("patient_id"))
            patient_data = {
                "name": request.form.get("name"),
                "phone": request.form.get("phone"),
                "email": request.form.get("email"),
                "clinic": request.form.get("clinic"),
                "specialty": request.form.get("specialty")
            }

            updated_patient = db.update_patient(patient_id, patient_data)
            if updated_patient:
                flash("Cliente actualizado correctamente ✅", "success")
            else:
                flash("Error actualizando cliente", "danger")

        elif action == "delete":
            patient_id = int(request.form.get("patient_id"))

            deleted = db.delete_patient(patient_id)
            if deleted:
                flash("Cliente eliminado correctamente ✅", "success")
            else:
                flash("Error eliminando cliente", "danger")

        return redirect(url_for("patients"))
    else:
        patients_list = db.get_all_patients()
        return render_template("patients.html", patients=patients_list)


@app.route("/admin_panel")
def admin_panel():
    if not session.get('admin_logged_in'):
        flash("Acceso denegado. Inicie sesión como administrador.", "danger")
        return redirect(url_for("patients"))

    # Obtener datos desde Supabase
    leads = db.get_all_leads()
    appointments = db.get_all_appointments()
    sales_candidates = db.get_all_sales_candidates()

    # Calcular estadísticas
    stats = db.get_leads_stats()
    stats['total_appointments'] = len(appointments)
    stats['total_sales_candidates'] = len(sales_candidates)

    return render_template("admin_panel.html",
                           leads=leads,
                           appointments=appointments,
                           sales_candidates=sales_candidates,
                           stats=stats)


@app.route("/thankyou")
def thankyou():
    return render_template("thankyou.html")


@app.route("/sales-thankyou")
def sales_thankyou():
    return render_template("thankyouVendedor.html")


# RUTAS DEL CATÁLOGO Y OTRAS PÁGINAS FALTANTES
@app.route("/catalogo")
def catalogo():
    """Catálogo completo de productos"""
    category_filter = request.args.get('category', '')
    products = db.get_all_products()

    if category_filter:
        filtered_products = [p for p in products if p.get('category') == category_filter]
    else:
        filtered_products = products

    # Obtener categorías únicas
    categories = list(set([product.get('category', '') for product in products if product.get('category')]))

    return render_template("catalogo.html",
                           products=filtered_products,
                           categories=categories,
                           current_category=category_filter)


@app.route("/vatech_catalog")
def vatech_catalog():
    """Catálogo específico de VATECH"""
    return render_template("vatech_catalog.html")


@app.route("/acteon_catalog")
def acteon_catalog():
    """Catálogo específico de ACTEON"""
    return render_template("acteon_catalog.html")


@app.route("/euronda_catalog")
def euronda_catalog():
    """Catálogo específico de EURONDA"""
    return render_template("euronda_catalog.html")


@app.route("/faro_catalog")
def faro_catalog():
    """Catálogo específico de FARO"""
    return render_template("faro_catalog.html")


@app.route("/frasaco_catalog")
def frasaco_catalog():
    """Catálogo específico de FRASACO"""
    return render_template("frasaco_catalog.html")


@app.route("/dmg_catalog")
def dmg_catalog():
    """Catálogo específico de DMG"""
    return render_template("dmg_catalog.html")


@app.route("/nufona_catalog")
def nufona_catalog():
    """Catálogo específico de NUFONA"""
    return render_template("nufona_catalog.html")


@app.route("/cursos", methods=["GET", "POST"])
def cursos():
    """Página de cursos"""
    if request.method == "POST":
        course_id = int(request.form.get("course_id"))
        student_name = request.form.get("student_name")
        student_email = request.form.get("student_email")

        courses = db.get_all_courses()
        course = next((c for c in courses if c['id'] == course_id), None)

        if course and course["available_spots"] > 0:
            new_spots = course["available_spots"] - 1
            updated_course = db.update_course_spots(course_id, new_spots)

            if updated_course:
                flash(f"Inscripción exitosa para {student_name} en el curso {course['name']}", "success")
            else:
                flash("Error procesando la inscripción", "danger")
        else:
            flash("Lo sentimos, no hay cupos disponibles para este curso", "danger")

        return redirect(url_for("cursos"))

    courses = db.get_all_courses()
    return render_template("cursos.html", courses=courses)


@app.route("/solicitudes_demo")
def solicitudes_demo():
    """Ver todas las solicitudes de demostración"""
    solicitudes = db.get_all_appointments()
    return render_template("solicitudes_demo.html", solicitudes=solicitudes)


@app.route("/chatindex")
def chatindex():
    """Página de chat"""
    return render_template("chatindex.html")


@app.route("/video_conferencia", methods=["GET", "POST"])
def video_conferencia():
    """Página de videoconferencia"""
    if request.method == "POST":
        pin = request.form.get("pin")
        if pin == "0404":
            client_name = request.form.get("client_name")
            meeting_type = request.form.get("meeting_type")
            return render_template("video_conferencia.html",
                                   authorized=True,
                                   client_name=client_name,
                                   meeting_type=meeting_type)
        else:
            flash("PIN incorrecto. Intenta nuevamente.", "danger")
            return redirect(url_for("video_conferencia"))
    else:
        return render_template("video_conferencia.html", authorized=False)


@app.route('/download_catalog')
def download_catalog():
    """Descargar catálogo en Excel"""
    products = db.get_all_products()

    data = []
    for product in products:
        data.append({
            'Producto': product.get('name', ''),
            'Categoría': product.get('category', ''),
            'Marca': product.get('brand', ''),
            'Descripción': product.get('description', ''),
            'Precio': product.get('price', ''),
            'Especificaciones': product.get('specifications', '')
        })

    df = pd.DataFrame(data)
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False, engine='openpyxl')
    excel_file.seek(0)
    return send_file(excel_file, download_name="catalogo_proedent.xlsx", as_attachment=True)


@app.route("/test_email")
def test_email():
    """Endpoint para probar configuración de email"""
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


# Rutas de administrador requerido
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


@app.route("/admin_logout")
def admin_logout():
    """Cerrar sesión de administrador"""
    session.pop('admin_logged_in', None)
    flash("Sesión de administrador cerrada", "info")
    return redirect(url_for("patients"))


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 INICIANDO APLICACIÓN PROEDENT CON SUPABASE")
    print("=" * 60)
    print(f"📍 URL: http://127.0.0.1:5000")
    print(f"📧 Email configurado: {'✅' if EMAIL_USER and EMAIL_PASSWORD else '❌'}")
    print(f"🗄️  Supabase configurado: {'✅' if SUPABASE_URL and SUPABASE_KEY else '❌'}")
    print(f"🎯 Lead Magnets disponibles:")
    print(f"   - /lead_magnet_secretos")
    print(f"   - /lead_magnet_errores")
    print(f"   - /lead_magnet_guia_rx")
    print(f"   - /sales_recruitment")
    print(f"📊 Panel Admin: /patients (admin/admin)")
    print("=" * 60)

    app.run(host="127.0.0.1", debug=True, port=5000)