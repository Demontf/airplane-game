import pygame
import random
from pygame.math import Vector2

class Background(pygame.sprite.Sprite):
    def __init__(self, image, groups):
        super().__init__(groups)
        self.image = image
        self.rect = self.image.get_rect()
        self.scroll_speed = 2
        self.y1 = 0
        self.y2 = -self.rect.height

    def update(self):
        self.y1 += self.scroll_speed
        self.y2 += self.scroll_speed
        
        if self.y1 > self.rect.height:
            self.y1 = -self.rect.height
        if self.y2 > self.rect.height:
            self.y2 = -self.rect.height

    def draw(self, surface):
        surface.blit(self.image, (0, self.y1))
        surface.blit(self.image, (0, self.y2))

class Player(pygame.sprite.Sprite):
    def __init__(self, image, speed, lives, groups):
        super().__init__(groups)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.centerx = 400
        self.rect.bottom = 550
        
        self.speed = speed
        self.lives = lives
        self.is_invincible = False
        self.invincible_timer = 0
        self.missile_unlocked = False
        self.last_missile_time = 0
        
        self.position = Vector2(self.rect.center)
        self.velocity = Vector2(0, 0)

    def update(self):
        # Handle invincibility
        if self.is_invincible:
            current_time = pygame.time.get_ticks()
            if current_time - self.invincible_timer > 2000:  # 2 seconds
                self.is_invincible = False
        
        # Handle movement
        keys = pygame.key.get_pressed()
        self.velocity.x = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * self.speed
        self.velocity.y = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * self.speed
        
        # Update position
        self.position += self.velocity
        
        # Keep player on screen
        self.position.x = max(0, min(self.position.x, 800))
        self.position.y = max(0, min(self.position.y, 600))
        
        self.rect.center = self.position

    def take_damage(self):
        if not self.is_invincible:
            self.lives -= 1
            self.is_invincible = True
            self.invincible_timer = pygame.time.get_ticks()

    def shoot(self):
        # TODO: Implement shooting logic
        pass

class Enemy(pygame.sprite.Sprite):
    def __init__(self, image, enemy_type, speed, groups):
        super().__init__(groups)
        self.image = image
        self.rect = self.image.get_rect()
        self.enemy_type = enemy_type
        self.speed = speed
        
        # Spawn at random position at top of screen
        self.rect.x = random.randint(0, 800 - self.rect.width)
        self.rect.y = -self.rect.height
        
        self.position = Vector2(self.rect.center)
        self.velocity = Vector2(0, speed)
        
        # Special behaviors
        self.can_shoot = enemy_type == 'blue'
        self.can_reverse = enemy_type == 'red'
        self.is_special = random.random() < 0.2  # 20% chance for special enemy

    def update(self):
        self.position += self.velocity
        self.rect.center = self.position
        
        # Remove if off screen
        if self.rect.top > 600:
            self.kill()
        
        # Special behaviors
        if self.can_shoot and random.random() < 0.01:  # 1% chance to shoot each frame
            self.shoot()
        
        if self.can_reverse and self.is_special and self.rect.bottom > 500:
            self.velocity.y = -self.speed

    def shoot(self):
        # TODO: Implement enemy shooting logic
        pass

class Bullet(pygame.sprite.Sprite):
    def __init__(self, image, position, velocity, damage, groups):
        super().__init__(groups)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = position
        
        self.position = Vector2(position)
        self.velocity = Vector2(velocity)
        self.damage = damage

    def update(self):
        self.position += self.velocity
        self.rect.center = self.position
        
        # Remove if off screen
        if (self.rect.bottom < 0 or self.rect.top > 600 or 
            self.rect.right < 0 or self.rect.left > 800):
            self.kill()