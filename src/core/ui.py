import pygame
import math

class Button:
    def __init__(self, x, y, width, height, text, font_size=36, color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.font = pygame.font.Font(None, font_size)
        self.is_hovered = False
        
    def draw(self, surface):
        # Draw button background with hover effect
        alpha = 200 if self.is_hovered else 128
        button_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(button_surface, (*self.color, alpha), 
                        (0, 0, self.rect.width, self.rect.height), 
                        border_radius=10)
        
        # Draw text
        text_surface = self.font.render(self.text, True, self.color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        
        # Draw glow effect when hovered
        if self.is_hovered:
            glow_surface = pygame.Surface((self.rect.width + 20, self.rect.height + 20), 
                                       pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*self.color, 50),
                           (0, 0, glow_surface.get_width(), glow_surface.get_height()),
                           border_radius=15)
            surface.blit(glow_surface, 
                        (self.rect.x - 10, self.rect.y - 10))
        
        surface.blit(button_surface, self.rect)
        surface.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False

class Menu:
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.buttons = {}
        self.current_menu = "main"
        
        # Create menu buttons
        self.create_main_menu()
        self.create_pause_menu()
        self.create_game_over_menu()
        
    def create_main_menu(self):
        button_width = 200
        button_height = 50
        spacing = 20
        start_y = self.height // 2 - 100
        
        self.buttons["main"] = {
            "single_player": Button(
                self.width//2 - button_width//2,
                start_y,
                button_width,
                button_height,
                "Single Player",
                color=(0, 255, 0)
            ),
            "multiplayer": Button(
                self.width//2 - button_width//2,
                start_y + button_height + spacing,
                button_width,
                button_height,
                "Multiplayer",
                color=(0, 200, 255)
            ),
            "quit": Button(
                self.width//2 - button_width//2,
                start_y + (button_height + spacing) * 2,
                button_width,
                button_height,
                "Quit",
                color=(255, 100, 100)
            )
        }
        
    def create_pause_menu(self):
        button_width = 200
        button_height = 50
        spacing = 20
        start_y = self.height // 2 - 75
        
        self.buttons["pause"] = {
            "resume": Button(
                self.width//2 - button_width//2,
                start_y,
                button_width,
                button_height,
                "Resume",
                color=(0, 255, 0)
            ),
            "main_menu": Button(
                self.width//2 - button_width//2,
                start_y + button_height + spacing,
                button_width,
                button_height,
                "Main Menu",
                color=(255, 200, 0)
            )
        }
        
    def create_game_over_menu(self):
        button_width = 200
        button_height = 50
        spacing = 20
        start_y = self.height // 2 + 50
        
        self.buttons["game_over"] = {
            "retry": Button(
                self.width//2 - button_width//2,
                start_y,
                button_width,
                button_height,
                "Try Again",
                color=(0, 255, 0)
            ),
            "main_menu": Button(
                self.width//2 - button_width//2,
                start_y + button_height + spacing,
                button_width,
                button_height,
                "Main Menu",
                color=(255, 200, 0)
            )
        }
        
    def draw(self, surface, menu_type, **kwargs):
        # Draw menu background
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        surface.blit(overlay, (0, 0))
        
        # Draw menu title
        font = pygame.font.Font(None, 72)
        if menu_type == "main":
            title = "AIRPLANE BATTLE"
            color = (255, 255, 255)
        elif menu_type == "pause":
            title = "PAUSED"
            color = (255, 200, 0)
        else:  # game_over
            title = "GAME OVER"
            color = (255, 50, 50)
            
            # Draw score in game over menu
            if 'score' in kwargs:
                score_font = pygame.font.Font(None, 48)
                score_text = score_font.render(f"Score: {kwargs['score']}", True, (255, 255, 255))
                score_rect = score_text.get_rect(center=(self.width//2, self.height//2))
                surface.blit(score_text, score_rect)
        
        title_surface = font.render(title, True, color)
        title_rect = title_surface.get_rect(center=(self.width//2, self.height//4))
        surface.blit(title_surface, title_rect)
        
        # Draw buttons
        for button in self.buttons[menu_type].values():
            button.draw(surface)
            
    def handle_event(self, event, menu_type):
        """Handle menu events and return action if button clicked"""
        for action, button in self.buttons[menu_type].items():
            if button.handle_event(event):
                return action
        return None