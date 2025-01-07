import pygame
import os

class AudioManager:
    def __init__(self, config):
        self.config = config
        self.sounds = {}
        self.enabled = config.getboolean('GAME', 'ENABLE_SOUND')
        self.current_music = None
        self.volume = 0.7
        
        # Initialize mixer
        pygame.mixer.init()
        
        # Set default volumes
        pygame.mixer.music.set_volume(self.volume * 0.5)  # Background music slightly quieter
        
        # Load sound effects
        self.load_sounds()
        
    def load_sounds(self):
        """Load all sound effects"""
        sound_files = {
            'shoot': 'shoot.ogg',
            'explosion': 'baozha.ogg',
            'missile': 'missile.ogg',
            'powerup': 'powerup.ogg',
            'menu_select': 'select.ogg',
            'menu_click': 'click.ogg'
        }
        
        for name, filename in sound_files.items():
            try:
                path = os.path.join('src', 'assets', 'sounds', filename)
                self.sounds[name] = pygame.mixer.Sound(path)
                self.sounds[name].set_volume(self.volume)
            except pygame.error:
                print(f"Warning: Could not load sound {filename}")
                
    def play_music(self, music_name):
        """Play background music"""
        if not self.enabled:
            return
            
        if music_name != self.current_music:
            try:
                if music_name == 'menu':
                    path = os.path.join('src', 'assets', 'sounds', 'menu_music.mp3')
                else:  # game
                    path = os.path.join('src', 'assets', 'sounds', 'bgmusic.mp3')
                    
                pygame.mixer.music.load(path)
                pygame.mixer.music.play(-1)  # Loop indefinitely
                self.current_music = music_name
            except pygame.error:
                print(f"Warning: Could not load music {music_name}")
                
    def play_sound(self, sound_name):
        """Play a sound effect"""
        if not self.enabled:
            return
            
        if sound_name in self.sounds:
            self.sounds[sound_name].play()
            
    def stop_music(self):
        """Stop currently playing music"""
        pygame.mixer.music.stop()
        self.current_music = None
        
    def pause_music(self):
        """Pause background music"""
        pygame.mixer.music.pause()
        
    def unpause_music(self):
        """Unpause background music"""
        pygame.mixer.music.unpause()
        
    def set_volume(self, volume):
        """Set volume for all audio (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume * 0.5)
        for sound in self.sounds.values():
            sound.set_volume(self.volume)
            
    def toggle_sound(self):
        """Toggle sound on/off"""
        self.enabled = not self.enabled
        if self.enabled:
            pygame.mixer.music.set_volume(self.volume * 0.5)
            if self.current_music:
                pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.set_volume(0)
            pygame.mixer.music.pause()