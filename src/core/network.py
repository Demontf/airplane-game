import socketio
import json
import threading
import eventlet
import logging
from pygame.math import Vector2

class GameState:
    def __init__(self):
        self.players = {}  # {player_id: {'position': (x, y), 'score': score, 'lives': lives}}
        self.enemies = []  # [{'type': type, 'position': (x, y), 'id': id}]
        self.bullets = []  # [{'position': (x, y), 'velocity': (vx, vy), 'owner': player_id}]
        self.game_status = 'waiting'  # 'waiting', 'playing', 'paused', 'game_over'

class NetworkManager:
    def __init__(self, config, game_instance=None):
        self.config = config
        self.role = config.getint('NETWORK', 'ROLE')
        self.server_ip = config.get('NETWORK', 'SERVER_IP')
        self.server_port = config.getint('NETWORK', 'SERVER_PORT')
        self.game = game_instance
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('NetworkManager')
        
        # Initialize game state
        self.game_state = GameState()
        self.player_id = None
        
        # Initialize Socket.IO client
        self.sio = socketio.Client()
        self.setup_events()
        
        if self.role == 1:  # Host
            self.start_server()
        else:  # Client
            self.connect_to_server()

    def setup_events(self):
        @self.sio.event
        def connect():
            self.logger.info('Connected to server')
            if self.role == 2:  # Client
                self.sio.emit('join_game')

        @self.sio.event
        def disconnect():
            self.logger.info('Disconnected from server')
            if self.game:
                self.game.handle_disconnect()

        @self.sio.on('player_joined')
        def on_player_joined(data):
            self.player_id = data['player_id']
            self.logger.info(f'Joined game as player {self.player_id}')
            if self.game:
                self.game.handle_player_joined(data)

        @self.sio.on('player_update')
        def on_player_update(data):
            if self.game:
                player_id = data['player_id']
                position = Vector2(data['position']['x'], data['position']['y'])
                velocity = Vector2(data['velocity']['x'], data['velocity']['y'])
                self.game.update_remote_player(player_id, position, velocity)

        @self.sio.on('game_state')
        def on_game_state(data):
            self.game_state = self.deserialize_game_state(data)
            if self.game:
                self.game.sync_game_state(self.game_state)

        @self.sio.on('player_shoot')
        def on_player_shoot(data):
            if self.game:
                player_id = data['player_id']
                position = Vector2(data['position']['x'], data['position']['y'])
                self.game.handle_remote_shoot(player_id, position)

        @self.sio.on('enemy_destroyed')
        def on_enemy_destroyed(data):
            if self.game:
                enemy_id = data['enemy_id']
                player_id = data['player_id']
                score = data['score']
                self.game.handle_enemy_destroyed(enemy_id, player_id, score)

    def start_server(self):
        server = socketio.Server()
        app = socketio.WSGIApp(server)
        
        @server.event
        def connect(sid, environ):
            self.logger.info(f'Client connected: {sid}')

        @server.event
        def join_game(sid):
            player_id = len(self.game_state.players) + 1
            self.game_state.players[player_id] = {
                'position': (400, 500),
                'score': 0,
                'lives': 3
            }
            server.emit('player_joined', {'player_id': player_id}, room=sid)
            server.emit('game_state', self.serialize_game_state(), skip_sid=sid)

        @server.event
        def player_update(sid, data):
            server.emit('player_update', data, skip_sid=sid)
            if self.game_state.players.get(data['player_id']):
                self.game_state.players[data['player_id']]['position'] = (
                    data['position']['x'],
                    data['position']['y']
                )

        @server.event
        def player_shoot(sid, data):
            server.emit('player_shoot', data, skip_sid=sid)
            self.game_state.bullets.append({
                'position': (data['position']['x'], data['position']['y']),
                'velocity': (0, -10),
                'owner': data['player_id']
            })

        @server.event
        def enemy_destroyed(sid, data):
            server.emit('enemy_destroyed', data)
            if self.game_state.players.get(data['player_id']):
                self.game_state.players[data['player_id']]['score'] += data['score']
        
        def run_server():
            eventlet.wsgi.server(eventlet.listen((self.server_ip, self.server_port)), app)
        
        threading.Thread(target=run_server, daemon=True).start()
        self.sio.connect(f'http://{self.server_ip}:{self.server_port}')

    def connect_to_server(self):
        try:
            self.sio.connect(f'http://{self.server_ip}:{self.server_port}')
        except Exception as e:
            self.logger.error(f"Failed to connect to server: {e}")
            if self.game:
                self.game.handle_connection_error(str(e))

    def send_player_update(self, position, velocity):
        if self.sio.connected and self.player_id:
            data = {
                'player_id': self.player_id,
                'position': {'x': position.x, 'y': position.y},
                'velocity': {'x': velocity.x, 'y': velocity.y}
            }
            self.sio.emit('player_update', data)

    def send_player_shoot(self, position):
        if self.sio.connected and self.player_id:
            data = {
                'player_id': self.player_id,
                'position': {'x': position.x, 'y': position.y}
            }
            self.sio.emit('player_shoot', data)

    def send_enemy_destroyed(self, enemy_id, score):
        if self.sio.connected and self.player_id:
            data = {
                'enemy_id': enemy_id,
                'player_id': self.player_id,
                'score': score
            }
            self.sio.emit('enemy_destroyed', data)

    def serialize_game_state(self):
        return {
            'players': self.game_state.players,
            'enemies': self.game_state.enemies,
            'bullets': self.game_state.bullets,
            'game_status': self.game_state.game_status
        }

    def deserialize_game_state(self, data):
        state = GameState()
        state.players = data['players']
        state.enemies = data['enemies']
        state.bullets = data['bullets']
        state.game_status = data['game_status']
        return state

    def update(self):
        # Periodic updates (if needed)
        pass

    def cleanup(self):
        if self.sio.connected:
            self.sio.disconnect()