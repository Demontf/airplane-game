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
        self.remote_players = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.backgrounds = pygame.sprite.Group()
        
        # Initialize multiplayer
        self.is_multiplayer = config.getint('NETWORK', 'ROLE') in [1, 2]
        self.network = NetworkManager(config, self) if self.is_multiplayer else None
        self.player_id = None
        self.remote_player_sprites = {}  # {player_id: sprite}
        
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
                elif event.key == pygame.K_RETURN:
                    if self.state == GameState.START:
                        self.state = GameState.PLAYING
                        pygame.mixer.music.play(-1)
                    elif self.state == GameState.GAME_OVER:
                        # Reset game state
                        self.state = GameState.PLAYING
                        self.score = 0
                        
                        # Clear all sprites
                        self.all_sprites.empty()
                        self.players.empty()
                        self.enemies.empty()
                        self.bullets.empty()
                        self.backgrounds.empty()
                        
                        # Create initial sprites
                        self.create_sprites()
                        
                        # Restart music
                        pygame.mixer.music.play(-1)
        
        # Handle continuous shooting
        if self.state == GameState.PLAYING:
            self.players.sprite.shoot([self.bullets, self.all_sprites])
        
        return True

    def update(self):
        if self.state != GameState.PLAYING:
            return
        
        # Update all sprites
        self.all_sprites.update()
        
        # Handle collisions
        self.handle_collisions()
        
        # Spawn enemies (only host spawns enemies in multiplayer)
        if not self.is_multiplayer or (self.is_multiplayer and self.config.getint('NETWORK', 'ROLE') == 1):
            self.spawn_enemies()
        
        # Update network and sync player position
        if self.network and self.players.sprite:
            self.network.send_player_update(
                self.players.sprite.position,
                self.players.sprite.velocity
            )
            self.network.update()
            
    def handle_player_joined(self, data):
        """Handle when a new player joins the game"""
        self.player_id = data['player_id']
        
        # Create remote player sprite if it's not us
        if self.player_id != data['player_id']:
            remote_player = Player(
                self.images['hero2'],  # Use different sprite for remote player
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
                    self.images['hero2'],
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

    def draw(self):
        self.screen.fill((0, 0, 0))
        
        if self.state == GameState.START:
            # Draw start screen
            self.screen.blit(self.images['background'], (0, 0))
            start_text = pygame.font.Font(None, 64).render('Press ENTER to Start', True, (255, 255, 255))
            text_rect = start_text.get_rect(center=(self.width // 2, self.height // 2))
            self.screen.blit(start_text, text_rect)
        
        elif self.state == GameState.PLAYING or self.state == GameState.PAUSED:
            # Draw backgrounds
            for bg in self.backgrounds:
                bg.draw(self.screen)
            
            # Draw all other sprites
            for sprite in self.all_sprites:
                if sprite not in self.backgrounds:
                    self.screen.blit(sprite.image, sprite.rect)
            
            # Draw HUD
            self.draw_hud()
            
            if self.state == GameState.PAUSED:
                # Create semi-transparent overlay
                overlay = pygame.Surface((self.width, self.height))
                overlay.fill((0, 0, 0))
                overlay.set_alpha(128)
                self.screen.blit(overlay, (0, 0))
                
                # Draw pause text
                pause_text = pygame.font.Font(None, 64).render('PAUSED', True, (255, 255, 255))
                text_rect = pause_text.get_rect(center=(self.width // 2, self.height // 2))
                self.screen.blit(pause_text, text_rect)
        
        elif self.state == GameState.GAME_OVER:
            # Draw game over screen
            self.screen.blit(self.images['gameover'], (0, 0))
            
            # Draw final score
            score_text = pygame.font.Font(None, 48).render(f'Final Score: {self.score}', True, (255, 255, 255))
            text_rect = score_text.get_rect(center=(self.width // 2, self.height // 2 + 50))
            self.screen.blit(score_text, text_rect)
            
            # Draw restart instruction
            restart_text = pygame.font.Font(None, 36).render('Press ENTER to Play Again', True, (255, 255, 255))
            text_rect = restart_text.get_rect(center=(self.width // 2, self.height // 2 + 100))
            self.screen.blit(restart_text, text_rect)
        
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