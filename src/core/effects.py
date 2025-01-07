import pygame
from pygame.math import Vector2

class Explosion(pygame.sprite.Sprite):
    def __init__(self, position, groups):
        super().__init__(groups)
        self.frames = [
            pygame.image.load(f'src/assets/images/explosion_{i}.png').convert_alpha()
            for i in range(8)
        ]
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.rect.center = position
        self.frame_index = 0
        self.animation_speed = 0.2
        self.frame_time = 0
        
    def update(self):
        # Update animation
        self.frame_time += 0.1
        if self.frame_time >= self.animation_speed:
            self.frame_time = 0
            self.frame_index += 1
            if self.frame_index >= len(self.frames):
                self.kill()  # Remove explosion when animation is done
            else:
                self.image = self.frames[self.frame_index]

class ParticleEmitter:
    def __init__(self):
        self.particles = []
        
    def emit(self, position, color, num_particles=10, speed=5, lifetime=1.0):
        """Create particles at the given position"""
        for _ in range(num_particles):
            angle = random.uniform(0, 360)
            speed = random.uniform(1, speed)
            velocity = Vector2(
                speed * math.cos(math.radians(angle)),
                speed * math.sin(math.radians(angle))
            )
            self.particles.append({
                'pos': Vector2(position),
                'vel': velocity,
                'color': color,
                'lifetime': lifetime,
                'time': 0
            })
    
    def update(self):
        """Update all particles"""
        # Update existing particles
        for particle in self.particles[:]:
            particle['time'] += 0.1
            if particle['time'] >= particle['lifetime']:
                self.particles.remove(particle)
            else:
                particle['pos'] += particle['vel']
                # Add gravity effect
                particle['vel'].y += 0.1
    
    def draw(self, surface):
        """Draw all particles"""
        for particle in self.particles:
            alpha = int(255 * (1 - particle['time'] / particle['lifetime']))
            color = (*particle['color'], alpha)
            pos = (int(particle['pos'].x), int(particle['pos'].y))
            pygame.draw.circle(surface, color, pos, 2)