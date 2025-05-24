import tkinter as tk
from tkinter import ttk, messagebox
from backend_pets import EstadoSesion, cargar_datos, Usuario
from backend_pets import *
import customtkinter as ctk
from tkcalendar import DateEntry
from PIL import Image, ImageTk
import shutil
import os
from tkinter import filedialog
from tkintermapview import TkinterMapView
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

class MapaDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Seleccionar ubicación")
        self.geometry("900x700")
        self.callback = callback
        
        self.marker = None
        self.ubicacion = {
            "coordenadas": None,
            "direccion": None
        }
        
        # Configurar geocodificador
        self.geocoder = Nominatim(user_agent="AnimalRescue/1.0", timeout=10)
        self.geocode = RateLimiter(self.geocoder.geocode, min_delay_seconds=1)
        self.reverse_geocode = RateLimiter(self.geocoder.reverse, min_delay_seconds=1)
        
        self.crear_interfaz()
        
        self.map_widget.add_right_click_menu_command(
            "Agregar marcador", 
            self.colocar_marcador, 
            pass_coords=True
        )
        
    def crear_interfaz(self):
        frame_superior = ctk.CTkFrame(self)
        frame_superior.pack(pady=10, fill="x")
        
        self.entry = ctk.CTkEntry(frame_superior, width=400)
        self.entry.pack(side="left", padx=5)
        
        ctk.CTkButton(frame_superior, text="Buscar", command=self.buscar_ubicacion).pack(side="left", padx=5)
        ctk.CTkButton(frame_superior, text="Confirmar", command=self.confirmar_ubicacion, 
                     fg_color="#4CAF50", hover_color="#45a049").pack(side="left", padx=5)
        
        self.map_widget = TkinterMapView(self, width=900, height=600)
        self.map_widget.pack(fill="both", expand=True)
        self.map_widget.set_zoom(15)
        self.map_widget.set_position(19.0414, -98.2063)  # Centrar en Puebla
        
        self.lbl_info = ctk.CTkLabel(self, text="Ubicación seleccionada: Ninguna")
        self.lbl_info.pack(pady=5)
        
    def colocar_marcador(self, coords):
        if self.marker:
            self.marker.delete()
        self.marker = self.map_widget.set_marker(coords[0], coords[1])
        self.ubicacion["coordenadas"] = (coords[0], coords[1])
        self.obtener_direccion(coords[0], coords[1])
        
    def obtener_direccion(self, lat, lon):
        try:
            time.sleep(1)
            location = self.reverse_geocode((lat, lon), language="es")
            if location:
                self.ubicacion["direccion"] = location.address
                self.lbl_info.configure(text=f"Ubicación: {location.address[:80]}...")
            else:
                self.lbl_info.configure(text="Dirección no disponible", text_color="red")
        except Exception as e:
            print(f"Error geocodificación: {str(e)}")
            self.lbl_info.configure(text="Error obteniendo dirección", text_color="red")
            
    def buscar_ubicacion(self):
        entrada = self.entry.get().strip()
        if "," in entrada:
            try:
                lat, lon = map(float, entrada.split(",", 1))
                self.colocar_marcador((lat, lon))
                return
            except ValueError:
                pass
        
        try:
            time.sleep(1)
            location = self.geocode(f"{entrada}, Puebla, México", exactly_one=True)
            if location:
                self.colocar_marcador((location.latitude, location.longitude))
        except Exception as e:
            self.lbl_info.configure(text="Error en la búsqueda", text_color="red")
            
    def confirmar_ubicacion(self):
        if self.ubicacion["coordenadas"]:
            self.callback(self.ubicacion)
            self.destroy()

usuarios = cargar_datos("usuarios.json")
albergues = cargar_datos("albergues.json")
rescatistas = cargar_datos("rescatistas.json")
animales = cargar_datos("animales.json")

ventana_principal = None

def actualizar_pantalla_principal():
    global ventana_principal
    if ventana_principal:
        ventana_principal.destroy()
        # Destruir imagen explícitamente
        global imagen_titulo
        imagen_titulo = None
    pantalla_inicial()

