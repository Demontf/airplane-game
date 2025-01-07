import pygame
import os
from .game_logic import GameLogic, GameState
from .sprites import Player, Enemy, Bullet, Background
from .network import NetworkManager
from .ui import Menu
from .audio import AudioManager
from .animation import AnimationManager
from .performance import PerformanceManager

class Game:
    def __init__(self, config):
        self.config = config
        
        # Initialize display
        self.width = config.getint('GAME', 'SCREEN_WIDTH')
        self.height = config.getint('GAME', 'SCREEN_HEIGHT')
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(config.get('GAME', 'TITLE'))
        
        # Initialize managers
        self.audio = AudioManager(config)
        self.animation = AnimationManager()
        self.performance = PerformanceManager(config)
        self.menu = Menu(self.width, self.height)
        
        # Initialize sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.players = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.effects = pygame.sprite.Group()
        self.backgrounds = pygame.sprite.Group()
        
        # Initialize multiplayer
        self.is_multiplayer = config.getint('NETWORK', 'ROLE') in [1, 2]
        self.network = NetworkManager(config, self) if self.is_multiplayer else None
        self.player_id = None
        self.remote_player_sprites = {}  # {player_id: sprite}
        
        # Load assets
        self.load_assets()
        
        # Initialize game logic
        self.logic = GameLogic(self)
        self.state = GameState.START
        
        # Create initial sprites
        self.create_sprites()
        
        # Start menu music
        self.audio.play_music('menu')

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
            
            # Handle menu events
            if self.state in [GameState.START, GameState.PAUSED, GameState.GAME_OVER]:
                action = self.menu.handle_event(event, self.state.name.lower())
                if action:
                    if action == 'single_player':
                        self.logic.reset_game()
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
                        self.logic.reset_game()
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
                    self.logic.reset_game()
                    self.audio.play_music('game')
        
        # Handle continuous shooting
        if self.state == GameState.PLAYING and self.players.sprite:
            self.players.sprite.shoot([self.bullets, self.all_sprites], self.network)
        
        return True

    def update(self):
        # Start performance monitoring
        self.performance.start_frame()
        
        if self.state == GameState.PLAYING:
            # Update all sprites
            self.all_sprites.update()
            
            # Update game logic
            self.logic.handle_collisions()
            if not self.is_multiplayer or (self.is_multiplayer and self.config.getint('NETWORK', 'ROLE') == 1):
                self.logic.spawn_enemies()
            self.logic.update_level()
            
            # Update particle effects
            self.particle_emitter.update()
            
            # Update animations
            for effect in self.effects:
                if effect.animation.finished:
                    effect.kill()
                else:
                    effect.image = effect.animation.update(1/60)  # Assuming 60 FPS
            
            # Update network
            if self.network and self.players.sprite:
                self.network.send_player_update(
                    self.players.sprite.position,
                    self.players.sprite.velocity
                )
                self.network.update()
        
        # End performance monitoring
        self.performance.end_frame()
            
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
            self.menu.draw(self.screen, 'game_over', score=self.logic.score)
            
        # Draw performance stats if enabled
        if self.config.getboolean('GAME', 'SHOW_PERFORMANCE'):
            self.draw_performance_stats()
            
        pygame.display.flip()

    def draw_hud(self):
        """Draw heads-up display"""
        # Create HUD surface with transparency
        hud_surface = pygame.Surface((self.width, 100), pygame.SRCALPHA)
        pygame.draw.rect(hud_surface, (0, 0, 0, 128), (0, 0, self.width, 100))
        
        font = pygame.font.Font(None, 36)
        y = 20
        
        # Draw score and high score
        score_text = font.render(f'Score: {self.logic.score}', True, (255, 255, 255))
        high_score_text = font.render(f'High Score: {self.logic.high_score}', True, (255, 255, 255))
        level_text = font.render(f'Level: {self.logic.level}', True, (255, 255, 255))
        
        hud_surface.blit(score_text, (20, y))
        hud_surface.blit(high_score_text, (20, y + 30))
        hud_surface.blit(level_text, (20, y + 60))
        
        # Draw lives with icons
        lives_text = font.render('Lives:', True, (255, 255, 255))
        lives_rect = lives_text.get_rect(topright=(self.width - 180, y))
        hud_surface.blit(lives_text, lives_rect)
        
        life_icon = pygame.transform.scale(self.images['player'], (20, 20))
        for i in range(self.players.sprite.lives):
            hud_surface.blit(life_icon, (self.width - 160 + i * 30, y))
        
        # Draw missile status
        if self.players.sprite.missile_unlocked:
            missile_text = font.render('Missiles: Ready', True, (0, 255, 0))
        else:
            progress = self.logic.score / self.config.getint('PLAYER', 'MISSILE_UNLOCK_SCORE')
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

    def run(self):
        running = True
        while running:
            self.clock.tick(self.fps)
            running = self.handle_events()
            self.update()
            self.draw()