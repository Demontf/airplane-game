import pygame
import math

class Animation:
    def __init__(self, frames, frame_duration, loop=False):
        self.frames = frames
        self.frame_duration = frame_duration
        self.loop = loop
        self.current_frame = 0
        self.frame_time = 0
        self.finished = False
        
    def update(self, dt):
        if self.finished and not self.loop:
            return self.frames[-1]
            
        self.frame_time += dt
        if self.frame_time >= self.frame_duration:
            self.frame_time = 0
            self.current_frame += 1
            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.frames) - 1
                    self.finished = True
                    
        return self.frames[self.current_frame]
        
    def reset(self):
        """Reset animation to start"""
        self.current_frame = 0
        self.frame_time = 0
        self.finished = False

class AnimationManager:
    def __init__(self):
        self.animations = {}
        
    def create_explosion_animation(self, size):
        """Create explosion animation frames"""
        frames = []
        num_frames = 8
        
        for i in range(num_frames):
            # Create frame surface
            surface = pygame.Surface(size, pygame.SRCALPHA)
            
            # Calculate explosion parameters
            progress = i / (num_frames - 1)
            radius = int(min(size[0], size[1]) * 0.5 * progress)
            alpha = int(255 * (1 - progress))
            
            # Draw explosion circle
            pygame.draw.circle(surface, (255, 165, 0, alpha), 
                             (size[0]//2, size[1]//2), radius)
            
            # Add some particles
            for _ in range(8):
                angle = math.radians(360 * i / 8)
                dist = radius * 0.8
                x = size[0]//2 + math.cos(angle) * dist
                y = size[1]//2 + math.sin(angle) * dist
                particle_size = max(2, int(4 * (1 - progress)))
                pygame.draw.circle(surface, (255, 200, 0, alpha),
                                 (int(x), int(y)), particle_size)
            
            frames.append(surface)
            
        return Animation(frames, 0.1)
        
    def create_powerup_animation(self, size):
        """Create powerup animation frames"""
        frames = []
        num_frames = 6
        
        for i in range(num_frames):
            surface = pygame.Surface(size, pygame.SRCALPHA)
            progress = i / (num_frames - 1)
            
            # Draw glowing circle
            radius = int(min(size[0], size[1]) * 0.3)
            pulse = math.sin(progress * math.pi * 2) * 0.2 + 0.8
            glow_radius = int(radius * pulse)
            
            for r in range(glow_radius, 0, -2):
                alpha = int(255 * (r / glow_radius) * 0.5)
                pygame.draw.circle(surface, (0, 255, 255, alpha),
                                 (size[0]//2, size[1]//2), r)
            
            frames.append(surface)
            
        return Animation(frames, 0.1, loop=True)
        
    def create_shield_animation(self, size):
        """Create shield animation frames"""
        frames = []
        num_frames = 8
        
        for i in range(num_frames):
            surface = pygame.Surface(size, pygame.SRCALPHA)
            progress = i / (num_frames - 1)
            
            # Draw shield circle
            radius = int(min(size[0], size[1]) * 0.5)
            thickness = max(1, int(radius * 0.1))
            angle = progress * math.pi * 2
            
            # Draw rotating arc
            rect = pygame.Rect(0, 0, radius*2, radius*2)
            rect.center = (size[0]//2, size[1]//2)
            
            start_angle = math.degrees(angle)
            arc_length = 180
            
            pygame.draw.arc(surface, (100, 200, 255, 128), rect,
                          math.radians(start_angle),
                          math.radians(start_angle + arc_length),
                          thickness)
            
            frames.append(surface)
            
        return Animation(frames, 0.1, loop=True)
        
    def get_animation(self, name, size):
        """Get or create an animation"""
        key = f"{name}_{size[0]}x{size[1]}"
        if key not in self.animations:
            if name == 'explosion':
                self.animations[key] = self.create_explosion_animation(size)
            elif name == 'powerup':
                self.animations[key] = self.create_powerup_animation(size)
            elif name == 'shield':
                self.animations[key] = self.create_shield_animation(size)
                
        return self.animations[key]