def pantalla_inicial():
    global root, ventana_principal, imagen_titulo

    if not ctk.get_appearance_mode():
        ctk.set_appearance_mode("light")
    ventana_principal = root = ctk.CTk()  
    root.title("Menu Principal")
    root.geometry("1200x600")

    root.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
    root.grid_rowconfigure((0, 1, 2, 4, 5, 6), weight=1)
    root.grid_rowconfigure(3, weight=1)


    imagen_titulo = ctk.CTkImage(
        light_image=Image.open(os.path.join(os.path.dirname(__file__), "imagen1.jpg")), 
        size=(800, 150)
    )

    frame_titulo = ctk.CTkFrame(
        master=root, 
        fg_color="#A6F8F1",
        corner_radius=8
    )
    frame_titulo.grid(
        column=1, row=0,
        columnspan=4, rowspan=1,
        padx=10, pady=10,
        sticky="nsew"
    )


    frame_titulo.grid_columnconfigure(0, weight=1)
    frame_titulo.grid_rowconfigure(0, weight=0)  # Fila para texto y botón
    frame_titulo.grid_rowconfigure(1, weight=1)  # Fila para imagen

    # Parte superior: texto y botón
    frame_superior = ctk.CTkFrame(frame_titulo, fg_color="transparent")
    frame_superior.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    if EstadoSesion.usuario:
        ctk.CTkLabel(
            frame_superior, 
            text="Dejando Huella", 
            font=("Arial", 25)
        ).pack(side=tk.LEFT, expand=True)
    else:
        ctk.CTkLabel(
            frame_superior, 
            text="Bienvenido Dejando Huella", 
            font=("Arial", 25)
        ).pack(side=tk.LEFT, expand=True)

    frame_sesion = ctk.CTkFrame(frame_superior, fg_color="transparent")
    frame_sesion.pack(side=tk.RIGHT, padx=10)

    # Botón dinámico
    if EstadoSesion.usuario:
        ctk.CTkButton(
            frame_sesion, 
            text=f"Cerrar sesión ({EstadoSesion.usuario['nombre']})", 
            command=lambda: [Usuario.cerrar_sesion(), actualizar_pantalla_principal()],
            hover_color="#FF5555"
        ).pack(padx=5, pady=5)
    else:
        ctk.CTkButton(
            frame_sesion, 
            text="Ingresar", 
            command=pantalla_ingresar, 
            hover_color="#12E82E"
        ).pack(padx=5, pady=5)

    # Parte inferior: imagen
    label_imagen = ctk.CTkLabel(
        master=frame_titulo,
        text="",
        image=imagen_titulo
    )
    label_imagen.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    frame_menu_horizontal = ctk.CTkFrame(
        master=root, 
        fg_color="#A6F8F1",
        corner_radius=8
    )
    frame_menu_horizontal.grid(
        column=1, row=2,
        columnspan=4, rowspan=1,
        padx=10, pady=10,
        sticky="nsew"
    )

    frame_contenido = ctk.CTkFrame(
        master=root,
        fg_color="#FFFFFF",
        corner_radius=8
    )
    frame_contenido.grid(
        column=1, row=3,
        columnspan=4, rowspan=2,
        padx=10, pady=(0,10),
        sticky="nsew"
    )

    # Función para limpiar el frame de contenido
    def limpiar_contenido():
        for widget in frame_contenido.winfo_children():
            widget.destroy()

    # Contenido para Educación
    def mostrar_educacion():
        limpiar_contenido()
        
        # Título
        ctk.CTkLabel(
            frame_contenido,
            text="Recursos Educativos",
            font=("Arial", 18, "bold"),
            text_color="#333333"
        ).pack(pady=(10,5))
        
        # Contenido
        recursos = [
            "1. Guía de tenencia responsable",
            "2. Cuidados básicos para mascotas",
            "3. Señales de maltrato animal",
            "4. Proceso de adopción paso a paso"
        ]
        
        for recurso in recursos:
            ctk.CTkLabel(
                frame_contenido,
                text=recurso,
                font=("Arial", 14),
                text_color="#555555"
            ).pack(anchor="w", padx=20, pady=2)
        
        # Botón de descarga (ejemplo)
        ctk.CTkButton(
            frame_contenido,
            text="Descargar Guía Completa",
            command=lambda: messagebox.showinfo("Descarga", "Guía descargada exitosamente"),
            fg_color="#4CAF50",
            hover_color="#45a049",
            width=200
        ).pack(pady=15)

    # Contenido para Foro
    def mostrar_foro():
        limpiar_contenido()
        
        # Título
        ctk.CTkLabel(
            frame_contenido,
            text="Foro Comunitario",
            font=("Arial", 18, "bold"),
            text_color="#333333"
        ).pack(pady=(10,5))

        # Cargar posts reales
        posts = Foro.cargar_posts()
        
        # Sección de publicaciones
        frame_publicaciones = ctk.CTkScrollableFrame(
            frame_contenido,
            height=200,
            fg_color="#FFFFFF"
        )
        frame_publicaciones.pack(fill="x", padx=10, pady=5, expand=True)

        for post in posts:
            frame_post = ctk.CTkFrame(
                frame_publicaciones,
                fg_color="#F8F8F8",
                corner_radius=6
            )
            frame_post.pack(fill="x", pady=5, padx=5)

            ctk.CTkLabel(
                frame_post,
                text=post["contenido"],  # <- Texto del post
                font=("Arial", 12),
                text_color="#333333",    # Color oscuro
                wraplength=500           # Ajustar ancho
            ).pack(padx=10, pady=(0, 10), anchor="w")

            def abrir_comentarios(post_id=post['id']):
                ventana_comentarios = ctk.CTkToplevel()
                ventana_comentarios.geometry("500x400+%d+%d" % (root.winfo_x()+150, root.winfo_y()+50))
                ventana_comentarios.transient(root)
                ventana_comentarios.lift()
                ventana_comentarios.grab_set()
                ventana_comentarios.focus_force()
                
                # Área de comentarios
                scroll = ctk.CTkScrollableFrame(ventana_comentarios)
                scroll.pack(fill="both", expand=True)
                
                # Cargar respuestas actualizadas
                posts_actualizados = Foro.cargar_posts()
                post_actual = next((p for p in posts_actualizados if p["id"] == post_id), None)
                
                if post_actual:
                    for respuesta in post_actual['respuestas']:
                        ctk.CTkLabel(
                            scroll,
                            text=f"{respuesta['autor']}: {respuesta['contenido']}",
                            font=("Arial", 11)
                        ).pack(anchor="w", pady=2)
                
                if EstadoSesion.usuario:
                    frame_nuevo_comentario = ctk.CTkFrame(ventana_comentarios)
                    frame_nuevo_comentario.pack(fill="x", pady=10)
                    
                    entrada = ctk.CTkEntry(frame_nuevo_comentario)
                    entrada.pack(side="left", fill="x", expand=True, padx=5)
                    
                    def publicar_comentario():
                        if entrada.get():
                            Foro.responder_post(post_id, EstadoSesion.usuario['nombre'], entrada.get())
                            ventana_comentarios.destroy()
                            mostrar_foro()  # <- Recargar toda la sección del foro
                            root.update()   # <- Actualizar la interfaz gráfica
                    
                    ctk.CTkButton(
                        frame_nuevo_comentario,
                        text="Comentar",
                        command=publicar_comentario
                    ).pack(side="right", padx=5)

            # Botón de comentarios
            ctk.CTkButton(
                frame_post,
                text=f"💬 {len(post['respuestas'])} comentarios",
                command=abrir_comentarios,
                fg_color="transparent",
                hover_color="#0EF2E3"
            ).pack(pady=5)

            # Cabecera con opciones de edición
            frame_cabecera = ctk.CTkFrame(frame_post, fg_color="transparent")
            frame_cabecera.pack(fill="x", padx=10, pady=(5,0))
            
            ctk.CTkLabel(
                frame_cabecera,
                text=f"{post['autor']} - {post['fecha']}",
                font=("Arial", 12, "bold"),
                text_color="#000000"
            ).pack(side="left")

            # Botones de edición si es el autor
            if EstadoSesion.usuario and EstadoSesion.usuario['nombre'] == post['autor']:
                frame_botones = ctk.CTkFrame(frame_cabecera, fg_color="transparent")
                frame_botones.pack(side="right")
                
                def editar_post(post_id=post['id'], contenido_original=post['contenido']):
                    ventana_edicion = ctk.CTkToplevel()
                    ventana_edicion.geometry("400x200+%d+%d" % (root.winfo_x()+200, root.winfo_y()+100))
                    ventana_edicion.transient(root)
                    ventana_edicion.grab_set()
                    
                    ctk.CTkLabel(ventana_edicion, text="Editar publicación:").pack(pady=5)
                    entrada = ctk.CTkEntry(ventana_edicion, width=300)
                    entrada.insert(0, contenido_original)
                    entrada.pack(pady=10)
                    
                    def guardar_cambios():
                        if Foro.editar_post(post_id, EstadoSesion.usuario['nombre'], entrada.get()):
                            mostrar_foro()
                            ventana_edicion.destroy()
                    ctk.CTkButton(ventana_edicion, text="Guardar", command=guardar_cambios).pack()
                
                ctk.CTkButton(
                    frame_botones,
                    text="✏️",
                    width=30,
                    command=editar_post
                ).pack(side="left", padx=2)
                
                def eliminar_post(post_id=post['id']):
                    if messagebox.askyesno("Confirmar", "¿Eliminar esta publicación?"):
                        if Foro.eliminar_post(post_id, EstadoSesion.usuario['nombre']):
                            mostrar_foro()
                ctk.CTkButton(
                    frame_botones,
                    text="🗑️",
                    width=30,
                    command=eliminar_post
                ).pack(side="left", padx=2)

        # Campo para nueva publicación solo si está logueado
        if EstadoSesion.usuario:
            frame_nuevo_post = ctk.CTkFrame(
                frame_contenido,
                fg_color="#F0F0F0",
                corner_radius=8
            )
            frame_nuevo_post.pack(pady=10, padx=10, fill="x")

            entrada_post = ctk.CTkEntry(
                frame_nuevo_post,
                placeholder_text="Escribe tu pregunta o comentario...",
                width=400
            )
            entrada_post.pack(side="left", padx=10, pady=10)

            def publicar():
                if not entrada_post.get():
                    messagebox.showerror("Error", "El mensaje no puede estar vacío")
                    return
                Foro.publicar_post(
                    EstadoSesion.usuario['nombre'],
                    entrada_post.get()
                )
                entrada_post.delete(0, tk.END)
                mostrar_foro()  # Actualizar vista

            ctk.CTkButton(
                frame_nuevo_post,
                text="Publicar",
                command=publicar,
                width=100,
                fg_color="#4CAF50",
                hover_color="#45a049"
            ).pack(side="right", padx=10, pady=10)
        else:
            ctk.CTkLabel(
                frame_contenido,
                text="Debes iniciar sesión para participar",
                text_color="#FF0000",
                font=("Arial", 12)
            ).pack(pady=10)

        def abrir_comentarios(post_id=post['id']):
            ventana_comentarios = ctk.CTkToplevel()
            ventana_comentarios.geometry("500x400+%d+%d" % (root.winfo_x()+150, root.winfo_y()+50))
            # Refuerza el orden y el enfoque
            ventana_comentarios.transient(root)
            ventana_comentarios.lift()
            ventana_comentarios.grab_set()
            ventana_comentarios.focus_force()
            
            frame_contenido = ctk.CTkFrame(ventana_comentarios)
            frame_contenido.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Área de comentarios
            scroll = ctk.CTkScrollableFrame(frame_contenido)
            scroll.pack(fill="both", expand=True)
            
            for respuesta in post['respuestas']:
                ctk.CTkLabel(
                    scroll,
                    text=f"{respuesta['autor']}: {respuesta['contenido']}",
                    font=("Arial", 11)
                ).pack(anchor="w", pady=2)
            
            if EstadoSesion.usuario:
                frame_nuevo_comentario = ctk.CTkFrame(frame_contenido)
                frame_nuevo_comentario.pack(fill="x", pady=10)
                
                entrada = ctk.CTkEntry(frame_nuevo_comentario, placeholder_text="Escribe tu comentario...")
                entrada.pack(side="left", fill="x", expand=True, padx=5)
                
                def publicar_comentario():
                    if entrada.get():
                        Foro.responder_post(post_id, EstadoSesion.usuario['nombre'], entrada.get())
                        ventana_comentarios.destroy()
                        mostrar_foro()
                ctk.CTkButton(
                    frame_nuevo_comentario,
                    text="Comentar",
                    width=100,
                    command=publicar_comentario
                ).pack(side="right", padx=5)
        
            ctk.CTkButton(
                frame_post,
                text=f"💬 {len(post['respuestas'])} comentarios",
                command=abrir_comentarios,
                fg_color="transparent",
                hover_color="#E0E0E0",
                width=120
            ).pack(pady=5)

    # Botones comunes
    ctk.CTkButton(
        frame_menu_horizontal,
        text="Educación",
        command=mostrar_educacion,
        hover_color="#12E82E",
        width=120
    ).grid(row=0, column=0, padx=10, pady=5)

    ctk.CTkButton(
        frame_menu_horizontal,
        text="Foro",
        command=mostrar_foro,
        hover_color="#12E82E",
        width=120
    ).grid(row=0, column=1, padx=10, pady=5)

    # Botones por rol
    if EstadoSesion.usuario:
        tipo_usuario = EstadoSesion.usuario['tipo']
        columna = 2  # Comenzar desde la tercera columna

        if tipo_usuario == "Ciudadano":
            def reportar_rescate():
                ventana_reporte = ctk.CTkToplevel()
                ventana_reporte.title("Reportar Animal")
                ventana_reporte.geometry("600x750")  # Aumentamos altura para nuevo campo

                # --- Configuración para aparecer delante y bloquear interacción ---
                ventana_reporte.transient(root)  # Indica relación padre-hijo
                ventana_reporte.lift()  # Trae la ventana al frente
                ventana_reporte.grab_set()  # Bloquea el foco
                ventana_reporte.focus_force()  # Fuerza el enfoque
                
                # --- Variables ---
                imagen_path = tk.StringVar()
                categoria = tk.StringVar(value="Perro")  # Valor por defecto
                ubicacion_seleccionada = tk.StringVar(value="")
                coordenadas = None

                # --- Contenedores ---
                frame_principal = ctk.CTkFrame(ventana_reporte)
                frame_principal.pack(padx=20, pady=20, fill="both", expand=True)

                def callback_ubicacion(ubicacion):
                    nonlocal coordenadas
                    coordenadas = ubicacion["coordenadas"]
                    ubicacion_seleccionada.set(ubicacion["direccion"] or "Coordenadas: " + ", ".join(map(str, coordenadas)))
                
                # Nuevo frame para ubicación
                frame_ubicacion = ctk.CTkFrame(frame_principal)
                frame_ubicacion.pack(fill="x", pady=5)
                
                ctk.CTkLabel(frame_ubicacion, text="Ubicación:").pack(side="left")
                entrada_ubicacion = ctk.CTkEntry(frame_ubicacion, textvariable=ubicacion_seleccionada, state="readonly")
                entrada_ubicacion.pack(side="left", padx=5, fill="x", expand=True)
                
                def abrir_mapa():
                    mapa_dialog = MapaDialog(root, callback_ubicacion)
                    mapa_dialog.transient(root)
                    mapa_dialog.lift()
                    mapa_dialog.grab_set()
                    mapa_dialog.focus_force()

                ctk.CTkButton(
                    frame_ubicacion,
                    text="📍 Seleccionar en mapa",
                    command= abrir_mapa,
                    fg_color="#2196F3",
                    hover_color="#1976D2"
                ).pack(side="left", padx=5)

                # --- Sección Categoría (NUEVO) ---
                frame_categoria = ctk.CTkFrame(frame_principal, fg_color="transparent")
                frame_categoria.pack(fill="x", pady=(0, 10))
                
                ctk.CTkLabel(
                    frame_categoria, 
                    text="Tipo de animal:",
                    font=("Arial", 14)
                ).pack(side="left", padx=(0, 10))
                
                # Selector visual con iconos
                opciones = [
                    ("Perro", "🐶"),
                    ("Gato", "🐱"),
                    ("Otro", "❓")
                ]
                
                for texto, emoji in opciones:
                    ctk.CTkRadioButton(
                        frame_categoria,
                        text=f"{emoji} {texto}",
                        variable=categoria,
                        value=texto,
                        radiobutton_height=20,
                        radiobutton_width=20,
                        corner_radius=10
                    ).pack(side="left", padx=5)

                # Sección de carga de imagen
                frame_imagen = ctk.CTkFrame(frame_principal, height=250)
                frame_imagen.pack(fill="x", pady=10)

                lbl_preview = ctk.CTkLabel(frame_imagen, text="Sin imagen seleccionada", width=300, height=200)
                lbl_preview.pack(pady=10)

                def seleccionar_imagen():
                    nonlocal lbl_preview
                    filetypes = (("Imágenes", "*.jpg *.jpeg *.png"),)
                    path = filedialog.askopenfilename(filetypes=filetypes)
                    if path:
                        imagen_path.set(path)
                        # Mostrar vista previa
                        image = Image.open(path)
                        image.thumbnail((300, 200))
                        ctk_image = ctk.CTkImage(light_image=image, size=image.size)
                        lbl_preview.configure(image=ctk_image, text="")

                ctk.CTkButton(
                    frame_imagen,
                    text="📸 Subir foto del animal",
                    command=seleccionar_imagen,
                    fg_color="#4CAF50",
                    hover_color="#45a049"
                ).pack(pady=5)

                # Formulario
                ctk.CTkLabel(frame_principal, text="Descripción:", font=("Arial", 14)).pack(anchor="w", pady=(10,0))
                entrada_desc = ctk.CTkTextbox(frame_principal, height=100, wrap="word")
                entrada_desc.pack(fill="x", pady=5)

                def guardar_reporte():
                    if not imagen_path.get():
                        messagebox.showerror("Error", "¡Debes subir una foto del animal!")
                        return
                        
                    try:
                        Reporte_Animal.Crear_Reporte(
                            imagen_path=imagen_path.get(),
                            descripcion=entrada_desc.get("1.0", "end-1c"),
                            ubicacion={
                                "coordenadas": coordenadas,
                                "direccion": ubicacion_seleccionada.get()
                            },
                            usuario=EstadoSesion.usuario['nombre'],
                            categoria=categoria.get()  # <- Nuevo parámetro
                        )
                        messagebox.showinfo("Éxito", "Reporte guardado. ¡Gracias por ayudar! 🐾")
                        ventana_reporte.destroy()
                    except Exception as e:
                        messagebox.showerror("Error", f"Oops! Error al guardar: {str(e)}")

                ctk.CTkButton(
                    frame_principal,
                    text="🚨 Reportar Animal",
                    command=guardar_reporte,
                    fg_color="#FF5722",
                    hover_color="#E64A19",
                    height=40
                ).pack(pady=20)

            ctk.CTkButton(
                frame_menu_horizontal,
                text="Reportar Rescate",
                command=reportar_rescate,
                hover_color="#FFA500",
                width=150
            ).grid(row=0, column=columna, padx=10, pady=5)
            columna += 1

            def Adoptar():
                ventana_adopcion = ctk.CTkToplevel()
                ventana_adopcion.title("Adoptar un Animal")
                ventana_adopcion.geometry("800x600")
                
                # Cargar adopciones disponibles
                adopciones = cargar_datos(ADOPCIONES_JSON)
                disponibles = [a for a in adopciones if a["estado"] == "Disponible"]
                
                frame = ctk.CTkScrollableFrame(ventana_adopcion)
                frame.pack(fill="both", expand=True, padx=20, pady=20)
                
                for adopcion in disponibles:
                    # Obtener datos del animal
                    animal = next((a for a in cargar_datos(ANIMALES_JSON) if a["id"] == adopcion["id_animal"]), None)
                    refugio = next((r for r in cargar_datos(ALBERGUE_JSON) if r["id"] == adopcion["id_refugio"]), None)
                    
                    frame_adop = ctk.CTkFrame(frame, fg_color="#F0F0F0")
                    frame_adop.pack(fill="x", pady=5)
                    
                    # Imagen
                    try:
                        image = Image.open(animal["imagen"]) if animal else Image.new('RGB', (100,100), color='gray')
                        image.thumbnail((150, 150))
                        ctk_image = ctk.CTkImage(light_image=image, size=image.size)
                        ctk.CTkLabel(frame_adop, image=ctk_image, text="").pack(side="left", padx=10)
                    except:
                        ctk.CTkLabel(frame_adop, text="🖼️ Imagen no disponible").pack(side="left", padx=10)
                    
                    # Info
                    frame_info = ctk.CTkFrame(frame_adop, fg_color="transparent")
                    frame_info.pack(side="left", fill="x", expand=True)
                    
                    texto = (
                        f"🐾 Nombre: {animal['nombre_provisional'] if animal else 'N/A'}\n"
                        f"🏠 Refugio: {refugio['nombre'] if refugio else 'N/A'}\n"
                        f"📅 Publicado: {adopcion['fecha_publicacion']}\n"
                        f"📝 Descripción: {adopcion['descripcion']}"
                    )
                    ctk.CTkLabel(frame_info, text=texto, justify="left").pack(anchor="w")
                    
                    # Botón Solicitar
                    def solicitar(id_adopcion=adopcion["id"]):
                        ventana_solicitud = ctk.CTkToplevel()
                        ventana_solicitud.geometry("500x300")
                        ventana_solicitud.transient(root)
                        ventana_solicitud.lift()
                        ventana_solicitud.grab_set()
                        ventana_solicitud.focus_force()
                        
                        ctk.CTkLabel(ventana_solicitud, text="¿Por qué quieres adoptar a este animal?").pack(pady=10)
                        entrada_motivo = ctk.CTkTextbox(ventana_solicitud, height=150)
                        entrada_motivo.pack(fill="x", padx=20, pady=10)
                        
                        def enviar_solicitud():
                            if not entrada_motivo.get("1.0", "end-1c"):
                                messagebox.showerror("Error", "Escribe tus motivos")
                                return
                            
                            Adopcion.solicitar_adopcion(
                                id_adopcion=id_adopcion,
                                id_ciudadano=EstadoSesion.usuario["nombre"],
                                mensaje=entrada_motivo.get("1.0", "end-1c")
                            )
                            messagebox.showinfo("Éxito", "Solicitud enviada al refugio")
                            ventana_solicitud.destroy()
                        
                        ctk.CTkButton(ventana_solicitud, text="Enviar", command=enviar_solicitud).pack()
                    
                    ctk.CTkButton(
                        frame_adop,
                        text="Solicitar Adopción",
                        command=solicitar,
                        fg_color="#2196F3",
                        width=120
                    ).pack(side="right", padx=10)

            ctk.CTkButton(
                frame_menu_horizontal,
                text="Adoptar",
                command=Adoptar,
                hover_color="#FFA500",
                width=150
            ).grid(row=0, column=columna, padx=10, pady=5)
            columna += 1
        
            def ver_mis_adopciones():
                limpiar_contenido()
                
                ctk.CTkLabel(
                    frame_contenido,
                    text="Mis Adopciones",
                    font=("Arial", 18, "bold")
                ).pack(pady=10)
                
                # Obtener datos del usuario actual
                ciudadanos = cargar_datos(CIUDADANOS_JSON)
                usuario_actual = next((u for u in ciudadanos if u["nombre"] == EstadoSesion.usuario["nombre"]), None)
                
                if not usuario_actual or "adopciones" not in usuario_actual or len(usuario_actual["adopciones"]) == 0:
                    ctk.CTkLabel(frame_contenido, text="Aún no has adoptado animales ❤️").pack()
                    return
                
                frame_adopciones = ctk.CTkScrollableFrame(frame_contenido)
                frame_adopciones.pack(fill="both", expand=True)
                
                for adopcion in usuario_actual["adopciones"]:
                    animal = next((a for a in cargar_datos(ANIMALES_JSON) if a["id"] == adopcion["id_animal"]), None)
                    refugio = next((r for r in cargar_datos(ALBERGUE_JSON) if r["id"] == adopcion["refugio"]), None)
                    
                    frame = ctk.CTkFrame(frame_adopciones, fg_color="#F8F8F8")
                    frame.pack(fill="x", pady=5)
                    
                    texto = (
                        f"🐾 Nombre: {animal['nombre_definitivo'] if animal else 'N/A'}\n"
                        f"🏠 Refugio: {refugio['nombre'] if refugio else 'N/A'}\n"
                        f"📅 Fecha de adopción: {adopcion['fecha']}"
                    )
                    ctk.CTkLabel(frame, text=texto).pack(side="left", padx=10)

            # Agregar botón "Mis Adopciones" al Ciudadano:
            ctk.CTkButton(
                frame_menu_horizontal,
                text="Mis Adopciones",
                command=ver_mis_adopciones,
                hover_color="#FFA500",
                width=150
            ).grid(row=0, column=columna, padx=10, pady=5)
            columna += 1

        elif tipo_usuario == "Rescatista":
            def ver_reportes():
                limpiar_contenido()
                
                # Título
                ctk.CTkLabel(
                    frame_contenido,
                    text="Reportes Pendientes",
                    font=("Arial", 18, "bold"),
                    text_color="#333333"
                ).pack(pady=(10,5))

                # Cargar reportes
                reportes = Rescatista.obtener_reportes_pendientes()
                
                if not reportes:
                    ctk.CTkLabel(
                        frame_contenido,
                        text="🎉 No hay reportes pendientes",
                        text_color="#4CAF50",
                        font=("Arial", 14)
                    ).pack()
                    return

                # Listado interactivo
                frame_reportes = ctk.CTkScrollableFrame(frame_contenido, height=400)
                frame_reportes.pack(fill="both", expand=True, padx=10, pady=10)

                for reporte in reportes:
                    frame_reporte = ctk.CTkFrame(
                        frame_reportes,
                        fg_color="#F8F8F8",
                        corner_radius=8
                    )
                    frame_reporte.pack(fill="x", pady=5, padx=5)
                    frame_reporte.grid_columnconfigure((0, 1), weight=1)
                    
                    # Sección de imagen (nueva)
                    frame_imagen = ctk.CTkFrame(frame_reporte, fg_color="transparent", width=200)
                    frame_imagen.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
                    
                    try:
                        # Cargar y mostrar imagen
                        image = Image.open(reporte['imagen'])
                        image.thumbnail((180, 180))  # Redimensionar manteniendo aspecto
                        ctk_image = ctk.CTkImage(light_image=image, size=image.size)
                        lbl_imagen = ctk.CTkLabel(frame_imagen, image=ctk_image, text="")
                        lbl_imagen.pack()
                    except Exception as e:
                        ctk.CTkLabel(
                            frame_imagen,
                            text="🖼️ Imagen no disponible",
                            text_color="#FF0000",
                            font=("Arial", 10)
                        ).pack()

                    # Sección de datos
                    frame_datos = ctk.CTkFrame(frame_reporte, fg_color="transparent")
                    frame_datos.grid(row=0, column=1, padx=10, pady=10, sticky="w")
                    
                    # Información del reporte
                    ctk.CTkLabel(
                        frame_datos,
                        text=f"📅 {reporte['fecha']} | 🏷️ {reporte['categoria']}",
                        font=("Arial", 12),
                        text_color="#555555"
                    ).pack(anchor="w", pady=5)

                    if reporte['ubicacion'].get('coordenadas'):
                        btn_mapa = ctk.CTkButton(
                            frame_datos,
                            text="Ver en mapa",
                            command=lambda coords=reporte['ubicacion']['coordenadas']: mostrar_mapa(coords),
                            width=80
                        )
                        btn_mapa.pack(pady=5)

                    # Función para mostrar el mapa
                    def mostrar_mapa(coords):
                        mapa_ventana = ctk.CTkToplevel()
                        mapa_ventana.title("Ubicación del reporte")
                        mapa_ventana.transient(root)
                        mapa_ventana.lift()
                        mapa_ventana.grab_set()
                        mapa_ventana.focus_force()
                        mapa_widget = TkinterMapView(mapa_ventana, width=600, height=400)
                        mapa_widget.pack(fill="both", expand=True)
                        mapa_widget.set_position(coords[0], coords[1])
                        mapa_widget.set_marker(coords[0], coords[1])

                    ctk.CTkLabel(
                        frame_datos,
                        text=reporte['descripcion'],
                        font=("Arial", 12),
                        text_color="#444444",
                        wraplength=400
                    ).pack(anchor="w", pady=(0,10))

                    # Botón de acción
                    def marcar_rescatado(reporte_id=reporte['id']):
                        ventana_rescate = ctk.CTkToplevel()
                        ventana_rescate.title("Confirmar Rescate")
                        ventana_rescate.geometry("500x600")
                        ventana_rescate.transient(root)
                        ventana_rescate.lift()
                        ventana_rescate.grab_set()
                        ventana_rescate.focus_force()
                        
                        # --- Variables ---
                        nombre_provisional = tk.StringVar()
                        evidencia_path = tk.StringVar()
                        
                        # --- Contenido ---
                        frame_form = ctk.CTkFrame(ventana_rescate)
                        frame_form.pack(padx=20, pady=20, fill="both", expand=True)

                        # --- Nombre provisional ---
                        ctk.CTkLabel(frame_form, text="Nombre provisional:").pack(pady=5)
                        entrada_nombre = ctk.CTkEntry(frame_form, textvariable=nombre_provisional)  # <- Añadir textvariable
                        entrada_nombre.pack(fill="x", pady=5)

                        # --- Subir evidencia ---
                        lbl_evidencia = ctk.CTkLabel(frame_form, text="Sin evidencia seleccionada", height=200)
                        lbl_evidencia.pack(pady=10)

                        def seleccionar_evidencia():
                            filetypes = (("Imágenes", "*.jpg *.jpeg *.png"),)
                            path = filedialog.askopenfilename(filetypes=filetypes)
                            if path:
                                evidencia_path.set(path)  # <- Actualizar la variable
                                image = Image.open(path)
                                image.thumbnail((300, 200))
                                ctk_image = ctk.CTkImage(light_image=image, size=image.size)
                                lbl_evidencia.configure(image=ctk_image, text="")

                        ctk.CTkButton(
                            frame_form,
                            text="📸 Subir evidencia del rescate",
                            command=seleccionar_evidencia,
                            fg_color="#4CAF50",
                            hover_color="#45a049"
                        ).pack(pady=5)

                        # --- Confirmación final ---
                        def confirmar_rescate():
                            # Validar usando las variables directamente
                            if not nombre_provisional.get() or not evidencia_path.get():
                                messagebox.showerror("Error", "Todos los campos son obligatorios")
                                return
                            
                            if messagebox.askyesno(
                                "Confirmar",
                                f"¿Marcar este animal como rescatado?\nNombre: {nombre_provisional.get()}"
                            ):
                                try:
                                    Reporte_Animal.actualizar_estado(
                                        reporte_id,
                                        EstadoSesion.usuario['nombre'],
                                        nombre_provisional.get(),
                                        evidencia_path.get()
                                    )
                                    messagebox.showinfo("Éxito", "¡Rescate registrado con éxito! 🐾")
                                    ventana_rescate.destroy()
                                    ver_reportes()  # Actualizar lista
                                except Exception as e:
                                    messagebox.showerror("Error", f"Error: {str(e)}")

                        ctk.CTkButton(
                            frame_form,
                            text="✅ Confirmar Rescate",
                            command=confirmar_rescate,
                            fg_color="#2196F3",
                            hover_color="#1976D2",
                            height=40
                        ).pack(pady=20)
                        
                    ctk.CTkButton(
                        frame_datos,
                        text="Marcar como Rescatado",
                        command=marcar_rescatado,
                        fg_color="#4CAF50",
                        hover_color="#45a049",
                        width=150
                    ).pack(pady=10)

            ctk.CTkButton(
                frame_menu_horizontal,
                text="Ver Reportes",
                command=ver_reportes,
                hover_color="#00BFFF",
                width=150
            ).grid(row=0, column=columna, padx=10, pady=5)
            columna += 1

            def agregar_refugio():
                ventana_refugio = ctk.CTkToplevel()
                ventana_refugio.title("Seleccionar Refugio")
                ventana_refugio.geometry("800x600")

                # Cargar lista de refugios
                refugios = cargar_datos(ALBERGUE_JSON)
                
                # Frame para lista de refugios
                frame_refugios = ctk.CTkScrollableFrame(ventana_refugio)
                frame_refugios.pack(fill="both", expand=True, padx=20, pady=20)

                # Variable para almacenar selección
                refugio_seleccionado = tk.IntVar(value=-1)

                def crear_tarjeta_refugio(refugio):
                    frame = ctk.CTkFrame(frame_refugios, fg_color="#F0F0F0")
                    frame.pack(fill="x", pady=5, padx=5)
                    
                    # Obtener datos actualizados del refugio
                    info_refugio = Refugio.obtener_info(refugio["id"])
                    ocupacion_actual = len(info_refugio["animales"])
                    espacio_disponible = info_refugio["capacidad_maxima"] - ocupacion_actual
                    
                    texto_refugio = (
                        f"🏠 {refugio['nombre']}\n"
                        f"📞 {refugio['telefono']}\n"
                        f"📍 {refugio['direccion']}\n"
                        f"🐾 Capacidad: {ocupacion_actual}/{info_refugio['capacidad_maxima']} "
                        f"(Disponible: {espacio_disponible})"
                    )
                    
                    ctk.CTkRadioButton(
                        frame,
                        text=texto_refugio,
                        variable=refugio_seleccionado,
                        value=refugio['id'],
                        corner_radius=10,
                        state="normal" if espacio_disponible > 0 else "disabled"  # Bloquear si está lleno
                    ).pack(side="left", padx=10, pady=10)
                    
                for refugio in refugios:
                    crear_tarjeta_refugio(refugio)

                def continuar_seleccion_animal():
                    if refugio_seleccionado.get() == -1:
                        messagebox.showerror("Error", "¡Selecciona un refugio!")
                        return
                    
                    # Mostrar animales rescatados por el rescatista
                    animales_rescatados = Rescatista.obtener_animales_rescatados(EstadoSesion.usuario['nombre'])
                    
                    ventana_animales = ctk.CTkToplevel()
                    ventana_animales.title("Seleccionar Animal")
                    ventana_animales.geometry("600x400")
                    ventana_animales.transient(root)
                    ventana_animales.lift()
                    ventana_animales.grab_set()
                    ventana_animales.focus_force()
                    
                    frame_animales = ctk.CTkScrollableFrame(ventana_animales)
                    frame_animales.pack(fill="both", expand=True, padx=20, pady=20)
                    
                    animal_seleccionado = tk.IntVar(value=-1)
                    
                    def crear_tarjeta_animal(animal):
                        frame = ctk.CTkFrame(frame_animales, fg_color="#F8F8F8")
                        frame.pack(fill="x", pady=2)
                        
                        ctk.CTkRadioButton(
                            frame,
                            text=f"🐾 {animal['nombre_provisional']} ({animal['categoria']})\n📅 Rescatado: {animal['fecha_rescate']}",
                            variable=animal_seleccionado,
                            value=animal['id'],
                            corner_radius=8
                        ).pack(side="left", padx=10)
                        
                    for animal in animales_rescatados:
                        crear_tarjeta_animal(animal)
                        
                    def enviar_solicitud():
                        if animal_seleccionado.get() == -1:
                            messagebox.showerror("Error", "¡Selecciona un animal!")
                            return
                            
                        Rescatista.solicitar_ingreso_refugio(
                            animal_seleccionado.get(),
                            refugio_seleccionado.get(),
                            EstadoSesion.usuario['nombre']
                        )
                        messagebox.showinfo("Éxito", "Solicitud enviada al refugio")
                        ventana_animales.destroy()
                        ventana_refugio.destroy()
                        
                    ctk.CTkButton(
                        frame_animales,
                        text="📤 Enviar Solicitud",
                        command=enviar_solicitud,
                        fg_color="#4CAF50"
                    ).pack(pady=10)

                ctk.CTkButton(
                    ventana_refugio,
                    text="Siguiente ➡️",
                    command=continuar_seleccion_animal,
                    fg_color="#2196F3"
                ).pack(pady=10)

            # En el menú del Rescatista, actualizar el comando del botón:
            ctk.CTkButton(
                frame_menu_horizontal,
                text="Agregar a Refugio",
                command=agregar_refugio,  
                hover_color="#00BFFF",
                width=150
            ).grid(row=0, column=columna, padx=10, pady=5)
            columna += 1

            def ver_mis_rescates():
                limpiar_contenido()
                
                ctk.CTkLabel(
                    frame_contenido,
                    text="Mis Rescates",
                    font=("Arial", 18, "bold")
                ).pack(pady=10)
                
                rescatista_actual = next((r for r in cargar_datos(RESCATISTAS_JSON) if r["nombre"] == EstadoSesion.usuario["nombre"]), None)
                
                if not rescatista_actual or "rescates" not in rescatista_actual or len(rescatista_actual["rescates"]) == 0:
                    ctk.CTkLabel(frame_contenido, text="Aún no has rescatado animales 🐾").pack()
                    return
                
                frame_rescates = ctk.CTkScrollableFrame(frame_contenido)
                frame_rescates.pack(fill="both", expand=True)
                
                for rescate in rescatista_actual["rescates"]:
                    reporte = next((r for r in cargar_datos(ANIMALES_JSON) if r["id"] == rescate["id_reporte"]), None)
                    
                    frame = ctk.CTkFrame(frame_rescates, fg_color="#F8F8F8")
                    frame.pack(fill="x", pady=5)
                    
                    texto = (
                        f"🐾 Nombre: {rescate['nombre_animal']}\n"
                        f"📅 Fecha de rescate: {rescate['fecha']}\n"
                        f"📍 Ubicación: {reporte['ubicacion'] if reporte else 'N/A'}"
                    )
                    ctk.CTkLabel(frame, text=texto).pack(side="left", padx=10)

            # Agregar botón "Mis Rescates" al Rescatista:
            ctk.CTkButton(
                frame_menu_horizontal,
                text="Mis Rescates",
                command=ver_mis_rescates,
                hover_color="#00BFFF",
                width=150
            ).grid(row=0, column=columna, padx=10, pady=5)

        elif tipo_usuario == "Albergue":
            def publicar_adopcion():
                # Obtener animales del refugio
                refugio_actual = next((r for r in cargar_datos(ALBERGUE_JSON) if r["nombre"] == EstadoSesion.usuario["nombre"]), None)
                animales_refugio = [a for a in refugio_actual["animales"] if not a.get("adoptado_por")]
                
                ventana_pub = ctk.CTkToplevel()
                ventana_pub.title("Publicar para Adopción")
                ventana_pub.geometry("600x700")
                ventana_pub.transient(root)
                ventana_pub.lift()
                ventana_pub.grab_set()
                ventana_pub.focus_force()
                
                # Variables
                animal_seleccionado = tk.IntVar(value=-1)
                imagen_path = tk.StringVar()
                
                # Contenido
                frame = ctk.CTkFrame(ventana_pub)
                frame.pack(padx=20, pady=20, fill="both", expand=True)
                
                # Seleccionar animal
                ctk.CTkLabel(frame, text="Selecciona un animal:").pack(pady=5)
                frame_animales = ctk.CTkScrollableFrame(frame, height=150)
                frame_animales.pack(fill="x")
                
                for animal in animales_refugio:
                    ctk.CTkRadioButton(
                        frame_animales,
                        text=f"{animal['nombre']} ({animal['categoria']})",
                        variable=animal_seleccionado,
                        value=animal["id_animal"]
                    ).pack(anchor="w", padx=10, pady=2)
                
                # Subir foto
                def seleccionar_imagen():
                    path = filedialog.askopenfilename(filetypes=(("Imágenes", "*.jpg *.jpeg *.png"),))
                    if path:
                        imagen_path.set(path)
                        image = Image.open(path)
                        image.thumbnail((300, 200))
                        ctk_image = ctk.CTkImage(light_image=image, size=image.size)
                        lbl_imagen.configure(image=ctk_image, text="")
                
                lbl_imagen = ctk.CTkLabel(frame, text="🖼️ Sin imagen seleccionada", height=200)
                lbl_imagen.pack(pady=5)
                ctk.CTkButton(frame, text="Subir foto", command=seleccionar_imagen).pack()
                
                # Descripción y requisitos
                ctk.CTkLabel(frame, text="Descripción del animal:").pack(pady=(10,0))
                entrada_desc = ctk.CTkTextbox(frame, height=50)
                entrada_desc.pack(fill="x")
                
                def publicar():
                        if animal_seleccionado.get() == -1 or not imagen_path.get():
                            messagebox.showerror("Error", "Selecciona un animal y sube una foto")
                            return
                        
                        # Copiar imagen a directorio
                        dest_dir = "adopciones_imgs"
                        if not os.path.exists(dest_dir):
                            os.makedirs(dest_dir)
                        dest_filename = f"{animal_seleccionado.get()}_{datetime.now().timestamp()}.jpg"
                        dest_path = os.path.join(dest_dir, dest_filename)
                        shutil.copyfile(imagen_path.get(), dest_path)
                        
                        # Registrar en backend (añadir parámetro imagen_path)
                        Adopcion.publicar_adopcion(
                            id_animal=animal_seleccionado.get(),
                            id_refugio=refugio_actual["id"],
                            descripcion=entrada_desc.get("1.0", "end-1c"),
                            imagen_path=dest_path  # <- Pasar nueva ruta
                        )
                        messagebox.showinfo("Éxito", "¡Animal publicado para adopción!")
                        ventana_pub.destroy()
                
                ctk.CTkButton(frame, text="Publicar", command=publicar, fg_color="#4CAF50").pack(pady=20)
            
            ctk.CTkButton(
                frame_menu_horizontal,
                text="Publicar Adopción",
                command=publicar_adopcion,
                hover_color="#FF69B4",
                width=150
            ).grid(row=0, column=columna, padx=10, pady=5)
            columna += 1

            def ver_solicitudes_refugio():
                limpiar_contenido()
                
                # Obtener ID del refugio (asumiendo que está almacenado en el usuario)
                refugio_actual = next((r for r in cargar_datos(ALBERGUE_JSON) if r["nombre"] == EstadoSesion.usuario["nombre"]), None)
                if not refugio_actual:
                    messagebox.showerror("Error", "Refugio no registrado")
                    return
                
                solicitudes = Refugio.obtener_solicitudes_pendientes(refugio_actual["id"])
                
                # Título
                ctk.CTkLabel(
                    frame_contenido,
                    text="Solicitudes Pendientes",
                    font=("Arial", 18, "bold")
                ).pack(pady=10)
                
                if not solicitudes:
                    ctk.CTkLabel(
                        frame_contenido,
                        text="🎉 No hay solicitudes pendientes",
                        text_color="#4CAF50"
                    ).pack()
                    return
                
                # Listado de solicitudes
                frame_listado = ctk.CTkScrollableFrame(frame_contenido, height=400)
                frame_listado.pack(fill="both", expand=True)
                
                for solicitud in solicitudes:
                    frame_solicitud = ctk.CTkFrame(frame_listado, fg_color="#F8F8F8")
                    frame_solicitud.pack(fill="x", pady=5, padx=5)
                    
                    # Obtener datos del animal
                    animal = next((a for a in cargar_datos(ANIMALES_JSON) if a["id"] == solicitud["id_animal"]), None)
                    
                    # Información
                    ctk.CTkLabel(
                        frame_solicitud,
                        text=f"🐾 Animal: {animal['nombre_provisional'] if animal else 'Desconocido'}\n"
                            f"📅 Fecha rescate: {animal['fecha_rescate'] if animal else 'N/A'}\n"
                            f"👤 Rescatista: {solicitud['rescatista']}",
                        justify="left"
                    ).pack(side="left", padx=10)
                    
                    # Botones de acción
                    frame_botones = ctk.CTkFrame(frame_solicitud, fg_color="transparent")
                    frame_botones.pack(side="right", padx=10)
                    
                    def aprobar_solicitud(id_solicitud=solicitud["id"]):
                        # Ventana para ingresar nombre definitivo
                        ventana_nombre = ctk.CTkToplevel()
                        ventana_nombre.geometry("300x150")
                        ventana_nombre.transient(root)
                        ventana_nombre.lift()
                        ventana_nombre.grab_set()
                        ventana_nombre.focus_force()
                        
                        ctk.CTkLabel(ventana_nombre, text="Nombre definitivo del animal:").pack(pady=10)
                        entrada_nombre = ctk.CTkEntry(ventana_nombre)
                        entrada_nombre.pack(pady=5)
                        
                        def confirmar_aprobacion():
                            nombre = entrada_nombre.get()
                            if not nombre:
                                messagebox.showerror("Error", "¡El nombre es obligatorio!")
                                return
                                
                            resultado, mensaje = Refugio.responder_solicitud(id_solicitud, "Aprobado", nombre)
                            if resultado:
                                messagebox.showinfo("Éxito", f"Animal registrado como: {nombre}")
                                ver_solicitudes_refugio()
                                ventana_nombre.destroy()
                            else:
                                messagebox.showerror("Error", mensaje)
                        
                        ctk.CTkButton(
                            ventana_nombre,
                            text="Confirmar",
                            command=confirmar_aprobacion
                        ).pack()
                            
                    def rechazar_solicitud(id_solicitud=solicitud["id"]):
                        if Refugio.responder_solicitud(id_solicitud, "Rechazado"):
                            messagebox.showinfo("Éxito", "Solicitud rechazada ❌")
                            ver_solicitudes_refugio()
                    
                    ctk.CTkButton(
                        frame_botones,
                        text="Aprobar",
                        fg_color="#4CAF50",
                        command=aprobar_solicitud,
                        width=80
                    ).pack(pady=2)
                    
                    ctk.CTkButton(
                        frame_botones,
                        text="Rechazar",
                        fg_color="#FF5252",
                        command=rechazar_solicitud,
                        width=80
                    ).pack(pady=2)

            # Actualizar el botón del refugio:
            ctk.CTkButton(
                frame_menu_horizontal,
                text="Ver Solicitudes",
                command=ver_solicitudes_refugio, 
                hover_color="#FF69B4",
                width=150
            ).grid(row=0, column=columna, padx=10, pady=5)
            columna += 1  # Ajustar posición de los demás botones

            def modificar_datos_refugio():
                # Obtener datos actuales del refugio
                refugio_actual = next((r for r in cargar_datos(ALBERGUE_JSON) if r["nombre"] == EstadoSesion.usuario["nombre"]), None)
                
                ventana_edicion = ctk.CTkToplevel()
                ventana_edicion.title("Editar Datos del Refugio")
                ventana_edicion.geometry("500x400")
                ventana_edicion.transient(root)
                ventana_edicion.lift()
                ventana_edicion.grab_set()
                ventana_edicion.focus_force()
                
                frame_form = ctk.CTkFrame(ventana_edicion)
                frame_form.pack(padx=20, pady=20, fill="both", expand=True)
                
                ubicacion_seleccionada = tk.StringVar(value=refugio_actual.get("direccion", ""))
                coordenadas_refugio = refugio_actual.get("coordenadas", None)

                def callback_ubicacion(ubicacion):
                    nonlocal coordenadas_refugio
                    coordenadas_refugio = ubicacion["coordenadas"]
                    ubicacion_seleccionada.set(ubicacion["direccion"] or "Coordenadas: " + ", ".join(map(str, coordenadas_refugio)))

                ctk.CTkLabel(frame_form, text="Ubicación:").pack(anchor="w", pady=(10, 0))
                entrada_ubicacion = ctk.CTkEntry(frame_form, textvariable=ubicacion_seleccionada, state="readonly")
                entrada_ubicacion.pack(fill="x", pady=(0, 5))

                def abrir_mapa():
                    mapa_dialog = MapaDialog(root, callback_ubicacion)
                    mapa_dialog.transient(root)
                    mapa_dialog.lift()
                    mapa_dialog.grab_set()
                    mapa_dialog.focus_force()

                ctk.CTkButton(
                    frame_form,
                    text="📍 Seleccionar en mapa",
                    command = abrir_mapa,
                    fg_color="#2196F3",
                    hover_color="#1976D2"
                ).pack(pady=(0, 10))
                
                ctk.CTkLabel(frame_form, text="Teléfono:").pack(pady=(10,0))
                entrada_telefono = ctk.CTkEntry(frame_form)
                entrada_telefono.insert(0, refugio_actual["telefono"])
                entrada_telefono.pack(fill="x")
                
                ctk.CTkLabel(frame_form, text="Capacidad máxima:").pack(pady=(10,0))
                entrada_capacidad = ctk.CTkEntry(frame_form)
                entrada_capacidad.insert(0, str(refugio_actual["capacidad_maxima"]))
                entrada_capacidad.pack(fill="x")
                
                def guardar_cambios():
                    try:
                        nueva_capacidad = int(entrada_capacidad.get())
                        if nueva_capacidad < len(refugio_actual["animales"]):
                            raise ValueError("La capacidad no puede ser menor a los animales actuales")
                    except ValueError:
                        messagebox.showerror("Error", "Capacidad debe ser un número válido")
                        return
                    
                    if Refugio.actualizar_datos(
                        refugio_actual["id"],
                        entrada_ubicacion.get(),
                        entrada_telefono.get(),
                        nueva_capacidad
                    ):
                        messagebox.showinfo("Éxito", "Datos actualizados correctamente")
                        ventana_edicion.destroy()
                    else:
                        messagebox.showerror("Error", "Error al actualizar datos")

                ctk.CTkButton(
                    frame_form,
                    text="💾 Guardar Cambios",
                    command=guardar_cambios,
                    fg_color="#4CAF50"
                ).pack(pady=20)

            # En el menú del Albergue, agregar nuevo botón
            ctk.CTkButton(
                frame_menu_horizontal,
                text="Modificar Datos",
                command=modificar_datos_refugio,
                hover_color="#FF69B4",
                width=150
            ).grid(row=0, column=columna, padx=10, pady=5)
            columna += 1

            def ver_solicitudes_adopcion():
                limpiar_contenido()
                
                refugio_actual = next((r for r in cargar_datos(ALBERGUE_JSON) if r["nombre"] == EstadoSesion.usuario["nombre"]), None)
                solicitudes = cargar_datos(SOLICITUDES_ADOPCION_JSON)
                solicitudes_refugio = [
                    s for s in solicitudes 
                    if s["estado"] == "Pendiente"  # <- Filtro clave
                    and s["id_adopcion"] in [a["id"] for a in cargar_datos(ADOPCIONES_JSON) 
                    if a["id_refugio"] == refugio_actual["id"]]
                ]
                
                ctk.CTkLabel(
                    frame_contenido,
                    text="Solicitudes de Adopción",
                    font=("Arial", 18, "bold")
                ).pack(pady=10)
                
                if not solicitudes_refugio:
                    ctk.CTkLabel(frame_contenido, text="🎉 No hay solicitudes pendientes").pack()
                    return
                
                frame_listado = ctk.CTkScrollableFrame(frame_contenido, height=400)
                frame_listado.pack(fill="both", expand=True)
                
                for solicitud in solicitudes_refugio:
                    frame_sol = ctk.CTkFrame(frame_listado, fg_color="#F8F8F8")
                    frame_sol.pack(fill="x", pady=5)
                    
                    # Info
                    adopcion = next((a for a in cargar_datos(ADOPCIONES_JSON) if a["id"] == solicitud["id_adopcion"]), None)
                    animal = next((a for a in cargar_datos(ANIMALES_JSON) if a["id"] == adopcion["id_animal"]), None) if adopcion else None
                    
                    texto = (
                        f"📅 Fecha: {solicitud['fecha']}\n"
                        f"👤 Solicitante: {solicitud['ciudadano']}\n"
                        f"🐾 Animal: {animal['nombre_provisional'] if animal else 'N/A'}\n"
                        f"💬 Mensaje: {solicitud['mensaje']}"
                    )
                    ctk.CTkLabel(frame_sol, text=texto, justify="left").pack(side="left", padx=10)
                    
                    # Botones
                    frame_btns = ctk.CTkFrame(frame_sol, fg_color="transparent")
                    frame_btns.pack(side="right", padx=10)
                    
                    def aprobar(id_sol=solicitud["id"]):
                        Adopcion.responder_solicitud(id_sol, "Aprobado")
                        messagebox.showinfo("Éxito", "Solicitud aprobada ✅")
                        ver_solicitudes_adopcion()
                    
                    def rechazar(id_sol=solicitud["id"]):
                        Adopcion.responder_solicitud(id_sol, "Rechazado")
                        messagebox.showinfo("Éxito", "Solicitud rechazada ❌")
                        ver_solicitudes_adopcion()
                    
                    ctk.CTkButton(frame_btns, text="Aprobar", fg_color="#4CAF50", command=aprobar, width=80).pack(pady=2)
                    ctk.CTkButton(frame_btns, text="Rechazar", fg_color="#FF5252", command=rechazar, width=80).pack(pady=2)

            # En el menú del Albergue, agregar botón:
            ctk.CTkButton(
                frame_menu_horizontal,
                text="Ver Solicitudes Adopción",
                command=ver_solicitudes_adopcion,
                hover_color="#FF69B4",
                width=150
            ).grid(row=0, column=columna, padx=10, pady=5)

    root.mainloop()

