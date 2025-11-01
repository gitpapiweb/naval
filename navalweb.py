# Papiweb desarrollos informaticos      
import io
import base64
import os
import json
import random
import sys
import pygame

# --- Constantes ---
# Estas son las dimensiones INTERNAS/VIRTUALES del juego
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
        
        # Efecto de desvanecimiento y encogimiento
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
        
        # Superficie inicial transparente
        self.image = pygame.Surface((self.radio * 2, self.radio * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color + (100,), (self.radio, self.radio), self.radio, 1)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.contador_vida += 1
        if self.contador_vida > self.vida_util:
            self.kill()
            return
        
        # Expansión del radio
        self.radio += self.velocidad_expansion
        
        # Cálculo de transparencia (alpha)
        alpha = max(0, 255 * (1 - (self.contador_vida / self.vida_util)))
        centro_actual = self.rect.center
        
        # Redibujar la ola con el nuevo radio y alpha
        self.image = pygame.Surface((int(self.radio * 2), int(self.radio * 2)), pygame.SRCALPHA)
        color_actual = self.color + (int(alpha),)
        pygame.draw.circle(self.image, color_actual, (int(self.radio), int(self.radio)), int(self.radio), 1)
        self.rect = self.image.get_rect(center=centro_actual)

# --- Clase para el Jugador (Barco) ---
class Jugador(pygame.sprite.Sprite):
    def __init__(self, ruta_assets):
        super().__init__()
        
        self.imagenes_barco = []
        # Guardar una referencia a la imagen original por nivel para el parpadeo
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
            self.imagen_original_por_nivel[3] = img2 # Asumiendo nivel 3 usa barco2
            
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
        """Crea una superficie de sombra semitransparente para una imagen."""
        sombra = imagen.copy()
        sombra.fill((0, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
        sombra.set_alpha(100) 
        return sombra

    def cambiar_aspecto(self, nivel):
        """Cambia la imagen del barco Y su sombra según el nivel."""
        self.nivel_actual = nivel
        
        # Usar la imagen original del nivel actual
        img_a_usar = self.imagen_original_por_nivel.get(nivel, self.imagen_original_por_nivel[1])
        
        # Solo actualiza si la imagen ha cambiado, o si la imagen actual es la superficie transparente
        if self.image is not img_a_usar or self.image.get_width() == 1:
            self.image = img_a_usar
            
            pos_actual = self.rect.center
            self.rect = self.image.get_rect(center=pos_actual)
            self.sombra = self.crear_sombra(self.image)
            
        return self.image # Devolver la imagen para usarla en el parpadeo

    def generar_olas(self):
        ahora = pygame.time.get_ticks()
        # Generar olas solo si el barco se está moviendo
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
        # Limitar movimiento dentro de la pantalla
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
        # Las bombas se matan al colisionar con el jugador o al salir de la pantalla
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
        """Define la posición inicial aleatoria de aparición."""
        self.rect.x = random.randint(0, ANCHO_PANTALLA - self.rect.width)
        self.rect.y = random.randint(-100, -40)

    def configurar_movimiento(self):
        """Define el tipo de enemigo y sus parámetros de movimiento."""
        self.tipo_enemigo = random.randint(1, 3)
        # Asegurarse de que el índice no exceda la lista
        idx = min(self.tipo_enemigo - 1, len(self.imagenes_avion) - 1)
        self.image = self.imagenes_avion[idx]
        
        # Reajustar el rect después de cambiar la imagen (si su tamaño cambió)
        pos_actual = self.rect.center
        self.rect = self.image.get_rect(center=pos_actual) 
        self.sombra = self.crear_sombra(self.image)
        self.sombra_offset = (4, 4)
        
        # Parámetros por Tipo de Enemigo
        if self.tipo_enemigo == 1: # Movimiento de Onda
            self.amplitud_onda = random.randint(50, 150)
            self.frecuencia_onda = random.uniform(0.01, 0.03)
            self.centro_x = self.rect.centerx
            self.angulo = 0
            self.velocidad_y = random.randint(2, 4)
            self.cadencia_disparo = 60 
            self.tipo_bomba = 1
        elif self.tipo_enemigo == 2: # Movimiento Rápido
            self.velocidad_y = random.randint(4, 6)
            self.cadencia_disparo = 45 
            self.tipo_bomba = 2
        elif self.tipo_enemigo == 3: # Movimiento Zigzag
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
        """Lo mueve a una nueva posición superior y re-randomiza sus parámetros."""
        self.configurar_posicion_inicial()
        self.configurar_movimiento()

    def update(self):
        
        if self.estado_vuelo == "descenso":
            
            self.rect.y += self.velocidad_y
            
            # Lógica de movimiento por tipo
            if self.tipo_enemigo == 1:
                self.angulo += self.frecuencia_onda
                # Cálculo de onda sinusoidal
                offset_x = self.amplitud_onda * pygame.math.Vector2(1, 0).rotate(self.angulo * 180 / 3.14159).y
                self.rect.centerx = self.centro_x + offset_x
            elif self.tipo_enemigo == 3: 
                self.contador_zigzag += 1
                if self.contador_zigzag >= self.cambio_zigzag_timer:
                    self.velocidad_x_zigzag *= -1 
                    self.contador_zigzag = 0
                    self.cambio_zigzag_timer = random.randint(30, 90)
                self.rect.x += self.velocidad_x_zigzag
                # Evitar que se salga por el lateral durante el zigzag
                if self.rect.left < 0 or self.rect.right > ANCHO_PANTALLA:
                    self.velocidad_x_zigzag *= -1
                    self.rect.x += self.velocidad_x_zigzag 
            
            # --- TRANSICIÓN A ESTADO DE SALIDA ---
            if self.rect.top > ALTO_PANTALLA:
                self.estado_vuelo = "salida"
                # Velocidad de salida rápida hacia un lado aleatorio
                self.velocidad_x_salida = random.choice([-10, 10]) 
                self.velocidad_y = 0 
                
        elif self.estado_vuelo == "salida":
            # Mover horizontalmente
            self.rect.x += self.velocidad_x_salida
            
            # --- LÓGICA DE REAPARICIÓN ---
            # Si el enemigo ha salido completamente por un lateral
            if self.rect.right < 0 or self.rect.left > ANCHO_PANTALLA:
                self.resetear_enemigo()
                
    def disparar(self):
        # Solo disparar en estado de descenso
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
        
        # --- Configuración de Resolución y Escalado (FullScreen) ---
        # 1. Configurar pantalla REAL (se adapta al monitor)
        self.pantalla = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.ancho_real = self.pantalla.get_width()
        self.alto_real = self.pantalla.get_height()
        
        # 2. Superficie de juego VIRTUAL (donde se dibuja el juego 800x600)
        self.superficie_juego = pygame.Surface((ANCHO_PANTALLA, ALTO_PANTALLA))
        self.ANCHO_JUEGO = ANCHO_PANTALLA
        self.ALTO_JUEGO = ALTO_PANTALLA

        pygame.display.set_caption("Defensor Naval - por Papiweb desarrollos informaticos")
        
        self.reloj = pygame.time.Clock()
        
        # --- Configuración de Rutas de Assets ---
        self.directorio_juego = os.path.dirname(os.path.abspath(__file__))
        self.directorio_assets = os.path.join(self.directorio_juego, "assets")

        # --- Cargar Audio ---
        try:
            self.sonido_explosion = pygame.mixer.Sound(os.path.join(self.directorio_assets, "fall.ogg"))
            self.sonido_disparo = pygame.mixer.Sound(os.path.join(self.directorio_assets, "gun.ogg"))
            
            self.musica_presentacion = os.path.join(self.directorio_assets, "epic.ogg")
            self.musica_theme = os.path.join(self.directorio_assets, "theme.ogg")
            self.musica_dance = os.path.join(self.directorio_assets, "dance.ogg")
            self.musica_score = os.path.join(self.directorio_assets, "score.ogg")
            
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

        # Variables para la transición de música
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

        # Sistema de puntuación y niveles
        self.puntuacion = 0
        self.vidas = 3
        self.nivel = 1
        self.font = pygame.font.Font(None, 36)
        self.font_marca = pygame.font.Font(None, 24)

        # Variables de Inmunidad (NUEVAS)
        self.inmune = False
        self.tiempo_inmunidad_inicio = 0
        self.duracion_inmunidad = 3000 # 3 segundos
        self.periodo_parpadeo = 100 # Cambia de estado (visible/oculto) cada 100ms

        # Sistema de Highscore
        self.highscores = []
        self.nombre_jugador = ""
        self.ruta_highscore = os.path.join(self.directorio_juego, "highscores.json")
        self.cargar_highscores()

        # Grupos de Sprites
        self.todos_los_sprites = pygame.sprite.LayeredUpdates()
        self.particulas = pygame.sprite.Group()
        self.olas = pygame.sprite.Group()
        self.enemigos = pygame.sprite.Group()
        self.bombas_enemigas = pygame.sprite.Group()
        self.disparos_jugador = pygame.sprite.Group()
        
        # Inicialización del Jugador
        self.jugador = Jugador(self.directorio_assets)
        self.jugador._layer = 3
        self.todos_los_sprites.add(self.jugador)
        
        # Evento para generar enemigos
        self.ADDENEMY = pygame.USEREVENT + 1
        pygame.time.set_timer(self.ADDENEMY, 1000) 
        self.jugando = True

    def calcular_escala(self):
        """Calcula el factor de escala y la posición para centrar el juego."""
        # Calcula el factor de escala que maximiza el tamaño manteniendo la proporción (800/600 = 4/3)
        escala_x = self.ancho_real / self.ANCHO_JUEGO
        escala_y = self.alto_real / self.ALTO_JUEGO
        
        self.escala = min(escala_x, escala_y)
        
        self.ancho_escalado = int(self.ANCHO_JUEGO * self.escala)
        self.alto_escalado = int(self.ALTO_JUEGO * self.escala)
        
        self.posicion_x = (self.ancho_real - self.ancho_escalado) // 2
        self.posicion_y = (self.alto_real - self.alto_escalado) // 2
        
        return self.ancho_escalado, self.alto_escalado, self.posicion_x, self.posicion_y

    def dibujar_a_pantalla_real(self):
        """Escala la superficie virtual del juego a la pantalla real."""
        ancho_e, alto_e, pos_x, pos_y = self.calcular_escala()
        
        # Primero, borra la pantalla real para crear las barras negras
        self.pantalla.fill((0, 0, 0)) 
        
        superficie_escalada = pygame.transform.scale(self.superficie_juego, (ancho_e, alto_e))
        self.pantalla.blit(superficie_escalada, (pos_x, pos_y))
        
        pygame.display.flip()

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
                    pygame.quit()
                    sys.exit()
                if evento.type == pygame.KEYDOWN or evento.type == pygame.MOUSEBUTTONDOWN:
                    presentacion_activa = False

            # --- DIBUJAR A SUPERFICIE VIRTUAL ---
            self.superficie_juego.blit(self.fondo_presentacion, (0, 0))
            
            ahora = pygame.time.get_ticks()
            if ahora - ultimo_cambio > duracion_imagen and self.imagenes_adelanto:
                indice_imagen = (indice_imagen + 1) % len(self.imagenes_adelanto)
                ultimo_cambio = ahora

            if self.imagenes_adelanto:
                imagen_actual = self.imagenes_adelanto[indice_imagen]
                rect_imagen = imagen_actual.get_rect(center=(self.ANCHO_JUEGO // 2, self.ALTO_JUEGO // 2))
                self.superficie_juego.blit(imagen_actual, rect_imagen)

            self.dibujar_texto("Defensor Naval", 60, self.ANCHO_JUEGO // 2, 50, self.font)
            self.dibujar_texto("Presiona cualquier tecla para comenzar", 30, self.ANCHO_JUEGO // 2, self.ALTO_JUEGO - 100, self.font)
            
            texto_marca = "Un juego de: Papiweb desarrollos informaticos"
            self.dibujar_texto(texto_marca, 24, self.ANCHO_JUEGO // 2, self.ALTO_JUEGO - 50, self.font_marca)

            # --- DIBUJAR A PANTALLA REAL (ESCALADO) ---
            self.dibujar_a_pantalla_real()
            self.reloj.tick(FPS)

        pygame.mixer.music.stop()
        if self.musica_theme:
            try:
                pygame.mixer.music.load(self.musica_theme)
                pygame.mixer.music.play(-1)
                pygame.mixer.music.set_volume(self.volumen_objetivo)
            except pygame.error as e:
                print(f"Error al reproducir música de tema: {e}")

    def ejecutar(self):
        self.pantalla_presentacion()
        while self.jugando:
            self.reloj.tick(FPS)
            self.eventos() 
            self.actualizar() 
            self.dibujar()    
        
        self.pantalla_game_over()

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

        # --- Lógica de Inmunidad ---
        if self.inmune:
            ahora = pygame.time.get_ticks()
            if ahora - self.tiempo_inmunidad_inicio > self.duracion_inmunidad:
                self.inmune = False

        # Generar olas del jugador
        nuevas_olas = self.jugador.generar_olas()
        if nuevas_olas:
            self.olas.add(nuevas_olas)
            self.todos_los_sprites.add(nuevas_olas)
        
        # Disparo enemigo (solo si está en descenso)
        for enemigo in self.enemigos:
            bomba = enemigo.disparar()
            if bomba:
                self.bombas_enemigas.add(bomba)
                self.todos_los_sprites.add(bomba)

        # Colisiones: Disparos del Jugador vs Enemigos
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

        # Colisiones: Bombas Enemigas vs Jugador (Solo si NO es inmune)
        if not self.inmune:
            colisiones_bomba_jugador = pygame.sprite.spritecollide(self.jugador, self.bombas_enemigas, True)
            if colisiones_bomba_jugador:
                if self.sonido_explosion:
                    self.sonido_explosion.play()
                self.vidas -= 1
                
                # Activar inmunidad
                self.inmune = True
                self.tiempo_inmunidad_inicio = pygame.time.get_ticks()
                
                for _ in range(30):
                    particula = Particula(self.jugador.rect.centerx, self.jugador.rect.centery)
                    self.particulas.add(particula)
                    self.todos_los_sprites.add(particula)
                
                # Reposicionar jugador
                self.jugador.rect.centerx = self.ANCHO_JUEGO // 2
                self.jugador.rect.bottom = self.ALTO_JUEGO - 10
                if self.vidas <= 0:
                    self.jugando = False 

        # Control de Niveles
        puntos_para_nivel = self.nivel * 1500 
        if self.puntuacion >= puntos_para_nivel:
            self.nivel += 1
            if self.nivel > 3: 
                self.nivel = 3 
            
            # Aumentar la cadencia de aparición de enemigos
            nueva_cadencia = max(200, 1000 - (self.nivel * 200)) 
            pygame.time.set_timer(self.ADDENEMY, nueva_cadencia)
            # El parpadeo necesita llamar a cambiar_aspecto, lo dejamos para dibujar()

    def dibujar(self):
        # 1. Dibujar el fondo a la superficie virtual
        fondo_idx = min(self.nivel - 1, len(self.fondos) - 1)
        self.superficie_juego.blit(self.fondos[fondo_idx], (0, 0))
        
        # --- Lógica de Parpadeo (Control de imagen del jugador) ---
        ahora = pygame.time.get_ticks()
        dibujar_jugador = True
        
        # Primero, asegurar que el jugador tiene su imagen correcta para el nivel
        imagen_original = self.jugador.cambiar_aspecto(self.nivel) 

        if self.inmune:
            # Si el tiempo transcurrido está en la fase 'off' del parpadeo, lo ocultamos.
            # (ahora - inicio) / periodo -> determina el ciclo. Si es par/impar, lo mostramos/ocultamos.
            if (ahora - self.tiempo_inmunidad_inicio) % (2 * self.periodo_parpadeo) < self.periodo_parpadeo:
                # Ocultar: usar una superficie transparente (1x1)
                self.jugador.image = pygame.Surface((1, 1), pygame.SRCALPHA)
                self.jugador.sombra = self.jugador.crear_sombra(self.jugador.image)
            else:
                # Mostrar: ya restauramos la imagen original con cambiar_aspecto() arriba
                self.jugador.image = imagen_original
                self.jugador.sombra = self.jugador.crear_sombra(self.jugador.image)
        else:
             # Si no es inmune, la imagen ya está correctamente restaurada por cambiar_aspecto()
             pass
        
        # 2. Dibujar sombras a la superficie virtual (Ahora todas las sombras se manejan aquí)
        
        # Sombra del Jugador
        if hasattr(self.jugador, 'sombra'):
            sombra_pos_x = self.jugador.rect.x + self.jugador.sombra_offset[0]
            sombra_pos_y = self.jugador.rect.y + self.jugador.sombra_offset[1]
            # Si el jugador está oculto, su sombra será la superficie 1x1, lo que lo oculta eficientemente.
            self.superficie_juego.blit(self.jugador.sombra, (sombra_pos_x, sombra_pos_y))
        
        # Sombras de Enemigos y Bombas
        for enemigo in self.enemigos:
             sombra_pos_x = enemigo.rect.x + enemigo.sombra_offset[0]
             sombra_pos_y = enemigo.rect.y + enemigo.sombra_offset[1]
             self.superficie_juego.blit(enemigo.sombra, (sombra_pos_x, sombra_pos_y))

        for bomba in self.bombas_enemigas:
             sombra_pos_x = bomba.rect.x + bomba.sombra_offset[0]
             sombra_pos_y = bomba.rect.y + bomba.sombra_offset[1]
             self.superficie_juego.blit(bomba.sombra, (sombra_pos_x, sombra_pos_y))
        
        # 3. Dibujar todos los sprites a la superficie virtual
        # self.todos_los_sprites.draw dibujará el Jugador con la imagen (visible o invisible).
        self.todos_los_sprites.draw(self.superficie_juego)
        
        # 4. Dibujar la UI a la superficie virtual
        self.dibujar_texto(f"Puntuación: {self.puntuacion}", 36, 10, 10, self.font, centrar_x=False) # Puntuación esquina superior izquierda
        self.dibujar_texto(f"Vidas: {self.vidas}", 36, self.ANCHO_JUEGO - 150, 10, self.font, centrar_x=False) # Vidas esquina superior derecha
        self.dibujar_texto(f"Nivel: {self.nivel}", 36, self.ANCHO_JUEGO // 2, 10, self.font) # Nivel centrado

        # 5. Escalar y dibujar la superficie virtual a la pantalla real
        self.dibujar_a_pantalla_real()

    def eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.jugando = False
            
            if evento.type == self.ADDENEMY:
                # El juego crea un nuevo enemigo
                nuevo_enemigo = Enemigo(self.directorio_assets) 
                self.enemigos.add(nuevo_enemigo)
                self.todos_los_sprites.add(nuevo_enemigo)

            if evento.type == self.ALTERNAR_MUSICA:
                self.cambiar_musica()

            if evento.type == pygame.KEYDOWN:
                # Salir con ESC
                if evento.key == pygame.K_ESCAPE:
                    self.jugando = False
                    pygame.quit()
                    sys.exit()
                # El jugador dispara al presionar espacio
                if evento.key == pygame.K_SPACE:
                    disparo = self.jugador.disparar()
                    if disparo:
                        if self.sonido_disparo:
                            self.sonido_disparo.play()
                        self.disparos_jugador.add(disparo)
                        self.todos_los_sprites.add(disparo)

    # --- FUNCIÓN DE DIBUJO DE TEXTO ---
    def dibujar_texto(self, texto, tamano, x, y, fuente, centrar_x=True):
        superficie_texto = fuente.render(texto, True, COLOR_BLANCO)
        rect_texto = superficie_texto.get_rect()
        
        if centrar_x:
            rect_texto.centerx = x
        else:
            # Si no está centrado, 'x' es la coordenada izquierda superior
            rect_texto.topleft = (x, y)
            
        rect_texto.top = y
        
        # Dibuja siempre a la superficie virtual del juego
        self.superficie_juego.blit(superficie_texto, rect_texto)

    def cargar_highscores(self):
        try:
            with open(self.ruta_highscore, "r") as f:
                self.highscores = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.highscores = []

    def guardar_highscores(self):
        if self.puntuacion > 0:
            self.highscores.append({"nombre": self.nombre_jugador if self.nombre_jugador else "AAA", "puntuacion": self.puntuacion})
        
        self.highscores = sorted(self.highscores, key=lambda x: x["puntuacion"], reverse=True)[:10] 
        with open(self.ruta_highscore, "w") as f:
            json.dump(self.highscores, f, indent=4)

    def pantalla_game_over(self):
        
        # 1. Silenciar sonidos de juego
        if self.sonido_explosion:
            self.sonido_explosion.set_volume(0)
        if self.sonido_disparo:
            self.sonido_disparo.set_volume(0)

        # 2. Cargar y reproducir theme.ogg
        if self.musica_theme:
            try:
                pygame.mixer.music.load(self.musica_theme) 
                pygame.mixer.music.play(-1)
                pygame.mixer.music.set_volume(0.6)
            except pygame.error as e:
                print(f"Error al reproducir música de Game Over (theme.ogg): {e}")

        font_grande = pygame.font.Font(None, 60)
        font_mediana = pygame.font.Font(None, 36)
        font_pequena = pygame.font.Font(None, 30)

        # Determinar si el puntaje califica para el highscore
        input_activo = True
        if self.puntuacion == 0 or (len(self.highscores) >= 10 and self.puntuacion < self.highscores[-1]["puntuacion"]):
             input_activo = False
             self.guardar_highscores() 

        game_over_loop = True
        while game_over_loop:
            # --- DIBUJAR A SUPERFICIE VIRTUAL ---
            self.superficie_juego.blit(self.fondos_score, (0, 0))
            
            # Título y textos centrados usando ANCHO_PANTALLA // 2
            self.dibujar_texto("GAME OVER", 60, self.ANCHO_JUEGO // 2, 50, font_grande)
            self.dibujar_texto(f"Tu Puntuación: {self.puntuacion}", 36, self.ANCHO_JUEGO // 2, 120, font_mediana)
            self.dibujar_texto("Highscores:", 36, self.ANCHO_JUEGO // 2, 180, font_mediana)
            
            y_offset = 220
            for i, score in enumerate(self.highscores):
                # Highscores list centrada
                self.dibujar_texto(f"{i+1}. {score['nombre']}: {score['puntuacion']}", 30, self.ANCHO_JUEGO // 2, y_offset + i * 30, font_pequena)

            if input_activo:
                # Prompt de ingreso de nombre centrado
                self.dibujar_texto("¡Nuevo Highscore! Ingresa tu nombre:", 30, self.ANCHO_JUEGO // 2, self.ALTO_JUEGO - 100, font_pequena)
                caja_rect = pygame.Rect(self.ANCHO_JUEGO // 2 - 100, self.ALTO_JUEGO - 60, 200, 32)
                pygame.draw.rect(self.superficie_juego, COLOR_BLANCO, caja_rect, 2)
                
                # CORRECCIÓN: Centrar el texto en lugar de usar offset a la izquierda
                self.dibujar_texto(self.nombre_jugador, 30, caja_rect.centerx, caja_rect.y + 5, font_pequena, centrar_x=True)
            else:
                # Mensaje de Reinicio/Salida centrado
                self.dibujar_texto("Presiona R para reiniciar o Q para salir", 30, self.ANCHO_JUEGO // 2, self.ALTO_JUEGO - 50, font_pequena)

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if input_activo:
                    if evento.type == pygame.KEYDOWN:
                        if evento.key == pygame.K_RETURN:
                            input_activo = False
                            self.guardar_highscores()
                        elif evento.key == pygame.K_BACKSPACE:
                            self.nombre_jugador = self.nombre_jugador[:-1]
                        elif len(self.nombre_jugador) < 10: 
                            self.nombre_jugador += evento.unicode
                else:
                    if evento.type == pygame.KEYDOWN:
                        if evento.key == pygame.K_r:
                            game_over_loop = False 
                        if evento.key == pygame.K_q:
                            pygame.quit()
                            sys.exit()
            
            # --- DIBUJAR A PANTALLA REAL (ESCALADO) ---
            self.dibujar_a_pantalla_real()
            self.reloj.tick(FPS)
        
        # Reiniciar el juego (crea una nueva instancia y la ejecuta)
        juego = Juego()
        juego.ejecutar()

# --- Iniciar el juego ---
if __name__ == "__main__":
    juego = Juego()
    juego.ejecutar()