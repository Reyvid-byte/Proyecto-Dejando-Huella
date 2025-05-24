import json
import os
from datetime import datetime, timedelta
import shutil
from typing import Any

FORO_JSON = "foro.json"
USUARIOS_JSON = "usuarios.json"
CIUDADANOS_JSON = "ciudadanos.json"
RESCATISTAS_JSON = "rescatistas.json"
ALBERGUE_JSON = "albergue.json"
ANIMALES_JSON = "animales.json"
SOLICITUDES_REFUGIO_JSON = "solicitudes_refugio.json"
ADOPCIONES_JSON = "adopciones.json"
SOLICITUDES_ADOPCION_JSON = "solicitudes_adopcion.json"


class EstadoSesion:
    usuario: dict[str, Any] = None

def cargar_datos(archivo):
    if not os.path.exists(archivo):
        return []
    try:
        with open(archivo, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def guardar_datos(archivo, datos):
    with open(archivo, "w") as f:
        json.dump(datos, f, indent=4)

class Usuario:

    def __init__(self, nombre,correo,password, tipo):
        self.nombre = nombre
        self.correo = correo
        self.password = password
        self.tipo = tipo

    @staticmethod
    def registrarse(nombre, correo, password, tipo):
        usuarios = cargar_datos(USUARIOS_JSON)
        
        # Validaciones existentes
        if not nombre or not correo or not password:
            return False, "Todos los campos son obligatorios"
        
        if any(u["nombre"] == nombre for u in usuarios):
            return False, "El usuario ya existe"
        
        # Guardar en USUARIOS_JSON
        nuevo_usuario = {
            "nombre": nombre,
            "correo": correo,
            "password": password,
            "tipo": tipo
        }
        usuarios.append(nuevo_usuario)
        guardar_datos(USUARIOS_JSON, usuarios)
        
        # Si es Refugio, guardar también en ALBERGUE_JSON
        if tipo == "Albergue":
            albergues = cargar_datos(ALBERGUE_JSON)
            
            # Generar ID único incremental
            nuevo_id = max([a["id"] for a in albergues], default=0) + 1
            
            nuevo_albergue = {
                "id": nuevo_id,
                "nombre": nombre,
                "correo": correo,
                "direccion": "",  # Campos adicionales
                "telefono": "",
                "capacidad_maxima": 20,
                "animales": []
            }
            albergues.append(nuevo_albergue)
            guardar_datos(ALBERGUE_JSON, albergues)

        elif tipo == "Ciudadano":

            ciudadanos = cargar_datos(CIUDADANOS_JSON)

            nuevo_ciudadano = {
                "nombre": nombre,
                "correo": correo,
                "adopciones": []
            }
            ciudadanos.append(nuevo_ciudadano)
            guardar_datos(CIUDADANOS_JSON, ciudadanos)

        elif tipo == "Rescatista":

            rescatistas = cargar_datos(RESCATISTAS_JSON)

            nuevo_rescatista = {
                "nombre": nombre,
                "correo": correo,
                "rescates": []
            }
            rescatistas.append(nuevo_rescatista)
            guardar_datos(RESCATISTAS_JSON, rescatistas)
        
        return True, "Registro exitoso"
    
    @staticmethod
    def iniciar_sesion(nombre: str, password: str) -> tuple[bool, str]:
        usuarios = cargar_datos(USUARIOS_JSON)
        for usuario in usuarios:
            if usuario["nombre"] == nombre and usuario["password"] == password:
                EstadoSesion.usuario = usuario  # <- Cambio aquí
                return True, "Inicio de sesión exitoso"
        return False, "Credenciales incorrectas"
    
    @staticmethod
    def cerrar_sesion() -> bool:
        EstadoSesion.usuario = None  # <- Cambio aquí
        return True


class Ciudadano(Usuario):

    def __init__(self, nombre, correo, password, tipo):
        super().__init__(nombre, correo, password, tipo)

class Rescatista(Usuario):
    def __init__(self, nombre, correo, password, tipo):
        super().__init__(nombre, correo, password, tipo)

    @staticmethod
    def obtener_reportes_pendientes():
        reportes = cargar_datos(ANIMALES_JSON)
        return [r for r in reportes if r["estado"] == "Pendiente"]

    @staticmethod
    def obtener_animales_rescatados(rescatista: str):
        animales = cargar_datos(ANIMALES_JSON)
        return [a for a in animales if 
                a.get("rescatista") == rescatista and 
                a["estado"] == "Rescatado" and 
                not a.get("refugio")]  # Solo animales no asignados

    @staticmethod
    def solicitar_ingreso_refugio(id_animal: int, id_refugio: int, rescatista: str):
        solicitudes = cargar_datos(SOLICITUDES_REFUGIO_JSON)
        
        nuevo_id = len(solicitudes) + 1
        nueva_solicitud = {
            "id": nuevo_id,
            "id_animal": id_animal,
            "id_refugio": id_refugio,
            "rescatista": rescatista,
            "estado": "Pendiente",
            "fecha_solicitud": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "fecha_respuesta": None
        }
        
        solicitudes.append(nueva_solicitud)
        guardar_datos(SOLICITUDES_REFUGIO_JSON, solicitudes)
        return True

class Refugio(Usuario):
    def __init__(self, nombre, correo, password, tipo):
        super().__init__(nombre, correo, password, tipo)

    @staticmethod
    def obtener_solicitudes_pendientes(id_refugio: int):
        solicitudes = cargar_datos(SOLICITUDES_REFUGIO_JSON)
        return [s for s in solicitudes if s["id_refugio"] == id_refugio and s["estado"] == "Pendiente"]

    @staticmethod
    def responder_solicitud(id_solicitud: int, decision: str, nombre_definitivo: str = None):
        solicitudes = cargar_datos(SOLICITUDES_REFUGIO_JSON)
        for solicitud in solicitudes:
            if solicitud["id"] == id_solicitud:
                if decision == "Aprobado":
                    # Verificar capacidad y actualizar datos
                    albergues = cargar_datos(ALBERGUE_JSON)
                    albergue = next((a for a in albergues if a["id"] == solicitud["id_refugio"]), None)
                    
                    if len(albergue["animales"]) >= albergue["capacidad_maxima"]:
                        return False, "Capacidad máxima alcanzada"
                    
                    if not nombre_definitivo:
                        return False, "Debe asignar un nombre definitivo"
                    
                    # Actualizar animal en ANIMALES_JSON
                    animales = cargar_datos(ANIMALES_JSON)
                    animal = next((a for a in animales if a["id"] == solicitud["id_animal"]), None)
                    if animal:
                        animal.update({
                            "nombre_definitivo": nombre_definitivo,
                            "refugio": solicitud["id_refugio"],
                            "estado": "En refugio"
                        })
                    
                    # Agregar al albergue
                    albergue["animales"].append({
                        "id_animal": solicitud["id_animal"],
                        "nombre": nombre_definitivo,
                        "categoria": animal["categoria"],
                        "fecha_ingreso": datetime.now().strftime("%d/%m/%Y %H:%M")
                    })
                    
                    guardar_datos(ANIMALES_JSON, animales)
                    guardar_datos(ALBERGUE_JSON, albergues)

                # Actualizar estado de la solicitud
                solicitud["estado"] = decision
                solicitud["fecha_respuesta"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                guardar_datos(SOLICITUDES_REFUGIO_JSON, solicitudes)
                return True, "Operación exitosa"
        return False, "Solicitud no encontrada"
    
    @staticmethod
    def actualizar_datos(id_refugio: int, nueva_direccion: dict, nuevo_telefono: str, nueva_capacidad: int):
        albergues = cargar_datos(ALBERGUE_JSON)
        for albergue in albergues:
            if albergue["id"] == id_refugio:
                albergue.update({
                    "direccion": nueva_direccion,
                    "telefono": nuevo_telefono,
                    "capacidad_maxima": nueva_capacidad
                })
                guardar_datos(ALBERGUE_JSON, albergues)
                return True
        return False

    @staticmethod
    def obtener_info(id_refugio: int):
        albergues = cargar_datos(ALBERGUE_JSON)
        return next((a for a in albergues if a["id"] == id_refugio), None)

class Reporte_Animal:
    UPLOAD_DIR = "uploads"
    RESCATE_DIR = "rescates"
    
    @classmethod
    def Crear_Reporte(cls, imagen_path: str, descripcion: str, ubicacion: dict, usuario: str, categoria: str):
        # Validar categoría
        categorias_validas = ["Perro", "Gato", "Otro"]
        if categoria not in categorias_validas:
            categoria = "Otro"  # Valor por defecto si no es válido
        
        # Generar nombre único para la imagen
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        ext = os.path.splitext(imagen_path)[1]
        filename = f"{usuario}_{timestamp}{ext}"
        dest_path = os.path.join(cls.UPLOAD_DIR, filename)
        
        # Copiar imagen al directorio de uploads
        shutil.copyfile(imagen_path, dest_path)
        
        # Crear registro del reporte
        reportes = cargar_datos(ANIMALES_JSON)
        nuevo_reporte = {
            "id": len(reportes) + 1,
            "usuario": usuario,
            "imagen": dest_path,
            "ubicacion": ubicacion,
            "descripcion": descripcion,
            "categoria": categoria,  # <- Nuevo campo
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "estado": "Pendiente",
            "prioridad": "Normal"  # Campo para futuras funcionalidades
        }
        reportes.append(nuevo_reporte)
        guardar_datos(ANIMALES_JSON, reportes)

    @classmethod
    def actualizar_estado(cls, reporte_id: int, rescatista: str, nombre_provisional: str, evidencia_path: str):
        reportes = cargar_datos(ANIMALES_JSON)
        for reporte in reportes:
            if reporte["id"] == reporte_id and reporte["estado"] == "Pendiente":
                # Mover imagen de evidencia
                if not os.path.exists(cls.RESCATE_DIR):
                    os.makedirs(cls.RESCATE_DIR)
                
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                ext = os.path.splitext(evidencia_path)[1]
                filename = f"{rescatista}_{timestamp}{ext}"
                dest_path = os.path.join(cls.RESCATE_DIR, filename)
                shutil.copyfile(evidencia_path, dest_path)
                
                # Actualizar datos
                reporte.update({
                    "estado": "Rescatado",
                    "rescatista": rescatista,
                    "nombre_provisional": nombre_provisional,
                    "evidencia": dest_path,
                    "fecha_rescate": datetime.now().strftime("%d/%m/%Y %H:%M")
                })
                guardar_datos(ANIMALES_JSON, reportes)

                rescatistas = cargar_datos(RESCATISTAS_JSON)
                for r in rescatistas:
                    if r["nombre"] == rescatista:
                        if "rescates" not in r:
                            r["rescates"] = []
                        r["rescates"].append({
                            "id_reporte": reporte_id,
                            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "nombre_animal": nombre_provisional
                        })
                        guardar_datos(RESCATISTAS_JSON, rescatistas)

                return True
        return False


class Adopcion:
    @staticmethod
    def publicar_adopcion(id_animal: int, id_refugio: int, descripcion: str, imagen_path: str):  # <- Añadir parámetro
        adopciones = cargar_datos(ADOPCIONES_JSON)
        
        nuevo_id = len(adopciones) + 1
        nueva_publicacion = {
            "id": nuevo_id,
            "id_animal": id_animal,
            "id_refugio": id_refugio,
            "descripcion": descripcion,
            "fecha_publicacion": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "estado": "Disponible",
            "solicitudes": [],
            "imagen_adopcion": imagen_path  # <- Guardar nueva imagen
        }
        adopciones.append(nueva_publicacion)
        guardar_datos(ADOPCIONES_JSON, adopciones)
        
        # Actualizar la imagen del animal en ANIMALES_JSON
        animales = cargar_datos(ANIMALES_JSON)
        for animal in animales:
            if animal["id"] == id_animal:
                animal["imagen"] = imagen_path  # <- Actualizar campo
                break
        guardar_datos(ANIMALES_JSON, animales)
        
        return True

    @staticmethod
    def solicitar_adopcion(id_adopcion: int, id_ciudadano: str, mensaje: str):
        solicitudes = cargar_datos(SOLICITUDES_ADOPCION_JSON)
        nueva_solicitud = {
            "id": len(solicitudes) + 1,
            "id_adopcion": id_adopcion,
            "ciudadano": id_ciudadano,
            "mensaje": mensaje,
            "estado": "Pendiente",
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        solicitudes.append(nueva_solicitud)
        guardar_datos(SOLICITUDES_ADOPCION_JSON, solicitudes)
        
        # Actualizar la publicación con la solicitud
        adopciones = cargar_datos(ADOPCIONES_JSON)
        for adopcion in adopciones:
            if adopcion["id"] == id_adopcion:
                adopcion["solicitudes"].append(nueva_solicitud["id"])
                guardar_datos(ADOPCIONES_JSON, adopciones)
                return True
        return False
    
    @staticmethod
    def responder_solicitud(id_solicitud: int, decision: str):
        solicitudes = cargar_datos(SOLICITUDES_ADOPCION_JSON)
        for solicitud in solicitudes:
            if solicitud["id"] == id_solicitud:
                solicitud["estado"] = decision
                guardar_datos(SOLICITUDES_ADOPCION_JSON, solicitudes)
                
                if decision == "Aprobado":
                    adopciones = cargar_datos(ADOPCIONES_JSON)
                    # Obtener el id_adopcion de la solicitud aprobada
                    id_adopcion_actual = solicitud["id_adopcion"]
                    
                    # Rechazar todas las demás solicitudes de la misma adopción
                    for s in solicitudes:
                        if s["id_adopcion"] == id_adopcion_actual and s["id"] != id_solicitud:
                            s["estado"] = "Rechazado"
                    guardar_datos(SOLICITUDES_ADOPCION_JSON, solicitudes)  # Guardar cambios aquí
                    
                    # Actualizar estado en ADOPCIONES_JSON y ANIMALES_JSON
                    for adopcion in adopciones:
                        if adopcion["id"] == id_adopcion_actual:
                            adopcion["estado"] = "Adoptado"
                            guardar_datos(ADOPCIONES_JSON, adopciones)
                            break  # Romper el bucle una vez encontrado
                    
                    animales = cargar_datos(ANIMALES_JSON)
                    for animal in animales:
                        if animal["id"] == adopcion["id_animal"]:
                            animal["estado"] = "Adoptado"
                    guardar_datos(ANIMALES_JSON, animales)
                    
                    # Registrar en CIUDADANOS_JSON
                    ciudadanos = cargar_datos(CIUDADANOS_JSON)
                    for ciudadano in ciudadanos:
                        if ciudadano["nombre"] == solicitud["ciudadano"]:
                            nueva_adopcion = {
                                "id_animal": adopcion["id_animal"],
                                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "refugio": adopcion["id_refugio"]
                            }
                            if "adopciones" not in ciudadano:
                                ciudadano["adopciones"] = []
                            ciudadano["adopciones"].append(nueva_adopcion)
                            guardar_datos(CIUDADANOS_JSON, ciudadanos)
                            break
                    return True
        return False

class Foro:
    @staticmethod
    def cargar_posts():
        return cargar_datos(FORO_JSON)

    @staticmethod
    def publicar_post(autor: str, contenido: str):
        posts = Foro.cargar_posts()
        nuevo_post = {
            "id": len(posts) + 1,
            "autor": autor,
            "contenido": contenido,
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "respuestas": []
        }
        posts.append(nuevo_post)
        guardar_datos(FORO_JSON, posts)
        return True

    @staticmethod
    def responder_post(post_id: int, autor: str, respuesta: str):
        posts = Foro.cargar_posts()
        for post in posts:
            if post["id"] == post_id:
                post["respuestas"].append({
                    "autor": autor,
                    "contenido": respuesta,
                    "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
                })
                guardar_datos(FORO_JSON, posts)
                return True
        return False
    
    @staticmethod
    def eliminar_post(post_id: int, usuario: str) -> bool:
        posts = Foro.cargar_posts()
        for i, post in enumerate(posts):
            if post["id"] == post_id and post["autor"] == usuario:
                del posts[i]
                guardar_datos(FORO_JSON, posts)
                return True
        return False

    @staticmethod
    def editar_post(post_id: int, usuario: str, nuevo_contenido: str) -> bool:
        posts = Foro.cargar_posts()
        for post in posts:
            if post["id"] == post_id and post["autor"] == usuario:
                post["contenido"] = nuevo_contenido
                guardar_datos(FORO_JSON, posts)
                return True
        return False

        