def pantalla_ingresar():
    root1 = ctk.CTkToplevel()
    root1.title("Ingresar")
    root1.geometry("400x600")
    root1.transient(root)
    root1.lift()
    root1.grab_set()
    root1.focus_force()

    root1.grid_columnconfigure((0, 1, 2, 3), weight=1)
    root1.grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=1)

    frame_bienvenido = ctk.CTkFrame (
        master=root1, 
        fg_color="#A6F8F1",
        corner_radius=8
    )
    frame_bienvenido.grid(
        column=1, row=0,
        columnspan=2,
        padx=10, pady=4,
        sticky="nsew"
    )

    frame_formulario = ctk.CTkFrame (
        master=root1, 
        fg_color="#A6F8F1",
        corner_radius=8
    )
    frame_formulario.grid(
        column=1, row=2,
        columnspan=2, rowspan=3,
        padx=10, pady=4,
        sticky="nsew"
    )

    ctk.CTkLabel(frame_bienvenido, text="Bienvenid@", font=("Arial", 25)).pack(pady=10, expan= True)

        
    ctk.CTkLabel(frame_formulario, text="Nombre:").pack()
    entrada_nombre_login = ctk.CTkEntry(frame_formulario)
    entrada_nombre_login.pack()

    ctk.CTkLabel(frame_formulario, text="Password:").pack()
    entrada_password_login = ctk.CTkEntry(frame_formulario, show = "*")
    entrada_password_login.pack()

    def iniciar():
        nombre = entrada_nombre_login.get()
        password = entrada_password_login.get()
        
        if not nombre or not password:
            messagebox.showerror("Error", "Complete todos los campos")
            return
        
        resultado, mensaje = Usuario.iniciar_sesion(nombre, password)
        
        if resultado:
            messagebox.showinfo("Éxito", f"Bienvenido {nombre}!")
            root1.destroy()
            actualizar_pantalla_principal()
            root.update_idletasks()  
        else:
            messagebox.showerror("Error", mensaje)
    
    ctk.CTkButton(frame_formulario, text="inciar sesion", command=iniciar, hover_color = "#12E82E").pack(pady=10)

    ctk.CTkLabel(frame_formulario, text="No tienes una cuenta?", font=("Arial", 10)).pack(pady=2)
    
    ctk.CTkButton(frame_formulario, text="Registrar", command=pantalla_registro, hover_color = "#12E82E").pack(pady=2)

    root1.mainloop()

