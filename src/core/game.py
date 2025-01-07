import pygame
import os
from .game_logic import GameLogic, GameState
from .sprites import Player, Enemy, Bullet, Background
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
        """Load all game assets"""
        self.images = {}
        image_files = {
            'background': 'bg.png',
            'player': 'hero1.png',
            'player2': 'hero2.png',
            'enemy_red': 'enemy01.png',
            'enemy_yellow': 'enemy02.png',
            'enemy_blue': 'enemy03.png',
            'bullet': 'b2.png',
            'enemy_bullet': 'b3.png',
            'missile': 'b.png',
            'explosion': 'effer.png',
            'explosion2': 'effer2.png',
            'start': 'start.png',
            'gameover': 'gameover.png'
        }
        
        for name, filename in image_files.items():
            path = os.path.join('src', 'assets', 'images', filename)
            try:
                self.images[name] = pygame.image.load(path).convert_alpha()
            except pygame.error:
                print(f"Warning: Could not load image {filename}")
                
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
                    
            # Handle menu events
            if self.state in [GameState.START, GameState.PAUSED, GameState.GAME_OVER]:
                action = self.menu.handle_event(event, self.state.name.lower())
                if action:
                    self.handle_menu_action(action)
                    
        return True
        
    def handle_menu_action(self, action):
        """Handle menu button clicks"""
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
            
        return True
        
    def update(self):
        """Update game state"""
        # Start performance monitoring
        self.performance.start_frame()
        
        if self.state == GameState.PLAYING:
            # Update all sprites
            self.all_sprites.update()
            
            # Handle game logic
            self.logic.handle_collisions()
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
                    
        # End performance monitoring
        self.performance.end_frame()
        
    def draw(self):
        """Draw everything to the screen"""
        self.screen.fill((0, 0, 0))
        
        # Draw game state
        if self.state == GameState.START:
            self.menu.draw(self.screen, 'main')
        elif self.state == GameState.PLAYING:
            # Draw game world
            self.backgrounds.draw(self.screen)
            self.all_sprites.draw(self.screen)
            self.effects.draw(self.screen)
            self.particle_emitter.draw(self.screen)
            
            # Draw HUD
            self.draw_hud()
        elif self.state == GameState.PAUSED:
            # Draw game world (dimmed)
            self.backgrounds.draw(self.screen)
            self.all_sprites.draw(self.screen)
            self.effects.draw(self.screen)
            self.particle_emitter.draw(self.screen)
            
            # Draw pause menu
            self.menu.draw(self.screen, 'pause')
        elif self.state == GameState.GAME_OVER:
            self.menu.draw(self.screen, 'game_over', score=self.logic.score)
            
        # Draw performance stats if enabled
        if self.config.getboolean('GAME', 'SHOW_PERFORMANCE'):
            self.draw_performance_stats()
            
        pygame.display.flip()
        
    def draw_hud(self):
        """Draw heads-up display"""
        font = pygame.font.Font(None, 36)
        
        # Draw score
        score_text = font.render(f'Score: {self.logic.score}', True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))
        
        # Draw high score
        high_score_text = font.render(f'High Score: {self.logic.high_score}', True, (255, 255, 255))
        self.screen.blit(high_score_text, (10, 50))
        
        # Draw level
        level_text = font.render(f'Level: {self.logic.level}', True, (255, 255, 255))
        self.screen.blit(level_text, (10, 90))
        
        # Draw lives
        lives_text = font.render(f'Lives: {self.players.sprite.lives}', True, (255, 255, 255))
        self.screen.blit(lives_text, (self.width - 150, 10))
        
        # Draw missile status
        if self.players.sprite.missile_unlocked:
            missile_text = font.render('Missiles: Ready', True, (0, 255, 0))
        else:
            progress = self.logic.score / self.config.getint('PLAYER', 'MISSILE_UNLOCK_SCORE')
            missile_text = font.render(f'Missiles: {int(progress * 100)}%', True, (255, 165, 0))
        self.screen.blit(missile_text, (self.width - 200, 50))
        
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
        """Main game loop"""
        clock = pygame.time.Clock()
        running = True
        
        while running:
            # Maintain frame rate
            clock.tick(self.config.getint('GAME', 'FPS'))
            
            # Handle events
            running = self.handle_events()
            
            # Update game state
            self.update()
            
            # Draw everything
            self.draw()
            
        # Clean up
        pygame.quit()