import pygame
import os
import wave
import struct
import numpy as np

class AudioManager:
    def __init__(self, config):
        self.config = config
        self.enabled = config.getboolean('GAME', 'ENABLE_SOUND', fallback=True)
        self.volume = 0.5
        self.current_music = None
        self.sounds = {}
        
        # Initialize mixer
        pygame.mixer.init()
        pygame.mixer.music.set_volume(self.volume)
        
        # Load sounds
        self.load_sounds()
        
        # Create default sounds if needed
        self.create_default_sounds()
        
    def create_default_sounds(self):
        """Create default sounds if files are missing"""
        # Create default music
        if not os.path.exists(os.path.join('src', 'assets', 'sounds', 'bgmusic.mp3')):
            self.create_default_music()
            
        # Create default sound effects
        if not os.path.exists(os.path.join('src', 'assets', 'sounds', 'baozha.ogg')):
            self.create_default_explosion()
            
    def create_default_music(self):
        """Create a simple background music"""
        # Create a directory if it doesn't exist
        os.makedirs(os.path.join('src', 'assets', 'sounds'), exist_ok=True)
        
        # Create a simple WAV file
        path = os.path.join('src', 'assets', 'sounds', 'bgmusic.wav')
        with wave.open(path, 'w') as wav:
            # Set parameters
            nchannels = 1
            sampwidth = 2
            framerate = 44100
            nframes = framerate * 2  # 2 seconds
            comptype = 'NONE'
            compname = 'not compressed'
            
            # Set WAV file parameters
            wav.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname))
            
            # Create a simple melody
            frequency = 440  # A4 note
            samples = []
            for i in range(nframes):
                t = float(i) / framerate
                value = int(32767 * np.sin(2 * np.pi * frequency * t))
                packed_value = struct.pack('h', value)
                samples.append(packed_value)
            
            wav.writeframes(b''.join(samples))
            
    def create_default_explosion(self):
        """Create a simple explosion sound effect"""
        path = os.path.join('src', 'assets', 'sounds', 'explosion.wav')
        with wave.open(path, 'w') as wav:
            # Set parameters
            nchannels = 1
            sampwidth = 2
            framerate = 44100
            nframes = int(framerate * 0.5)  # 0.5 seconds
            comptype = 'NONE'
            compname = 'not compressed'
            
            # Set WAV file parameters
            wav.setparams((nchannels, sampwidth, framerate, nframes, comptype, compname))
            
            # Create a noise burst that fades out
            samples = []
            for i in range(nframes):
                t = float(i) / nframes
                fade = 1 - t  # Linear fade out
                value = int(32767 * fade * (np.random.random() * 2 - 1))
                packed_value = struct.pack('h', value)
                samples.append(packed_value)
            
            wav.writeframes(b''.join(samples))
        
    def load_sounds(self):
        """Load all sound effects"""
        sound_files = {
            'explosion': ['baozha.ogg', 'explosion.wav'],
            'shoot': ['shoot.ogg', 'shoot.wav'],
            'powerup': ['powerup.ogg', 'powerup.wav']
        }
        
        for name, filenames in sound_files.items():
            loaded = False
            for filename in filenames:
                try:
                    path = os.path.join('src', 'assets', 'sounds', filename)
                    if os.path.exists(path):
                        self.sounds[name] = pygame.mixer.Sound(path)
                        self.sounds[name].set_volume(self.volume)
                        loaded = True
                        break
                except pygame.error as e:
                    print(f"Warning: Could not load sound {filename}: {e}")
            
            if not loaded:
                print(f"Warning: Could not load any sound for {name}")
                
    def play_music(self, music_name):
        """Play background music"""
        if not self.enabled:
            return
            
        if music_name != self.current_music:
            try:
                # Try different file formats
                for ext in ['.mp3', '.wav', '.ogg']:
                    if music_name == 'menu':
                        path = os.path.join('src', 'assets', 'sounds', f'menu_music{ext}')
                    else:  # game
                        path = os.path.join('src', 'assets', 'sounds', f'bgmusic{ext}')
                        
                    if os.path.exists(path):
                        pygame.mixer.music.load(path)
                        pygame.mixer.music.play(-1)  # Loop indefinitely
                        self.current_music = music_name
                        return
                        
                print(f"Warning: Could not load music {music_name}")
            except pygame.error as e:
                print(f"Warning: Could not load music {music_name}: {e}")
                
    def play_sound(self, sound_name):
        """Play a sound effect"""
        if not self.enabled:
            return
            
        if sound_name in self.sounds:
            self.sounds[sound_name].play()
            
    def stop_music(self):
        """Stop background music"""
        pygame.mixer.music.stop()
        self.current_music = None
        
    def pause_music(self):
        """Pause background music"""
        pygame.mixer.music.pause()
        
    def unpause_music(self):
        """Unpause background music"""
        pygame.mixer.music.unpause()
        
    def toggle_sound(self):
        """Toggle sound on/off"""
        self.enabled = not self.enabled
        if self.enabled:
            pygame.mixer.music.set_volume(self.volume)
            for sound in self.sounds.values():
                sound.set_volume(self.volume)
        else:
            pygame.mixer.music.set_volume(0)
            for sound in self.sounds.values():
                sound.set_volume(0)