def pantalla_registro():
    root2 = ctk.CTkToplevel()
    root2.title("Ingresar")
    root2.geometry("400x600")
    root2.after(100, lambda: root2.focus())
    root2.transient(root)
    root2.lift()
    root2.grab_set()
    root2.focus_force()

    root2.grid_columnconfigure((0, 1, 2, 3), weight=1)
    root2.grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=1)

    frame_nuevo_usuarios = ctk.CTkFrame (
        master=root2, 
        fg_color="#A6F8F1",
        corner_radius=8
    )
    frame_nuevo_usuarios.grid(
        column=1, row=0,
        columnspan=2,
        padx=10, pady=4,
        sticky="nsew"
    )

    frame_formulario2 = ctk.CTkFrame (
        master=root2, 
        fg_color="#A6F8F1",
        corner_radius=8
    )
    frame_formulario2.grid(
        column=1, row=2,
        columnspan=2, rowspan=3,
        padx=10, pady=4,
        sticky="nsew"
    )
    
    ctk.CTkLabel(frame_nuevo_usuarios, text="Nuevo Usuario", font=("Arial", 20)).pack(pady=10, expan= True)

    ctk.CTkLabel(frame_formulario2, text="Nombre:").pack()
    entrada_nombre_register = ctk.CTkEntry(frame_formulario2)
    entrada_nombre_register.pack()

    ctk.CTkLabel(frame_formulario2, text="Correo:").pack()
    entrada_correo = ctk.CTkEntry(frame_formulario2)
    entrada_correo.pack()

    ctk.CTkLabel(frame_formulario2, text="Password:").pack()
    entrada_password_register = ctk.CTkEntry(frame_formulario2)
    entrada_password_register.pack()

    filtro = ctk.CTkComboBox(
        frame_formulario2,
        values=["Ciudadano", "Rescatista", "Albergue"],
        state="readonly"
    )
    ctk.CTkLabel(frame_formulario2, text="Tipo de cuenta:").pack()
    filtro.pack(padx=5)
    

    def registrar():
        nombre = entrada_nombre_register.get()
        correo = entrada_correo.get()
        password = entrada_password_register.get()
        tipo = filtro.get()
        
        resultado, mensaje = Usuario.registrarse(nombre, correo, password, tipo)
        
        if resultado:
            messagebox.showinfo("Éxito", mensaje)
            root2.destroy()
            pantalla_ingresar()  # Redirigir a login
        else:
            messagebox.showerror("Error", mensaje)
    
    ctk.CTkButton(frame_formulario2, text="completar registro", command=registrar, hover_color = "#12E82E").pack(pady=10)

    root2.mainloop()


if __name__ == "__main__":
    pantalla_inicial()