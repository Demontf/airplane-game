import unittest
import pygame
from unittest.mock import Mock, patch
from src.core.game_logic import GameLogic, GameState
from src.core.sprites import Player, Enemy, Bullet

class TestGameLogic(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        pygame.init()
        self.mock_game = Mock()
        self.mock_game.config = Mock()
        self.mock_game.config.getint.return_value = 100
        self.mock_game.config.getfloat.return_value = 1.0
        self.mock_game.width = 800
        self.mock_game.height = 600
        self.mock_game.screen = pygame.Surface((800, 600))
        self.mock_game.all_sprites = pygame.sprite.Group()
        self.mock_game.players = pygame.sprite.Group()
        self.mock_game.enemies = pygame.sprite.Group()
        self.mock_game.bullets = pygame.sprite.Group()
        self.mock_game.enemy_bullets = pygame.sprite.Group()
        self.mock_game.effects = pygame.sprite.Group()
        
        self.game_logic = GameLogic(self.mock_game)
        
    def tearDown(self):
        """Clean up after tests"""
        pygame.quit()
        
    def test_initial_state(self):
        """Test initial game state"""
        self.assertEqual(self.game_logic.score, 0)
        self.assertEqual(self.game_logic.high_score, 0)
        self.assertEqual(self.game_logic.level, 1)
        self.assertEqual(self.game_logic.enemy_spawn_delay, 1000)
        
    def test_update_level(self):
        """Test level update based on score"""
        # Level 1 at start
        self.assertEqual(self.game_logic.level, 1)
        
        # Level 2 at 1000 points
        self.game_logic.score = 1000
        self.game_logic.update_level()
        self.assertEqual(self.game_logic.level, 2)
        
        # Level 3 at 2000 points
        self.game_logic.score = 2000
        self.game_logic.update_level()
        self.assertEqual(self.game_logic.level, 3)
        
        # Check spawn delay decrease
        self.assertLess(self.game_logic.enemy_spawn_delay, 1000)
        
    def test_game_over(self):
        """Test game over state"""
        # Set initial score and trigger game over
        self.game_logic.score = 500
        self.game_logic.game_over()
        
        # Check state and high score
        self.assertEqual(self.mock_game.state, GameState.GAME_OVER)
        self.assertEqual(self.game_logic.high_score, 500)
        
        # Test high score is only updated if beaten
        self.game_logic.score = 300
        self.game_logic.game_over()
        self.assertEqual(self.game_logic.high_score, 500)
        
    def test_reset_game(self):
        """Test game reset"""
        # Set up some game state
        self.game_logic.score = 1000
        self.game_logic.level = 3
        self.game_logic.enemy_spawn_delay = 700
        
        # Reset game
        self.game_logic.reset_game()
        
        # Check everything is reset
        self.assertEqual(self.game_logic.score, 0)
        self.assertEqual(self.game_logic.level, 1)
        self.assertEqual(self.game_logic.enemy_spawn_delay, 1000)
        self.assertEqual(self.mock_game.state, GameState.PLAYING)
        
    @patch('random.random')
    @patch('random.choice')
    def test_spawn_enemies(self, mock_choice, mock_random):
        """Test enemy spawning"""
        # Mock random choices
        mock_choice.return_value = 'red'
        mock_random.return_value = 0.1  # Below spawn threshold
        
        # Test enemy spawning
        self.game_logic.spawn_enemies()
        self.assertEqual(len(self.mock_game.enemies), 1)
        
        # Test enemy limit
        for _ in range(10):
            self.game_logic.spawn_enemies()
        self.assertLessEqual(len(self.mock_game.enemies), 
                           self.mock_game.config.getint('ENEMY', 'MAX_ENEMIES'))
        
    def test_handle_collisions(self):
        """Test collision handling"""
        # Create test sprites
        player = Player(pygame.Surface((32, 32)), 5, 3, [self.mock_game.players])
        enemy = Enemy(pygame.Surface((32, 32)), 'red', 3, 1, 100, False, 5, 1000,
                     [self.mock_game.enemies])
        bullet = Bullet(pygame.Surface((8, 8)), (400, 300), (0, -10), 1,
                       [self.mock_game.bullets])
        
        # Test bullet hitting enemy
        enemy.rect.center = bullet.rect.center
        self.game_logic.handle_collisions()
        self.assertEqual(self.game_logic.score, 100)
        
        # Test enemy hitting player
        enemy = Enemy(pygame.Surface((32, 32)), 'red', 3, 1, 100, False, 5, 1000,
                     [self.mock_game.enemies])
        enemy.rect.center = player.rect.center
        self.game_logic.handle_collisions()
        self.assertEqual(player.lives, 2)
        
        # Test game over when player loses all lives
        player.lives = 1
        enemy = Enemy(pygame.Surface((32, 32)), 'red', 3, 1, 100, False, 5, 1000,
                     [self.mock_game.enemies])
        enemy.rect.center = player.rect.center
        self.game_logic.handle_collisions()
        self.assertEqual(self.mock_game.state, GameState.GAME_OVER)

if __name__ == '__main__':
    unittest.main()