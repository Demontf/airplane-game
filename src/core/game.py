import pygame
import os
import math
from enum import Enum
from .sprites import Player, Enemy, Bullet, Background
from .network import NetworkManager
from .ui import Menu
from .audio import AudioManager
from .animation import AnimationManager
from .performance import PerformanceManager
from .effects import ParticleEmitter, Explosion

class GameState(Enum):
    START = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4

class Game:
    def __init__(self, config):
        self.config = config
        
        # Initialize display
        self.width = config.getint('GAME', 'SCREEN_WIDTH')
        self.height = config.getint('GAME', 'SCREEN_HEIGHT')
        display_flags = pygame.HWSURFACE | pygame.DOUBLEBUF
        if config.getboolean('GAME', 'ENABLE_VSYNC', fallback=True):
            display_flags |= pygame.SCALED
        self.screen = pygame.display.set_mode((self.width, self.height), display_flags)
        pygame.display.set_caption(config.get('GAME', 'TITLE'))
        
        # Initialize managers
        self.audio = AudioManager(config)
        self.animation = AnimationManager()
        self.performance = PerformanceManager(config)
        self.menu = Menu(self.width, self.height)
        
        # Initialize clock
        self.clock = pygame.time.Clock()
        self.fps = config.getint('GAME', 'FPS')
        
        # Initialize game state
        self.state = GameState.START
        self.score = 0
        
        # Initialize sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.players = pygame.sprite.Group()
        self.remote_players = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.backgrounds = pygame.sprite.Group()
        self.effects = pygame.sprite.Group()
        
        # Initialize effects
        self.particle_emitter = ParticleEmitter()
        
        # Initialize multiplayer
        self.is_multiplayer = config.getint('NETWORK', 'ROLE') in [1, 2]
        self.network = NetworkManager(config, self) if self.is_multiplayer else None
        self.player_id = None
        self.remote_player_sprites = {}  # {player_id: sprite}
        
        # Load assets
        self.load_assets()
        
        # Create initial sprites
        self.create_sprites()
        
        # Start menu music
        self.audio.play_music('menu')

    def load_assets(self):
        """Load all game assets"""
        # Load images
        self.images = {
            'background': pygame.image.load('src/assets/images/bg.png').convert(),
            'player': pygame.image.load('src/assets/images/hero1.png').convert_alpha(),
            'player2': pygame.image.load('src/assets/images/hero2.png').convert_alpha(),
            'enemy_red': pygame.image.load('src/assets/images/enemy01.png').convert_alpha(),
            'enemy_yellow': pygame.image.load('src/assets/images/enemy02.png').convert_alpha(),
            'enemy_blue': pygame.image.load('src/assets/images/enemy03.png').convert_alpha(),
            'bullet': pygame.image.load('src/assets/images/b2.png').convert_alpha(),
            'missile': pygame.image.load('src/assets/images/b.png').convert_alpha(),
            'enemy_bullet': pygame.image.load('src/assets/images/b3.png').convert_alpha(),
            'explosion': pygame.image.load('src/assets/images/effer.png').convert_alpha(),
            'gameover': pygame.image.load('src/assets/images/gameover.png').convert_alpha(),
        }
        
        # Load sounds
        try:
            if os.path.exists('src/assets/sounds/bgmusic.mp3'):
                pygame.mixer.music.load('src/assets/sounds/bgmusic.mp3')
            else:
                print("Warning: Background music file not found")
        except pygame.error as e:
            print(f"Warning: Could not load background music: {e}")
            
        try:
            self.sounds = {
                'explosion': pygame.mixer.Sound('src/assets/sounds/baozha.ogg'),
            }
        except pygame.error as e:
            print(f"Warning: Could not load sound effects: {e}")
            self.sounds = {}

    def create_sprites(self):
        """Create initial game sprites"""
        # Create background
        Background(self.images['background'], [self.backgrounds, self.all_sprites])
        
        # Create player
        Player(
            self.images['player'],
            self.config.getint('PLAYER', 'SPEED'),
            self.config.getint('PLAYER', 'INITIAL_LIVES'),
            [self.players, self.all_sprites]
        )

    def handle_events(self):
        """Handle all game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            # Handle menu events
            if self.state in [GameState.START, GameState.PAUSED, GameState.GAME_OVER]:
                menu_type = 'main' if self.state == GameState.START else self.state.name.lower()
                action = self.menu.handle_event(event, menu_type)
                if action:
                    if action == 'single_player':
                        self.state = GameState.PLAYING
                        self.audio.play_music('game')
                    elif action == 'multiplayer':
                        # TODO: Implement multiplayer
                        pass
                    elif action == 'resume':
                        self.state = GameState.PLAYING
                        self.audio.unpause_music()
                    elif action == 'main_menu':
                        self.state = GameState.START
                        self.audio.play_music('menu')
                    elif action == 'retry':
                        self.state = GameState.PLAYING
                        self.score = 0
                        self.all_sprites.empty()
                        self.players.empty()
                        self.enemies.empty()
                        self.bullets.empty()
                        self.backgrounds.empty()
                        self.create_sprites()
                        self.audio.play_music('game')
                    elif action == 'quit':
                        return False
            
            # Handle game controls
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.PAUSED
                        self.audio.pause_music()
                    elif self.state == GameState.PAUSED:
                        self.state = GameState.PLAYING
                        self.audio.unpause_music()
                elif event.key == pygame.K_m:
                    self.audio.toggle_sound()
                elif event.key == pygame.K_RETURN and self.state == GameState.START:
                    self.state = GameState.PLAYING
                    self.audio.play_music('game')
        
        # Handle continuous shooting
        if self.state == GameState.PLAYING and self.players.sprite:
            self.players.sprite.shoot([self.bullets, self.all_sprites], self.network)
        
        return True

    def update(self):
        """Update game state"""
        # Start performance monitoring
        self.performance.start_frame()
        
        if self.state == GameState.PLAYING:
            # Update all sprites
            self.all_sprites.update()
            
            # Handle collisions
            self.handle_collisions()
            
            # Spawn enemies (only host spawns enemies in multiplayer)
            if not self.is_multiplayer or (self.is_multiplayer and self.config.getint('NETWORK', 'ROLE') == 1):
                self.spawn_enemies()
            
            # Update network
            if self.network and self.players.sprite:
                self.network.send_player_update(
                    self.players.sprite.position,
                    self.players.sprite.velocity
                )
                self.network.update()
        
        # End performance monitoring
        self.performance.end_frame()

    def draw(self):
        """Draw everything to the screen"""
        self.screen.fill((0, 0, 0))
        
        # Draw game state
        if self.state == GameState.START:
            # Draw background
            self.backgrounds.draw(self.screen)
            # Draw menu
            self.menu.draw(self.screen, 'main')
            
        elif self.state == GameState.PLAYING:
            # Draw game world
            self.backgrounds.draw(self.screen)
            self.all_sprites.draw(self.screen)
            self.effects.draw(self.screen)
            
            # Draw player effects
            for sprite in self.players:
                # Draw engine glow
                glow_surf = pygame.Surface((sprite.rect.width + 10, sprite.rect.height + 10), pygame.SRCALPHA)
                glow_surf.blit(sprite.image, (5, 5))
                glow_surf = pygame.transform.gaussian_blur(glow_surf, 3)
                self.screen.blit(glow_surf, (sprite.rect.x - 5, sprite.rect.y - 5))
                
                # Draw shield effect if invincible
                if sprite.is_invincible:
                    shield_anim = self.animation.get_animation('shield', (64, 64))
                    shield_frame = shield_anim.update(1/60)
                    shield_rect = shield_frame.get_rect(center=sprite.rect.center)
                    self.screen.blit(shield_frame, shield_rect)
            
            # Draw HUD
            self.draw_hud()
            
        elif self.state == GameState.PAUSED:
            # Draw game world (dimmed)
            self.backgrounds.draw(self.screen)
            self.all_sprites.draw(self.screen)
            self.effects.draw(self.screen)
            
            # Draw pause menu
            self.menu.draw(self.screen, 'pause')
            
        elif self.state == GameState.GAME_OVER:
            # Draw game over menu
            self.menu.draw(self.screen, 'game_over', score=self.score)
            
        # Draw performance stats if enabled
        if self.config.getboolean('GAME', 'SHOW_PERFORMANCE', fallback=True):
            self.draw_performance_stats()
            
        pygame.display.flip()

    def draw_hud(self):
        """Draw heads-up display"""
        # Create HUD surface with transparency
        hud_surface = pygame.Surface((self.width, 100), pygame.SRCALPHA)
        pygame.draw.rect(hud_surface, (0, 0, 0, 128), (0, 0, self.width, 100))
        
        font = pygame.font.Font(None, 36)
        y = 20
        
        # Draw score
        score_text = font.render(f'Score: {self.score}', True, (255, 255, 255))
        score_rect = score_text.get_rect(topleft=(20, y))
        hud_surface.blit(score_text, score_rect)
        
        # Draw lives with icons
        lives_text = font.render('Lives:', True, (255, 255, 255))
        lives_rect = lives_text.get_rect(topright=(self.width - 180, y))
        hud_surface.blit(lives_text, lives_rect)
        
        life_icon = pygame.transform.scale(self.images['player'], (20, 20))
        for i in range(self.players.sprite.lives):
            hud_surface.blit(life_icon, (self.width - 160 + i * 30, y))
        
        # Draw missile status
        if hasattr(self.players.sprite, 'missile_unlocked') and self.players.sprite.missile_unlocked:
            missile_text = font.render('Missiles: Ready', True, (0, 255, 0))
        else:
            progress = self.score / self.config.getint('PLAYER', 'MISSILE_UNLOCK_SCORE')
            missile_text = font.render(f'Missiles: {int(progress * 100)}%', True, (255, 165, 0))
        missile_rect = missile_text.get_rect(topright=(self.width - 20, y + 30))
        hud_surface.blit(missile_text, missile_rect)
        
        # Draw the HUD surface
        self.screen.blit(hud_surface, (0, 0))
        
    def draw_performance_stats(self):
        """Draw performance statistics"""
        stats = self.performance.get_stats()
        font = pygame.font.Font(None, 24)
        y = self.height - 100
        
        for key, value in stats.items():
            text = font.render(f'{key}: {value}', True, (200, 200, 200))
            self.screen.blit(text, (10, y))
            y += 20

    def handle_collisions(self):
        """Handle all game collisions"""
        # Player bullets hitting enemies
        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True)
        for hit in hits:
            self.score += 100
            if 'explosion' in self.sounds:
                self.sounds['explosion'].play()
            # Create explosion effect
            Explosion(hit.rect.center, [self.effects, self.all_sprites])
            # Add particle effects
            self.particle_emitter.emit(
                hit.rect.center,
                (255, 165, 0),  # Orange color
                num_particles=20,
                speed=8,
                lifetime=0.5
            )
        
        # Enemies hitting player
        hits = pygame.sprite.spritecollide(self.players.sprite, self.enemies, True)
        if hits and not self.players.sprite.is_invincible:
            self.players.sprite.take_damage()
            if 'explosion' in self.sounds:
                self.sounds['explosion'].play()
            # Create explosion effect
            for hit in hits:
                Explosion(hit.rect.center, [self.effects, self.all_sprites])
                # Add particle effects
                self.particle_emitter.emit(
                    hit.rect.center,
                    (255, 0, 0),  # Red color
                    num_particles=30,
                    speed=10,
                    lifetime=0.8
                )
            if self.players.sprite.lives <= 0:
                self.state = GameState.GAME_OVER

    def spawn_enemies(self):
        """Spawn new enemies"""
        if len(self.enemies) < self.config.getint('ENEMY', 'MAX_ENEMIES'):
            import random
            
            # Randomly choose enemy type
            enemy_type = random.choice(['red', 'yellow', 'blue'])
            
            if enemy_type == 'red':
                image = self.images['enemy_red']
                speed = self.config.getint('ENEMY', 'RED_SPEED')
            elif enemy_type == 'yellow':
                image = self.images['enemy_yellow']
                speed = self.config.getint('ENEMY', 'YELLOW_SPEED')
            else:  # blue
                image = self.images['enemy_blue']
                speed = self.config.getint('ENEMY', 'BLUE_SPEED')
            
            Enemy(image, enemy_type, speed, [self.enemies, self.all_sprites])

    def handle_player_joined(self, data):
        """Handle when a new player joins the game"""
        self.player_id = data['player_id']
        
        # Create remote player sprite if it's not us
        if self.player_id != data['player_id']:
            remote_player = Player(
                self.images['player2'],  # Use different sprite for remote player
                self.config.getint('PLAYER', 'SPEED'),
                self.config.getint('PLAYER', 'INITIAL_LIVES'),
                [self.remote_players, self.all_sprites]
            )
            self.remote_player_sprites[data['player_id']] = remote_player
            
    def update_remote_player(self, player_id, position, velocity):
        """Update remote player position and velocity"""
        if player_id != self.player_id:
            if player_id not in self.remote_player_sprites:
                # Create new remote player if we don't have it
                remote_player = Player(
                    self.images['player2'],
                    self.config.getint('PLAYER', 'SPEED'),
                    self.config.getint('PLAYER', 'INITIAL_LIVES'),
                    [self.remote_players, self.all_sprites]
                )
                self.remote_player_sprites[player_id] = remote_player
            
            # Update position and velocity
            player = self.remote_player_sprites[player_id]
            player.position = position
            player.velocity = velocity
            player.rect.center = position
            
    def handle_remote_shoot(self, player_id, position):
        """Handle when a remote player shoots"""
        if player_id != self.player_id and player_id in self.remote_player_sprites:
            self.remote_player_sprites[player_id].shoot([self.bullets, self.all_sprites])
            
    def handle_enemy_destroyed(self, enemy_id, player_id, score):
        """Handle when an enemy is destroyed by any player"""
        if player_id == self.player_id:
            self.score += score
            
    def handle_disconnect(self):
        """Handle when disconnected from server"""
        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSED
            
    def handle_connection_error(self, error):
        """Handle connection error"""
        print(f"Connection error: {error}")
        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSED
            
    def sync_game_state(self, game_state):
        """Sync game state from server"""
        # Update scores and lives
        for player_id, data in game_state.players.items():
            if player_id == self.player_id:
                self.score = data['score']
                if self.players.sprite:
                    self.players.sprite.lives = data['lives']
            elif player_id in self.remote_player_sprites:
                player = self.remote_player_sprites[player_id]
                player.lives = data['lives']

    def run(self):
        """Main game loop"""
        running = True
        while running:
            self.clock.tick(self.fps)
            running = self.handle_events()
            self.update()
            self.draw()