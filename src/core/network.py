import socketio
import json
import threading

class NetworkManager:
    def __init__(self, config):
        self.config = config
        self.role = config.getint('NETWORK', 'ROLE')
        self.server_ip = config.get('NETWORK', 'SERVER_IP')
        self.server_port = config.getint('NETWORK', 'SERVER_PORT')
        
        self.sio = socketio.Client()
        self.setup_events()
        
        if self.role == 1:  # Host
            self.start_server()
        else:  # Client
            self.connect_to_server()

    def setup_events(self):
        @self.sio.event
        def connect():
            print('Connected to server')

        @self.sio.event
        def disconnect():
            print('Disconnected from server')

        @self.sio.on('player_update')
        def on_player_update(data):
            # TODO: Handle player position updates
            pass

        @self.sio.on('game_state')
        def on_game_state(data):
            # TODO: Handle game state updates
            pass

    def start_server(self):
        # Start server in a separate thread
        server = socketio.Server()
        app = socketio.WSGIApp(server)
        
        def run_server():
            import eventlet
            eventlet.wsgi.server(eventlet.listen((self.server_ip, self.server_port)), app)
        
        threading.Thread(target=run_server, daemon=True).start()
        
        # Connect to own server
        self.sio.connect(f'http://{self.server_ip}:{self.server_port}')

    def connect_to_server(self):
        try:
            self.sio.connect(f'http://{self.server_ip}:{self.server_port}')
        except Exception as e:
            print(f"Failed to connect to server: {e}")

    def send_player_update(self, position, velocity):
        if self.sio.connected:
            self.sio.emit('player_update', {
                'position': {'x': position.x, 'y': position.y},
                'velocity': {'x': velocity.x, 'y': velocity.y}
            })

    def send_game_state(self, state):
        if self.sio.connected:
            self.sio.emit('game_state', state)

    def update(self):
        # TODO: Implement any necessary periodic updates
        pass

    def cleanup(self):
        if self.sio.connected:
            self.sio.disconnect()