import csv
from flask import Flask, render_template, request, session,jsonify
from datetime import datetime, timedelta
import random
import os

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'

UPLOAD_FOLDER = 'tmp'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/archivos_tmp')
def listar_archivos_tmp():
    archivos = os.listdir('/tmp')
    html = "<h2>Archivos en /tmp</h2><ul>"
    for archivo in archivos:
        html += f'<li><a href="/descargar/{archivo}">{archivo}</a></li>'
    html += "</ul>"
    return html

@app.route('/guardar-pdf', methods=['POST'])
def guardar_pdf():
    if 'pdf' not in request.files:
        print("❌ No se recibió ningún archivo")
        return jsonify({'error': 'No se recibió ningún archivo'}), 400

    file = request.files['pdf']
    filename = file.filename

    # Verifica que tenga nombre y sea un PDF
    if not filename.endswith('.pdf'):
        print("❌ Archivo no válido:", filename)
        return jsonify({'error': 'Formato no válido, solo se aceptan PDFs'}), 400

    try:
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        print(f"✅ Archivo guardado: {filename}")
        return jsonify({'message': 'Archivo guardado correctamente', 'filename': filename}), 200
    except Exception as e:
        print("❌ Error al guardar:", str(e))
        return jsonify({'error': 'No se pudo guardar el archivo'}), 500



def registrar_usuario(datos, calificacion):
    # Definir el archivo donde se almacenarán los registros
    archivo = 'usuarios_examen.csv'
    
    # Obtener la fecha y hora actual
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Obtener los datos del usuario
    usuario = [
        datos['nombre'],
        datos['correo'],
        datos['grado'],
        datos['grupo'],
        fecha_hora,
        calificacion
    ]
    
    # Si el archivo no existe, crearlo y agregar encabezados
    try:
        with open(archivo, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Si el archivo está vacío, agregar encabezados
            if file.tell() == 0:
                writer.writerow(['Nombre', 'Correo', 'Grado', 'Grupo', 'Fecha y Hora', 'Calificación'])
            
            # Escribir la nueva línea con los datos del usuario
            writer.writerow(usuario)
    
    except Exception as e:
        print(f"Error al escribir el archivo CSV: {e}")


def cargar_preguntas():
    preguntas = []
    with open('preguntas.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Omitir encabezado
        for row in reader:
            pregunta = {
                'pregunta': row[0],
                'opciones': row[1:5],  # Las 4 opciones
                'respuesta': row[5]
            }
            preguntas.append(pregunta)
    return preguntas

@app.route('/')
def inicio():
    return render_template('inicio.html')
    
@app.route('/formulario')
def formulario():
    return render_template('formulario.html')

@app.route('/examen', methods=['POST'])
def examen():
    nombre = request.form['nombre']
    correo = request.form['correo']
    grado = request.form['grado']
    grupo = request.form['grupo']

    preguntas = cargar_preguntas()
    seleccionadas = random.sample(preguntas, 15)

    # Agregar índice a cada pregunta seleccionada
    for i, pregunta in enumerate(seleccionadas):
        pregunta['indice'] = i

    session['datos'] = {
        'nombre': nombre,
        'correo': correo,
        'grado': grado,
        'grupo': grupo,
        'preguntas': seleccionadas
    }
    session['inicio_examen'] = datetime.now().isoformat()
    session['examen_enviado'] = False

    return render_template('examen.html', preguntas=seleccionadas)

@app.route('/resultado', methods=['POST'])
def resultado():
    if session.get('examen_enviado'):
        return "Examen ya enviado.", 403

    inicio = session.get('inicio_examen')
    if not inicio:
        return "No se encontró la hora de inicio.", 400

    ahora = datetime.now()
    inicio_dt = datetime.fromisoformat(inicio)
    tiempo_maximo = timedelta(minutes=2)

    

    # Aquí sigue tu lógica para calificar, generar PDF y guardar CSV
    
    datos = session.get('datos')
    respuestas = {}
    correctas = 0

    for i, pregunta in enumerate(datos['preguntas']):
        clave = f"pregunta_{i}"
        respuesta = request.form.get(clave, '')
        respuestas[clave] = respuesta
        if respuesta.strip().lower() == pregunta['respuesta'].strip().lower():
            correctas += 1

    calificacion = round(correctas * 10 / 15, 2)

    # Registrar los datos del usuario en el CSV
    registrar_usuario(datos, calificacion)
    if ahora - inicio_dt > tiempo_maximo:
        return render_template('reporte.html', datos=datos, respuestas=respuestas, calificacion=calificacion)
    session['examen_enviado'] = True  # bloquear reintentos
    return render_template('reporte.html', datos=datos, respuestas=respuestas, calificacion=calificacion)


if __name__ == '__main__':
    #app.run(debug=True)
    #app.run(host='0.0.0.0', port=5000, debug=True)
    app.run(host="0.0.0.0", port=5000, threaded=True)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
