import pygame
import random
from enum import Enum
from .sprites import Player, Enemy, Bullet, Background
from .ui import Menu
from .audio import AudioManager
from .animation import AnimationManager
from .performance import PerformanceManager

class GameState(Enum):
    START = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4

class GameLogic:
    def __init__(self, game):
        self.game = game
        self.config = game.config
        self.screen = game.screen
        self.width = game.width
        self.height = game.height
        
        # Initialize managers
        self.audio = game.audio
        self.animation = game.animation
        self.performance = game.performance
        
        # Initialize game variables
        self.score = 0
        self.high_score = 0
        self.level = 1
        self.spawn_timer = 0
        self.last_spawn_time = 0
        self.enemy_spawn_delay = 1000  # milliseconds
        
    def handle_collisions(self):
        """Handle all game collisions"""
        # Player bullets hitting enemies
        hits = pygame.sprite.groupcollide(self.game.enemies, self.game.bullets, False, True)
        for enemy, bullets in hits.items():
            for bullet in bullets:
                if enemy.take_damage(bullet.damage):
                    self.score += enemy.score_value
                    # Create explosion animation
                    from .effects import Explosion
                    Explosion(enemy.rect.center, [self.game.effects, self.game.all_sprites])
                    # Play explosion sound
                    self.audio.play_sound('explosion')
                    # Add particles
                    self.game.particle_emitter.emit(
                        enemy.rect.center,
                        (255, 165, 0),
                        num_particles=20,
                        speed=8,
                        lifetime=0.5
                    )
                    
                    # Check for missile unlock
                    if len(self.game.players) > 0:
                        player = next(iter(self.game.players))
                        if (not hasattr(player, 'missile_unlocked') or not player.missile_unlocked) and \
                           self.score >= self.config.getint('PLAYER', 'MISSILE_UNLOCK_SCORE'):
                            player.missile_unlocked = True
                            self.audio.play_sound('powerup')
        
        # Enemies hitting player
        if len(self.game.players) > 0:
            player = next(iter(self.game.players))
            if not player.is_invincible:
                hits = pygame.sprite.spritecollide(player, self.game.enemies, True)
                if hits:
                    player.take_damage()
                    self.audio.play_sound('explosion')
                    # Create explosion animation
                    for hit in hits:
                        from .effects import Explosion
                        Explosion(hit.rect.center, [self.game.effects, self.game.all_sprites])
                        # Add particles
                        self.game.particle_emitter.emit(
                            hit.rect.center,
                            (255, 0, 0),
                            num_particles=30,
                            speed=10,
                            lifetime=0.8
                        )
                    
                    if player.lives <= 0:
                        self.game_over()
        
        # Enemy bullets hitting player
        if len(self.game.players) > 0:
            player = next(iter(self.game.players))
            if not player.is_invincible:
                hits = pygame.sprite.spritecollide(player, self.game.enemy_bullets, True)
                if hits:
                    player.take_damage()
                    self.audio.play_sound('explosion')
                    # Create smaller explosion animation
                    for hit in hits:
                        from .effects import Explosion
                        Explosion(hit.rect.center, [self.game.effects, self.game.all_sprites])
                    
                    if player.lives <= 0:
                        self.game_over()
                    
    def spawn_enemies(self):
        """Handle enemy spawning"""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_spawn_time > self.enemy_spawn_delay:
            if len(self.game.enemies) < self.config.getint('ENEMY', 'MAX_ENEMIES'):
                # Calculate spawn probability based on level
                spawn_chance = min(0.8, 0.3 + (self.level - 1) * 0.1)
                if random.random() < spawn_chance:
                    # Choose enemy type with weighted probabilities
                    weights = {
                        'red': 0.5 - (self.level - 1) * 0.05,  # Decrease over levels
                        'yellow': 0.3,
                        'blue': 0.2 + (self.level - 1) * 0.05  # Increase over levels
                    }
                    enemy_type = random.choices(
                        list(weights.keys()),
                        weights=list(weights.values())
                    )[0]
                    
                    # Get enemy stats
                    if enemy_type == 'red':
                        speed = self.config.getfloat('ENEMY', 'RED_SPEED')
                        health = self.config.getint('ENEMY', 'RED_HEALTH')
                        score = self.config.getint('ENEMY', 'RED_SCORE')
                        image = self.game.images['enemy_red']
                    elif enemy_type == 'yellow':
                        speed = self.config.getfloat('ENEMY', 'YELLOW_SPEED')
                        health = self.config.getint('ENEMY', 'YELLOW_HEALTH')
                        score = self.config.getint('ENEMY', 'YELLOW_SCORE')
                        image = self.game.images['enemy_yellow']
                    else:  # blue
                        speed = self.config.getfloat('ENEMY', 'BLUE_SPEED')
                        health = self.config.getint('ENEMY', 'BLUE_HEALTH')
                        score = self.config.getint('ENEMY', 'BLUE_SCORE')
                        image = self.game.images['enemy_blue']
                    
                    # Apply level scaling
                    level_multiplier = 1 + (self.level - 1) * 0.2
                    speed *= level_multiplier
                    health = int(health * level_multiplier)
                    score = int(score * level_multiplier)
                    
                    # Create enemy
                    Enemy(
                        image=image,
                        enemy_type=enemy_type,
                        speed=speed,
                        health=health,
                        score_value=score,
                        is_special=random.random() < self.config.getfloat('ENEMY', 'SPECIAL_ENEMY_CHANCE'),
                        bullet_speed=self.config.getfloat('ENEMY', 'ENEMY_BULLET_SPEED'),
                        shoot_delay=self.config.getint('ENEMY', 'ENEMY_SHOOT_DELAY'),
                        groups=[self.game.enemies, self.game.all_sprites]
                    )
                    
                    self.last_spawn_time = current_time
                    
    def update_level(self):
        """Update game level based on score"""
        new_level = 1 + self.score // 1000
        if new_level != self.level:
            self.level = new_level
            # Decrease spawn delay as level increases
            self.enemy_spawn_delay = max(
                500,  # Minimum delay
                1000 - (self.level - 1) * 100  # Decrease by 100ms per level
            )
            
    def game_over(self):
        """Handle game over state"""
        self.game.state = GameState.GAME_OVER
        self.audio.stop_music()
        self.audio.play_sound('explosion')
        # Update high score
        if self.score > self.high_score:
            self.high_score = self.score
            
    def reset_game(self):
        """Reset game state for a new game"""
        # Clear all sprites
        self.game.all_sprites.empty()
        self.game.players.empty()
        self.game.enemies.empty()
        self.game.bullets.empty()
        self.game.enemy_bullets.empty()
        self.game.effects.empty()
        
        # Reset game variables
        self.score = 0
        self.level = 1
        self.spawn_timer = 0
        self.last_spawn_time = 0
        self.enemy_spawn_delay = 1000
        
        # Create initial sprites
        self.game.create_sprites()
        
        # Start music
        self.audio.play_music('game')
        
        # Set game state
        self.game.state = GameState.PLAYING