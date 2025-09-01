# http://127.0.0.1:5000/

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import pandas as pd
import pickle
import os
from datetime import datetime
import random
from io import BytesIO
import uuid

app = Flask(__name__)
app.secret_key = "clave-secreta-para-flash"  # Clave para mensajes flash

# Bases de datos en memoria
patients_db = {}  # Mantener para clientes/pacientes odontológicos
products_db = {}  # Nueva base para catálogo de productos
courses_db = {}  # Nueva base para cursos
appointments_db = {}  # Para citas de demostración

patient_id_counter = 1
product_id_counter = 1
course_id_counter = 1
appointment_id_counter = 1


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


# Endpoint para solicitud de demostración
@app.route("/agendar_demo", methods=["POST"])
def agendar_demo():
    nombre = request.form.get("nombre")
    correo = request.form.get("correo")
    fecha = request.form.get("fecha")
    representante = request.form.get("representante")

    global appointment_id_counter
    appointment_data = {
        "id": appointment_id_counter,
        "nombre": nombre,
        "correo": correo,
        "fecha": fecha,
        "representante": representante,
        "status": "Pendiente"
    }
    appointments_db[appointment_id_counter] = appointment_data
    appointment_id_counter += 1

    flash(f"Solicitud de demostración recibida para {nombre} con {representante} en la fecha {fecha}.", "success")
    return redirect(url_for("index"))


@app.route("/patients", methods=["GET", "POST"])
def patients():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "register":
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


if __name__ == "__main__":
    print("Iniciando aplicación Proedent en http://127.0.0.1:5000")
    app.run(host="127.0.0.1", debug=True, port=5000)