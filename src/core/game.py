import pygame
from enum import Enum
from .sprites import Player, Enemy, Bullet, Background
from .network import NetworkManager

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
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(config.get('GAME', 'TITLE'))
        
        # Initialize clock
        self.clock = pygame.time.Clock()
        self.fps = config.getint('GAME', 'FPS')
        
        # Initialize game state
        self.state = GameState.START
        self.score = 0
        
        # Initialize sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.players = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.backgrounds = pygame.sprite.Group()
        
        # Initialize network if multiplayer
        self.network = NetworkManager(config) if config.getint('NETWORK', 'ROLE') in [1, 2] else None
        
        # Load assets
        self.load_assets()
        
        # Create initial sprites
        self.create_sprites()

    def load_assets(self):
        # Load images
        self.images = {
            'background': pygame.image.load('src/assets/images/bg.png').convert(),
            'player': pygame.image.load('src/assets/images/hero1.png').convert_alpha(),
            'enemy_red': pygame.image.load('src/assets/images/enemy01.png').convert_alpha(),
            'enemy_yellow': pygame.image.load('src/assets/images/enemy02.png').convert_alpha(),
            'enemy_blue': pygame.image.load('src/assets/images/enemy03.png').convert_alpha(),
            'bullet': pygame.image.load('src/assets/images/b2.png').convert_alpha(),
            'missile': pygame.image.load('src/assets/images/b.png').convert_alpha(),
            'explosion': pygame.image.load('src/assets/images/effer.png').convert_alpha(),
        }
        
        # Load sounds
        pygame.mixer.music.load('src/assets/sounds/bgmusic.mp3')
        self.sounds = {
            'explosion': pygame.mixer.Sound('src/assets/sounds/baozha.ogg'),
        }

    def create_sprites(self):
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
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.PAUSED
                    elif self.state == GameState.PAUSED:
                        self.state = GameState.PLAYING
                elif event.key == pygame.K_RETURN and self.state == GameState.START:
                    self.state = GameState.PLAYING
                    pygame.mixer.music.play(-1)
        
        return True

    def update(self):
        if self.state != GameState.PLAYING:
            return
        
        # Update all sprites
        self.all_sprites.update()
        
        # Handle collisions
        self.handle_collisions()
        
        # Spawn enemies
        self.spawn_enemies()
        
        # Update network
        if self.network:
            self.network.update()

    def handle_collisions(self):
        # Player bullets hitting enemies
        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True)
        for hit in hits:
            self.score += 100
            self.sounds['explosion'].play()
            # TODO: Add explosion animation
        
        # Enemies hitting player
        hits = pygame.sprite.spritecollide(self.players.sprite, self.enemies, True)
        if hits and not self.players.sprite.is_invincible:
            self.players.sprite.take_damage()
            self.sounds['explosion'].play()
            if self.players.sprite.lives <= 0:
                self.state = GameState.GAME_OVER

    def spawn_enemies(self):
        if len(self.enemies) < self.config.getint('ENEMY', 'MAX_ENEMIES'):
            # TODO: Implement enemy spawning logic
            pass

    def draw(self):
        self.screen.fill((0, 0, 0))
        
        if self.state == GameState.START:
            # Draw start screen
            pass
        elif self.state == GameState.PLAYING or self.state == GameState.PAUSED:
            # Draw all sprites
            self.all_sprites.draw(self.screen)
            
            # Draw HUD
            self.draw_hud()
            
            if self.state == GameState.PAUSED:
                # Draw pause overlay
                pass
        elif self.state == GameState.GAME_OVER:
            # Draw game over screen
            pass
        
        pygame.display.flip()

    def draw_hud(self):
        # Draw score
        font = pygame.font.Font(None, 36)
        score_text = font.render(f'Score: {self.score}', True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))
        
        # Draw lives
        lives_text = font.render(f'Lives: {self.players.sprite.lives}', True, (255, 255, 255))
        self.screen.blit(lives_text, (10, 50))

    def run(self):
        running = True
        while running:
            self.clock.tick(self.fps)
            running = self.handle_events()
            self.update()
            self.draw()