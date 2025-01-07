import pygame
import time
from collections import deque

class PerformanceManager:
    def __init__(self, config):
        """Initialize performance manager"""
        self.config = config
        self.frame_times = deque(maxlen=60)  # Store last 60 frame times
        self.last_frame_time = time.time()
        self.current_fps = 60
        self.particle_count = 0
        self.sprite_count = 0
        self.network_latency = 0
        
        # Performance flags
        self.vsync_enabled = config.getboolean('GAME', 'ENABLE_VSYNC', fallback=True)
        self.max_particles = config.getint('GAME', 'MAX_PARTICLES', fallback=100)
        self.sound_enabled = config.getboolean('GAME', 'ENABLE_SOUND', fallback=True)
        
        # Initialize performance settings
        if self.vsync_enabled:
            pygame.display.set_mode((
                config.getint('GAME', 'SCREEN_WIDTH'),
                config.getint('GAME', 'SCREEN_HEIGHT')
            ), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.SCALED)
        
        # Pre-render common surfaces
        self.cached_surfaces = {}
        
    def start_frame(self):
        """Call at the start of each frame"""
        self.last_frame_time = time.time()
        
    def end_frame(self):
        """Call at the end of each frame"""
        frame_time = time.time() - self.last_frame_time
        self.frame_times.append(frame_time)
        if self.frame_times:  # Check if deque is not empty
            self.current_fps = 1.0 / (sum(self.frame_times) / len(self.frame_times))
        
    def should_spawn_particle(self):
        """Check if we can spawn more particles"""
        return self.particle_count < self.max_particles
        
    def update_sprite_count(self, count):
        """Update total sprite count"""
        self.sprite_count = count
        
    def update_network_latency(self, latency):
        """Update network latency measurement"""
        self.network_latency = latency
        
    def get_cached_surface(self, key, creator_func):
        """Get or create a cached surface"""
        if key not in self.cached_surfaces:
            self.cached_surfaces[key] = creator_func()
        return self.cached_surfaces[key]
        
    def clear_cache(self):
        """Clear the surface cache"""
        self.cached_surfaces.clear()
        
    def get_stats(self):
        """Get current performance stats"""
        return {
            'fps': round(self.current_fps, 1),
            'sprite_count': self.sprite_count,
            'particle_count': self.particle_count,
            'network_latency': round(self.network_latency * 1000, 1),  # Convert to ms
            'vsync': self.vsync_enabled,
            'sound': self.sound_enabled
        }
        
    def optimize_automatically(self):
        """Automatically adjust settings based on performance"""
        if self.current_fps < 45:  # Performance is poor
            if self.particle_count > self.max_particles // 2:
                self.max_particles = self.max_particles // 2  # Reduce particles
            if self.vsync_enabled:
                self.vsync_enabled = False  # Disable VSync
            if self.sound_enabled and self.current_fps < 30:
                self.sound_enabled = False  # Disable sound as last resort
        elif self.current_fps > 58:  # Performance is good
            if self.max_particles < self.config.getint('GAME', 'MAX_PARTICLES', fallback=100):
                self.max_particles *= 1.5  # Increase particles
            if not self.vsync_enabled:
                self.vsync_enabled = True  # Enable VSync
            if not self.sound_enabled:
                self.sound_enabled = True  # Re-enable sound