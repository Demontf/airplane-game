import pygame
import math
import random
import numpy as np
from pygame.math import Vector2
from pygame import Surface, SRCALPHA
from typing import Tuple, List

def gaussian_blur(surface: Surface, radius: int = 5) -> Surface:
    """Apply gaussian blur to a surface"""
    width, height = surface.get_size()
    
    # Create a larger surface to handle edge effects
    pad = radius * 2
    padded = pygame.Surface((width + pad * 2, height + pad * 2), SRCALPHA)
    padded.fill((0, 0, 0, 0))
    padded.blit(surface, (pad, pad))
    
    # Create kernel
    kernel_size = radius * 2 + 1
    kernel = np.zeros((kernel_size, kernel_size))
    sigma = radius / 3
    for x in range(kernel_size):
        for y in range(kernel_size):
            dx = x - radius
            dy = y - radius
            kernel[x, y] = np.exp(-(dx*dx + dy*dy)/(2*sigma*sigma))
    kernel = kernel / kernel.sum()
    
    # Get pixel array
    pixels = pygame.surfarray.pixels_alpha(padded)
    
    # Apply convolution
    result = np.zeros_like(pixels)
    for x in range(pad, width + pad):
        for y in range(pad, height + pad):
            value = 0
            for kx in range(kernel_size):
                for ky in range(kernel_size):
                    px = x + kx - radius
                    py = y + ky - radius
                    value += pixels[px, py] * kernel[kx, ky]
            result[x, y] = value
    
    # Create output surface
    output = pygame.Surface((width, height), SRCALPHA)
    output.fill((0, 0, 0, 0))
    
    # Copy blurred alpha values
    for x in range(width):
        for y in range(height):
            color = surface.get_at((x, y))
            alpha = int(result[x + pad, y + pad])
            output.set_at((x, y), (color[0], color[1], color[2], alpha))
    
    return output

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