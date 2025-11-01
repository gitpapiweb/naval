# Papiweb desarrollos informaticos
# (Adaptado por Gemini para pygbag/web)
import io
import base64
import os
import json
import random
import sys
import asyncio  # <-- IMPORTANTE: Añadido para la web
import pygame

# --- Constantes ---
ANCHO_PANTALLA = 800
ALTO_PANTALLA = 600
COLOR_MAR = (0, 0, 50)
COLOR_BLANCO = (255, 255, 255)
FPS = 60
VELOCIDAD_JUGADOR = 5

# --- Clase para las Partículas de Explosión ---
class Particula(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self._layer = 5
        self.image = pygame.Surface((random.randint(2, 5), random.randint(2, 5)))
        self.image.fill(random.choice([(255, 0, 0), (255, 165, 0), (255, 255, 0)]))
        self.rect = self.image.get_rect(center=(x, y))
        self.velocidad_x = random.uniform(-2, 2)
        self.velocidad_y = random.uniform(-2, 2)
        self.vida_util = random.randint(15, 30) 
        self.contador_vida = 0

    def update(self):
        self.rect.x += self.velocidad_x
        self.rect.y += self.velocidad_y
        self.contador_vida += 1
        if self.contador_vida > self.vida_util:
            self.kill() 
        
        escala = 1 - (self.contador_vida / self.vida_util)
        ancho_original, alto_original = self.image.get_size()
        nuevo_ancho = max(1, int(ancho_original * escala))
        nuevo_alto = max(1, int(alto_original * escala))
        self.rect.width = nuevo_ancho
        self.rect.height = nuevo_alto

# --- Clase para las Olas (Efecto visual del barco) ---
class Ola(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self._layer = 2 
        self.radio_inicial = random.randint(5, 10)
        self.radio = self.radio_inicial
        self.velocidad_expansion = random.uniform(0.2, 0.5)
        self.color = (200, 200, 255) 
        self.vida_util = random.randint(40, 80)
        self.contador_vida = 0
        
        self.image = pygame.Surface((self.radio * 2, self.radio * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color + (100,), (self.radio, self.radio), self.radio, 1)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.contador_vida += 1
        if self.contador_vida > self.vida_util:
            self.kill()
            return
        
        self.radio += self.velocidad_expansion
        
        alpha = max(0, 255 * (1 - (self.contador_vida / self.vida_util)))
        centro_actual = self.rect.center
        
        self.image = pygame.Surface((int(self.radio * 2), int(self.radio * 2)), pygame.SRCALPHA)
        color_actual = self.color + (int(alpha),)
        pygame.draw.circle(self.image, color_actual, (int(self.radio), int(self.radio)), int(self.radio), 1)
        self.rect = self.image.get_rect(center=centro_actual)

# --- Clase para el Jugador (Barco) ---
class Jugador(pygame.sprite.Sprite):
    def __init__(self, ruta_assets):
        super().__init__()
        
        self.imagenes_barco = []
        self.imagen_original_por_nivel = {}
        try:
            barco1 = pygame.image.load(os.path.join(ruta_assets, "barco.png")).convert_alpha()
            barco2 = pygame.image.load(os.path.join(ruta_assets, "barco2.png")).convert_alpha()
            escala_barco1 = (70, 52) 
            escala_barco2 = (70, 52) 
            
            img1 = pygame.transform.scale(barco1, escala_barco1)
            img2 = pygame.transform.scale(barco2, escala_barco2)
            
            self.imagenes_barco.append(img1)
            self.imagenes_barco.append(img2)
            
            self.imagen_original_por_nivel[1] = img1
            self.imagen_original_por_nivel[2] = img2
            self.imagen_original_por_nivel[3] = img2
            
        except pygame.error as e:
            print(f"Error al cargar imágenes del barco: {e}")
            fallback_surface = pygame.Surface((70, 52))
            fallback_surface.fill(COLOR_BLANCO)
            self.imagenes_barco = [fallback_surface, fallback_surface]
            self.imagen_original_por_nivel[1] = fallback_surface
            self.imagen_original_por_nivel[2] = fallback_surface
            self.imagen_original_por_nivel[3] = fallback_surface

        self.image = self.imagenes_barco[0]
        self.rect = self.image.get_rect()
        
        self.sombra = self.crear_sombra(self.image)
        self.sombra_offset = (4, 4) 
        
        self.rect.centerx = ANCHO_PANTALLA // 2
        self.rect.bottom = ALTO_PANTALLA - 10
        self.velocidad_x = 0
        self.cadencia_disparo = 500 
        self.ultimo_disparo = pygame.time.get_ticks()
        self.cadencia_olas = 100
        self.ultima_ola = pygame.time.get_ticks()
        
        self.nivel_actual = 1

    def crear_sombra(self, imagen):
        sombra = imagen.copy()
        sombra.fill((0, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
        sombra.set_alpha(100) 
        return sombra

    def cambiar_aspecto(self, nivel):
        self.nivel_actual = nivel
        img_a_usar = self.imagen_original_por_nivel.get(nivel, self.imagen_original_por_nivel[1])
        
        if self.image is not img_a_usar or self.image.get_width() == 1:
            self.image = img_a_usar
            
            pos_actual = self.rect.center
            self.rect = self.image.get_rect(center=pos_actual)
            self.sombra = self.crear_sombra(self.image)
            
        return self.image

    def generar_olas(self):
        ahora = pygame.time.get_ticks()
        if self.velocidad_x != 0 and ahora - self.ultima_ola > self.cadencia_olas:
            self.ultima_ola = ahora
            pos_ola_izquierda = (self.rect.left, self.rect.centery + 10)
            pos_ola_derecha = (self.rect.right, self.rect.centery + 10)
            return [Ola(*pos_ola_izquierda), Ola(*pos_ola_derecha)]
        return []

    def update(self):
        self.velocidad_x = 0
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_LEFT]:
            self.velocidad_x = -VELOCIDAD_JUGADOR
        if teclas[pygame.K_RIGHT]:
            self.velocidad_x = VELOCIDAD_JUGADOR
            
        self.rect.x += self.velocidad_x
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > ANCHO_PANTALLA:
            self.rect.right = ANCHO_PANTALLA

    def disparar(self):
        ahora = pygame.time.get_ticks()
        if ahora - self.ultimo_disparo > self.cadencia_disparo:
            self.ultimo_disparo = ahora
            return DisparoJugador(self.rect.centerx, self.rect.top)
        return None

# --- Clase para el Disparo del Jugador ---
class DisparoJugador(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self._layer = 4
        self.image = pygame.Surface((5, 10))
        self.image.fill((0, 255, 0)) 
        self.rect = self.image.get_rect(center=(x, y))
        self.velocidad_y = -8

    def update(self):
        self.rect.y += self.velocidad_y
        if self.rect.bottom < 0:
            self.kill()

# --- Clase para las Bombas ---
class Bomba(pygame.sprite.Sprite):
    def __init__(self, x, y, tipo_bomba=1):
        super().__init__()
        self._layer = 4
        self.tipo_bomba = tipo_bomba
        if self.tipo_bomba == 1:
            self.image = pygame.Surface((8, 16))
            self.image.fill((255, 255, 0)) 
            self.velocidad_y = 5
        elif self.tipo_bomba == 2:
            self.image = pygame.Surface((10, 20))
            self.image.fill((255, 100, 0))
            self.velocidad_y = 7
        else: 
            self.image = pygame.Surface((6, 12))
            self.image.fill((0, 255, 255))
            self.velocidad_y = 9
        self.rect = self.image.get_rect(center=(x, y))
        
        self.sombra = self.crear_sombra(self.image)
        self.sombra_offset = (3, 3)

    def crear_sombra(self, imagen):
        sombra = imagen.copy()
        sombra.fill((0, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
        sombra.set_alpha(100)
        return sombra

    def update(self):
        self.rect.y += self.velocidad_y
        if self.rect.top > ALTO_PANTALLA:
            self.kill()

# --- Clase para el Enemigo (Avión) ---
class Enemigo(pygame.sprite.Sprite):
    def __init__(self, ruta_assets):
        super().__init__()
        self._layer = 4
        
        self.imagenes_avion = []
        try:
            avion1 = pygame.image.load(os.path.join(ruta_assets, "avion.png")).convert_alpha()
            avion2 = pygame.image.load(os.path.join(ruta_assets, "avion2.png")).convert_alpha()
            avion3 = pygame.image.load(os.path.join(ruta_assets, "avion3.png")).convert_alpha()
            
            escala1 = (45, 31)
            escala2 = (55, 36)
            escala3 = (65, 45)
            
            self.imagenes_avion.append(pygame.transform.scale(avion1, escala1))
            self.imagenes_avion.append(pygame.transform.scale(avion2, escala2))
            self.imagenes_avion.append(pygame.transform.scale(avion3, escala3))
        except pygame.error as e:
            print(f"Error al cargar imágenes de avión: {e}")
            fallback_surface = pygame.Surface((45, 31))
            fallback_surface.fill((200, 0, 0))
            self.imagenes_avion = [fallback_surface, fallback_surface, fallback_surface]

        self.tipo_enemigo = 0 
        self.image = self.imagenes_avion[0]
        self.rect = self.image.get_rect()
        
        self.estado_vuelo = "descenso" 
        self.velocidad_x_salida = 0 
        self.ultimo_disparo = pygame.time.get_ticks()

        self.configurar_posicion_inicial()
        self.configurar_movimiento()

    def crear_sombra(self, imagen):
        sombra = imagen.copy()
        sombra.fill((0, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
        sombra.set_alpha(100)
        return sombra
    
    def configurar_posicion_inicial(self):
        self.rect.x = random.randint(0, ANCHO_PANTALLA - self.rect.width)
        self.rect.y = random.randint(-100, -40)

    def configurar_movimiento(self):
        self.tipo_enemigo = random.randint(1, 3)
        idx = min(self.tipo_enemigo - 1, len(self.imagenes_avion) - 1)
        self.image = self.imagenes_avion[idx]
        
        pos_actual = self.rect.center
        self.rect = self.image.get_rect(center=pos_actual) 
        self.sombra = self.crear_sombra(self.image)
        self.sombra_offset = (4, 4)
        
        if self.tipo_enemigo == 1: 
            self.amplitud_onda = random.randint(50, 150)
            self.frecuencia_onda = random.uniform(0.01, 0.03)
            self.centro_x = self.rect.centerx
            self.angulo = 0
            self.velocidad_y = random.randint(2, 4)
            self.cadencia_disparo = 60 
            self.tipo_bomba = 1
        elif self.tipo_enemigo == 2: 
            self.velocidad_y = random.randint(4, 6)
            self.cadencia_disparo = 45 
            self.tipo_bomba = 2
        elif self.tipo_enemigo == 3: 
            self.velocidad_y = random.randint(2, 3)
            self.velocidad_x_zigzag = random.choice([-2, 2])
            self.cambio_zigzag_timer = random.randint(30, 90) 
            self.contador_zigzag = 0
            self.cadencia_disparo = 90 
            self.tipo_bomba = 3

        self.estado_vuelo = "descenso"
        self.velocidad_x_salida = 0
        self.ultimo_disparo = pygame.time.get_ticks()

    def resetear_enemigo(self):
        self.configurar_posicion_inicial()
        self.configurar_movimiento()

    def update(self):
        if self.estado_vuelo == "descenso":
            self.rect.y += self.velocidad_y
            
            if self.tipo_enemigo == 1:
                self.angulo += self.frecuencia_onda
                offset_x = self.amplitud_onda * pygame.math.Vector2(1, 0).rotate(self.angulo * 180 / 3.14159).y
                self.rect.centerx = self.centro_x + offset_x
            elif self.tipo_enemigo == 3: 
                self.contador_zigzag += 1
                if self.contador_zigzag >= self.cambio_zigzag_timer:
                    self.velocidad_x_zigzag *= -1 
                    self.contador_zigzag = 0
                    self.cambio_zigzag_timer = random.randint(30, 90)
                self.rect.x += self.velocidad_x_zigzag
                if self.rect.left < 0 or self.rect.right > ANCHO_PANTALLA:
                    self.velocidad_x_zigzag *= -1
                    self.rect.x += self.velocidad_x_zigzag 
            
            if self.rect.top > ALTO_PANTALLA:
                self.estado_vuelo = "salida"
                self.velocidad_x_salida = random.choice([-10, 10]) 
                self.velocidad_y = 0 
                
        elif self.estado_vuelo == "salida":
            self.rect.x += self.velocidad_x_salida
            
            if self.rect.right < 0 or self.rect.left > ANCHO_PANTALLA:
                self.resetear_enemigo()
                
    def disparar(self):
        if self.estado_vuelo != "descenso":
            return None
            
        ahora = pygame.time.get_ticks()
        if ahora - self.ultimo_disparo > self.cadencia_disparo * (1000 / FPS):
            self.ultimo_disparo = ahora
            return Bomba(self.rect.centerx, self.rect.bottom, self.tipo_bomba)
        return None

# --- Clase Principal del Juego ---
class Juego:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        # --- Configuración de Pantalla (Simplificado para web) ---
        # pygbag se encargará de escalar esta pantalla de 800x600
        self.pantalla = pygame.display.set_mode((ANCHO_PANTALLA, ALTO_PANTALLA))
        self.ANCHO_JUEGO = ANCHO_PANTALLA
        self.ALTO_JUEGO = ALTO_PANTALLA

        pygame.display.set_caption("Defensor Naval - por Papiweb desarrollos informaticos")
        
        self.reloj = pygame.time.Clock()
        
        # --- Configuración de Rutas de Assets (Simplificado para web) ---
        # Se asume que 'assets' está en la misma carpeta que el script
        self.directorio_assets = "assets"

        # --- Cargar Audio ---
        try:
            self.sonido_explosion = pygame.mixer.Sound(os.path.join(self.directorio_assets, "fall.ogg"))
            self.sonido_disparo = pygame.mixer.Sound(os.path.join(self.directorio_assets, "gun.ogg"))
            
            self.musica_presentacion = os.path.join(self.directorio_assets, "epic.ogg")
            self.musica_theme = os.path.join(self.directorio_assets, "theme.ogg")
            self.musica_dance = os.path.join(self.directorio_assets, "dance.ogg")
            self.musica_score = os.path.join(self.directorio_assets, "score.png") # ¿Es .png o .ogg? Asumo ogg
            
            # CORRECCIÓN: Si score es música, debe ser .ogg (como los otros)
            # Si era un typo y es 'score.ogg', descomenta la línea de abajo y borra la de arriba
            # self.musica_score = os.path.join(self.directorio_assets, "score.ogg")
            
            # Si 'score.png' es un FONDO, entonces falta el audio 'score.ogg'
            # Por ahora, lo pondré en None si es .png
            if self.musica_score.endswith(".png"):
                print("Advertencia: 'musica_score' apunta a un .png, se usará 'theme.ogg' en su lugar.")
                self.musica_score = self.musica_theme # Usar theme como fallback

            self.musica_actual = self.musica_theme
            
        except pygame.error as e:
            print(f"Error al cargar audio desde la carpeta 'assets': {e}")
            self.sonido_explosion = None
            self.sonido_disparo = None
            self.musica_presentacion = None
            self.musica_theme = None
            self.musica_dance = None
            self.musica_score = None
            self.musica_actual = None

        # Cargar assets de la presentación
        try:
            self.fondo_presentacion = pygame.image.load(os.path.join(self.directorio_assets, "presentacion.png")).convert()
            self.fondo_presentacion = pygame.transform.scale(self.fondo_presentacion, (self.ANCHO_JUEGO, self.ALTO_JUEGO))
            self.imagenes_adelanto = [
                pygame.transform.scale(pygame.image.load(os.path.join(self.directorio_assets, "barco.png")).convert_alpha(), (160, 120)),
                pygame.transform.scale(pygame.image.load(os.path.join(self.directorio_assets, "avion.png")).convert_alpha(), (100, 70)),
                pygame.transform.scale(pygame.image.load(os.path.join(self.directorio_assets, "barco2.png")).convert_alpha(), (160, 120)),
                pygame.transform.scale(pygame.image.load(os.path.join(self.directorio_assets, "avion2.png")).convert_alpha(), (120, 80)),
                pygame.transform.scale(pygame.image.load(os.path.join(self.directorio_assets, "avion3.png")).convert_alpha(), (140, 100)),
            ]
        except pygame.error as e:
            print(f"Error al cargar imágenes de la presentación: {e}")
            self.fondo_presentacion = pygame.Surface((self.ANCHO_JUEGO, self.ALTO_JUEGO))
            self.fondo_presentacion.fill(COLOR_MAR)
            self.imagenes_adelanto = []

        self.transicionando_musica = False
        self.volumen_objetivo = 0.5
        self.tiempo_transicion = 1000 
        self.ALTERNAR_MUSICA = pygame.USEREVENT + 2
        pygame.time.set_timer(self.ALTERNAR_MUSICA, 30000) 

        # Cargar fondos de niveles
        self.fondos = []
        try:
            fondo1 = pygame.image.load(os.path.join(self.directorio_assets, "fondo.png")).convert()
            fondo2 = pygame.image.load(os.path.join(self.directorio_assets, "fondo2.png")).convert()
            fondo3 = pygame.image.load(os.path.join(self.directorio_assets, "fondo3.png")).convert()
            fondo_score = pygame.image.load(os.path.join(self.directorio_assets, "score.png")).convert()
            self.fondos.append(pygame.transform.scale(fondo1, (self.ANCHO_JUEGO, self.ALTO_JUEGO)))
            self.fondos.append(pygame.transform.scale(fondo2, (self.ANCHO_JUEGO, self.ALTO_JUEGO)))
            self.fondos.append(pygame.transform.scale(fondo3, (self.ANCHO_JUEGO, self.ALTO_JUEGO)))
            self.fondos_score = pygame.transform.scale(fondo_score, (self.ANCHO_JUEGO, self.ALTO_JUEGO))
        except pygame.error as e:
            print(f"Error al cargar imágenes de fondo: {e}")
            fallback_fondo = pygame.Surface((self.ANCHO_JUEGO, self.ALTO_JUEGO))
            fallback_fondo.fill(COLOR_MAR)
            self.fondos = [fallback_fondo, fallback_fondo, fallback_fondo]
            self.fondos_score = fallback_fondo

        self.puntuacion = 0
        self.vidas = 3
        self.nivel = 1
        self.font = pygame.font.Font(None, 36)
        self.font_marca = pygame.font.Font(None, 24)

        self.inmune = False
        self.tiempo_inmunidad_inicio = 0
        self.duracion_inmunidad = 3000
        self.periodo_parpadeo = 100 

        self.highscores = []
        self.nombre_jugador = ""
        # Ruta simplificada para la web
        self.ruta_highscore = "highscores.json"
        self.cargar_highscores()

        self.todos_los_sprites = pygame.sprite.LayeredUpdates()
        self.particulas = pygame.sprite.Group()
        self.olas = pygame.sprite.Group()
        self.enemigos = pygame.sprite.Group()
        self.bombas_enemigas = pygame.sprite.Group()
        self.disparos_jugador = pygame.sprite.Group()
        
        self.jugador = Jugador(self.directorio_assets)
        self.jugador._layer = 3
        self.todos_los_sprites.add(self.jugador)
        
        self.ADDENEMY = pygame.USEREVENT + 1
        pygame.time.set_timer(self.ADDENEMY, 1000) 
        self.jugando = True
        # Flag para el bucle principal (main)
        self.quiere_reiniciar = False

    # --- Funciones de escalado eliminadas (calcular_escala, dibujar_a_pantalla_real) ---
    # --- pygbag se encarga de esto ---

    def pantalla_presentacion(self):
        if self.musica_presentacion:
            try:
                pygame.mixer.music.load(self.musica_presentacion)
                pygame.mixer.music.play(-1)
                pygame.mixer.music.set_volume(0.7)
            except pygame.error as e:
                print(f"Error al reproducir música de presentación: {e}")

        indice_imagen = 0
        ultimo_cambio = pygame.time.get_ticks()
        duracion_imagen = 2000 
        presentacion_activa = True

        while presentacion_activa:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.jugando = False # Indicar al bucle 'ejecutar' que no inicie
                    presentacion_activa = False # Salir de este bucle
                if evento.type == pygame.KEYDOWN or evento.type == pygame.MOUSEBUTTONDOWN:
                    presentacion_activa = False

            if not presentacion_activa:
                break

            # --- DIBUJAR (Directo a self.pantalla) ---
            self.pantalla.blit(self.fondo_presentacion, (0, 0))
            
            ahora = pygame.time.get_ticks()
            if ahora - ultimo_cambio > duracion_imagen and self.imagenes_adelanto:
                indice_imagen = (indice_imagen + 1) % len(self.imagenes_adelanto)
                ultimo_cambio = ahora

            if self.imagenes_adelanto:
                imagen_actual = self.imagenes_adelanto[indice_imagen]
                rect_imagen = imagen_actual.get_rect(center=(self.ANCHO_JUEGO // 2, self.ALTO_JUEGO // 2))
                self.pantalla.blit(imagen_actual, rect_imagen)

            self.dibujar_texto("Defensor Naval", 60, self.ANCHO_JUEGO // 2, 50, self.font)
            self.dibujar_texto("Presiona cualquier tecla para comenzar", 30, self.ANCHO_JUEGO // 2, self.ALTO_JUEGO - 100, self.font)
            
            texto_marca = "Un juego de: Papiweb desarrollos informaticos"
            self.dibujar_texto(texto_marca, 24, self.ANCHO_JUEGO // 2, self.ALTO_JUEGO - 50, self.font_marca)

            # --- DIBUJAR A PANTALLA REAL (ESCALADO) ---
            pygame.display.flip() # <-- Reemplaza a dibujar_a_pantalla_real
            self.reloj.tick(FPS)

        pygame.mixer.music.stop()
        
        # Si el usuario NO cerró la ventana, cargar música del tema
        if self.jugando and self.musica_theme:
            try:
                pygame.mixer.music.load(self.musica_theme)
                pygame.mixer.music.play(-1)
                pygame.mixer.music.set_volume(self.volumen_objetivo)
            except pygame.error as e:
                print(f"Error al reproducir música de tema: {e}")

    # --- Convertido a ASYNC para la web ---
    async def ejecutar(self):
        self.pantalla_presentacion()
        
        # self.jugando se pondrá en False si el usuario cierra en la presentación
        while self.jugando:
            self.reloj.tick(FPS)
            self.eventos() 
            # eventos() puede cambiar self.jugando a False (con ESC)
            if not self.jugando:
                break
                
            self.actualizar() 
            # actualizar() puede cambiar self.jugando a False (vidas=0)
            if not self.jugando:
                break
                
            self.dibujar() # dibujar() ahora solo llama a pygame.display.flip()
            
            # --- ¡LA PARTE MÁS IMPORTANTE PARA LA WEB! ---
            # Cede el control al navegador para que no se congele
            await asyncio.sleep(0)
        
        # Si el juego termina por pérdida de vidas (no por ESC)
        if self.vidas <= 0:
            self.pantalla_game_over()
        
        # Al salir de esta función, el bucle 'main' de abajo
        # comprobará self.quiere_reiniciar

    def cambiar_musica(self):
        pygame.mixer.music.stop()
        try:
            if self.musica_actual == self.musica_theme and self.musica_dance:
                pygame.mixer.music.load(self.musica_dance)
                self.musica_actual = self.musica_dance
            elif self.musica_theme:
                pygame.mixer.music.load(self.musica_theme)
                self.musica_actual = self.musica_theme
            else:
                return 
            
            pygame.mixer.music.play(-1)
            self.volumen_inicial_transicion = 0.0
            self.volumen_final_transicion = self.volumen_objetivo
            self.tiempo_inicio_transicion = pygame.time.get_ticks()
            self.transicionando_musica = True
            pygame.mixer.music.set_volume(0.0)
        except Exception as e:
            print(f"Error al cambiar música: {e}")

    def manejar_transicion_musica(self):
        if not self.transicionando_musica:
            return
        
        ahora = pygame.time.get_ticks()
        tiempo_pasado = ahora - self.tiempo_inicio_transicion
        
        if tiempo_pasado >= self.tiempo_transicion:
            pygame.mixer.music.set_volume(self.volumen_final_transicion)
            self.transicionando_musica = False
        else:
            progreso = tiempo_pasado / self.tiempo_transicion
            volumen_actual = self.volumen_inicial_transicion + (self.volumen_final_transicion - self.volumen_inicial_transicion) * progreso
            pygame.mixer.music.set_volume(volumen_actual)

    def actualizar(self):
        self.todos_los_sprites.update()
        self.manejar_transicion_musica()

        if self.inmune:
            ahora = pygame.time.get_ticks()
            if ahora - self.tiempo_inmunidad_inicio > self.duracion_inmunidad:
                self.inmune = False

        nuevas_olas = self.jugador.generar_olas()
        if nuevas_olas:
            self.olas.add(nuevas_olas)
            self.todos_los_sprites.add(nuevas_olas)
        
        for enemigo in self.enemigos:
            bomba = enemigo.disparar()
            if bomba:
                self.bombas_enemigas.add(bomba)
                self.todos_los_sprites.add(bomba)

        colisiones_jugador_enemigo = pygame.sprite.groupcollide(self.disparos_jugador, self.enemigos, True, True)
        for disparo, enemigos_alcanzados in colisiones_jugador_enemigo.items():
            for enemigo in enemigos_alcanzados:
                if self.sonido_explosion:
                    self.sonido_explosion.play()
                self.puntuacion += 100 
                for _ in range(20): 
                    particula = Particula(enemigo.rect.centerx, enemigo.rect.centery)
                    self.particulas.add(particula)
                    self.todos_los_sprites.add(particula)

        if not self.inmune:
            colisiones_bomba_jugador = pygame.sprite.spritecollide(self.jugador, self.bombas_enemigas, True)
            if colisiones_bomba_jugador:
                if self.sonido_explosion:
                    self.sonido_explosion.play()
                self.vidas -= 1
                
                self.inmune = True
                self.tiempo_inmunidad_inicio = pygame.time.get_ticks()
                
                for _ in range(30):
                    particula = Particula(self.jugador.rect.centerx, self.jugador.rect.centery)
                    self.particulas.add(particula)
                    self.todos_los_sprites.add(particula)
                
                self.jugador.rect.centerx = self.ANCHO_JUEGO // 2
                self.jugador.rect.bottom = self.ALTO_JUEGO - 10
                if self.vidas <= 0:
                    self.jugando = False # <-- Esto detendrá el bucle 'ejecutar'

        puntos_para_nivel = self.nivel * 1500 
        if self.puntuacion >= puntos_para_nivel:
            self.nivel += 1
            if self.nivel > 3: 
                self.nivel = 3 
            
            nueva_cadencia = max(200, 1000 - (self.nivel * 200)) 
            pygame.time.set_timer(self.ADDENEMY, nueva_cadencia)

    def dibujar(self):
        # 1. Dibujar el fondo (directo a self.pantalla)
        fondo_idx = min(self.nivel - 1, len(self.fondos) - 1)
        self.pantalla.blit(self.fondos[fondo_idx], (0, 0))
        
        # --- Lógica de Parpadeo (Sin cambios, sigue siendo correcta) ---
        ahora = pygame.time.get_ticks()
        dibujar_jugador = True
        
        imagen_original = self.jugador.cambiar_aspecto(self.nivel) 

        if self.inmune:
            if (ahora - self.tiempo_inmunidad_inicio) % (2 * self.periodo_parpadeo) < self.periodo_parpadeo:
                self.jugador.image = pygame.Surface((1, 1), pygame.SRCALPHA)
                self.jugador.sombra = self.jugador.crear_sombra(self.jugador.image)
            else:
                self.jugador.image = imagen_original
                self.jugador.sombra = self.jugador.crear_sombra(self.jugador.image)
        
        # 2. Dibujar sombras (directo a self.pantalla)
        if hasattr(self.jugador, 'sombra'):
            sombra_pos_x = self.jugador.rect.x + self.jugador.sombra_offset[0]
            sombra_pos_y = self.jugador.rect.y + self.jugador.sombra_offset[1]
            self.pantalla.blit(self.jugador.sombra, (sombra_pos_x, sombra_pos_y))
        
        for enemigo in self.enemigos:
             sombra_pos_x = enemigo.rect.x + enemigo.sombra_offset[0]
             sombra_pos_y = enemigo.rect.y + enemigo.sombra_offset[1]
             self.pantalla.blit(enemigo.sombra, (sombra_pos_x, sombra_pos_y))

        for bomba in self.bombas_enemigas:
             sombra_pos_x = bomba.rect.x + bomba.sombra_offset[0]
             sombra_pos_y = bomba.rect.y + bomba.sombra_offset[1]
             self.pantalla.blit(bomba.sombra, (sombra_pos_x, sombra_pos_y))
        
        # 3. Dibujar todos los sprites (directo a self.pantalla)
        self.todos_los_sprites.draw(self.pantalla)
        
        # 4. Dibujar la UI (directo a self.pantalla)
        self.dibujar_texto(f"Puntuación: {self.puntuacion}", 36, 10, 10, self.font, centrar_x=False)
        self.dibujar_texto(f"Vidas: {self.vidas}", 36, self.ANCHO_JUEGO - 150, 10, self.font, centrar_x=False)
        self.dibujar_texto(f"Nivel: {self.nivel}", 36, self.ANCHO_JUEGO // 2, 10, self.font)

        # 5. Escalar y dibujar -> AHORA SOLO ACTUALIZAR
        pygame.display.flip()

    def eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.jugando = False
                self.quiere_reiniciar = False # Salir del bucle 'main'
            
            if evento.type == self.ADDENEMY:
                nuevo_enemigo = Enemigo(self.directorio_assets) 
                self.enemigos.add(nuevo_enemigo)
                self.todos_los_sprites.add(nuevo_enemigo)

            if evento.type == self.ALTERNAR_MUSICA:
                self.cambiar_musica()

            if evento.type == pygame.KEYDOWN:
                # Salir con ESC
                if evento.key == pygame.K_ESCAPE:
                    self.jugando = False
                    self.quiere_reiniciar = False # Salir del bucle 'main'
                    # No usar sys.exit()
                
                if evento.key == pygame.K_SPACE:
                    disparo = self.jugador.disparar()
                    if disparo:
                        if self.sonido_disparo:
                            self.sonido_disparo.play()
                        self.disparos_jugador.add(disparo)
                        self.todos_los_sprites.add(disparo)

    # --- FUNCIÓN DE DIBUJO DE TEXTO (Ahora dibuja a self.pantalla) ---
    def dibujar_texto(self, texto, tamano, x, y, fuente, centrar_x=True):
        superficie_texto = fuente.render(texto, True, COLOR_BLANCO)
        rect_texto = superficie_texto.get_rect()
        
        if centrar_x:
            rect_texto.centerx = x
        else:
            rect_texto.topleft = (x, y)
            
        rect_texto.top = y
        
        # Dibuja siempre a la pantalla principal
        self.pantalla.blit(superficie_texto, rect_texto)

    def cargar_highscores(self):
        try:
            # En la web, esto leerá desde el almacenamiento virtual
            with open(self.ruta_highscore, "r") as f:
                self.highscores = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, pygame.error):
            # pygame.error puede ocurrir si la ruta no es válida en web
            self.highscores = []

    def guardar_highscores(self):
        try:
            if self.puntuacion > 0:
                self.highscores.append({"nombre": self.nombre_jugador if self.nombre_jugador else "AAA", "puntuacion": self.puntuacion})
            
            self.highscores = sorted(self.highscores, key=lambda x: x["puntuacion"], reverse=True)[:10] 
            
            # En la web, esto escribirá en el almacenamiento virtual (se perderá al recargar)
            # Para persistencia real, se necesitaría 'pygbag.vfs.save'
            with open(self.ruta_highscore, "w") as f:
                json.dump(self.highscores, f, indent=4)
        except Exception as e:
            print(f"Error al guardar highscore (esperado en web si no se usa VFS): {e}")

    def pantalla_game_over(self):
        if self.sonido_explosion:
            self.sonido_explosion.set_volume(0)
        if self.sonido_disparo:
            self.sonido_disparo.set_volume(0)

        # Usar la música de 'score' o 'theme' como fallback
        musica_a_usar = self.musica_score if self.musica_score else self.musica_theme
        if musica_a_usar:
            try:
                pygame.mixer.music.load(musica_a_usar) 
                pygame.mixer.music.play(-1)
                pygame.mixer.music.set_volume(0.6)
            except pygame.error as e:
                print(f"Error al reproducir música de Game Over: {e}")

        font_grande = pygame.font.Font(None, 60)
        font_mediana = pygame.font.Font(None, 36)
        font_pequena = pygame.font.Font(None, 30)

        input_activo = True
        if self.puntuacion == 0 or (len(self.highscores) >= 10 and self.puntuacion < self.highscores[-1]["puntuacion"]):
             input_activo = False
             self.guardar_highscores() 

        game_over_loop = True
        while game_over_loop:
            # --- DIBUJAR (Directo a self.pantalla) ---
            self.pantalla.blit(self.fondos_score, (0, 0))
            
            self.dibujar_texto("GAME OVER", 60, self.ANCHO_JUEGO // 2, 50, font_grande)
            self.dibujar_texto(f"Tu Puntuación: {self.puntuacion}", 36, self.ANCHO_JUEGO // 2, 120, font_mediana)
            self.dibujar_texto("Highscores:", 36, self.ANCHO_JUEGO // 2, 180, font_mediana)
            
            y_offset = 220
            for i, score in enumerate(self.highscores):
                self.dibujar_texto(f"{i+1}. {score['nombre']}: {score['puntuacion']}", 30, self.ANCHO_JUEGO // 2, y_offset + i * 30, font_pequena)

            if input_activo:
                self.dibujar_texto("¡Nuevo Highscore! Ingresa tu nombre:", 30, self.ANCHO_JUEGO // 2, self.ALTO_JUEGO - 100, font_pequena)
                caja_rect = pygame.Rect(self.ANCHO_JUEGO // 2 - 100, self.ALTO_JUEGO - 60, 200, 32)
                pygame.draw.rect(self.pantalla, COLOR_BLANCO, caja_rect, 2) # <-- Dibujar a self.pantalla
                self.dibujar_texto(self.nombre_jugador, 30, caja_rect.centerx, caja_rect.y + 5, font_pequena, centrar_x=True)
            else:
                self.dibujar_texto("Presiona R para reiniciar o Q para salir", 30, self.ANCHO_JUEGO // 2, self.ALTO_JUEGO - 50, font_pequena)

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.quiere_reiniciar = False
                    game_over_loop = False
                    # No usar sys.exit()
                
                if input_activo:
                    if evento.type == pygame.KEYDOWN:
                        if evento.key == pygame.K_RETURN:
                            input_activo = False
                            self.guardar_highscores()
                        elif evento.key == pygame.K_BACKSPACE:
                            self.nombre_jugador = self.nombre_jugador[:-1]
                        elif len(self.nombre_jugador) < 10 and evento.unicode.isprintable(): # Asegurarse de que sea imprimible
                            self.nombre_jugador += evento.unicode
                else:
                    if evento.type == pygame.KEYDOWN:
                        if evento.key == pygame.K_r:
                            self.quiere_reiniciar = True # Indicar al bucle 'main' que reinicie
                            game_over_loop = False 
                        if evento.key == pygame.K_q:
                            self.quiere_reiniciar = False # Indicar al bucle 'main' que no reinicie
                            game_over_loop = False
                            # No usar sys.exit()
            
            # --- DIBUJAR A PANTALLA REAL (ESCALADO) ---
            pygame.display.flip() # <-- Reemplaza a dibujar_a_pantalla_real
            self.reloj.tick(FPS)
        
        # No reiniciar el juego aquí. Simplemente salir.
        # El bucle 'main' se encargará de la lógica de reinicio.


# --- Iniciar el juego (Nuevo bucle 'main' asíncrono) ---
async def main():
    while True:
        juego = Juego()
        await juego.ejecutar() # El juego se ejecuta hasta Game Over o ESC
        
        # Si el usuario presionó 'R' en Game Over, juego.quiere_reiniciar será True
        if not juego.quiere_reiniciar:
            break # Salir del bucle 'while True' y terminar

    print("Juego terminado. Saliendo.")
    pygame.quit()

if __name__ == "__main__":
    # Esta es la forma estándar de ejecutar un programa asyncio/pygbag
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Juego interrumpido por el usuario.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        # En un entorno web, es mejor solo registrar el error
        # que intentar un sys.exit()