"""
Modelo que representa una sala de juego individual.
"""

import threading
import json
import time  # Para simular la ejecución continua del hilo

class Table:
    def __init__(self, _id):
        self.id = _id
        self.game_board = [' ' for _ in range(9)]
        self.available = True
        self.players = []
        self.player_sockets = {}
        self.winner = None
        self.turn = 'X'
        self.lock = threading.Lock()  # Lock para sincronización
        self.running = False  # Indica si el hilo de la sala está activo
        self.thread = None  # Hilo de la sala

    def start_thread(self):
        """Inicia el hilo de la sala."""
        self.running = True
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def stop_thread(self):
        """Detiene el hilo de la sala."""
        self.running = False
        if self.thread:
            self.thread.join()

    def run(self):
        """Lógica que se ejecuta en el hilo de la sala."""
        while self.running:
            with self.lock:
                if self.winner:
                    self.running = False  # Detener el hilo si el juego ha terminado
            time.sleep(1)  # Simula un ciclo de ejecución
    
    def add_player(self, player_id, websocket):
        #Añade un jugador a la sala y almacena su WebSocket
        with self.lock:
            if len(self.players) < 2:
                self.players.append(player_id)
                self.player_sockets[player_id] = websocket
                
                # La sala se vuelve no disponible cuando está llena
                if len(self.players) == 2:
                    self.available = False
                return True
            return False

    def remove_player(self, player_id):
        #Elimina un jugador de la sala
        with self.lock:
            if player_id in self.players:
                self.players.remove(player_id)
                del self.player_sockets[player_id]
                self.available = True
                return True
            return False

    def make_move(self, index, player_id):
        #Permite marcar solo si es el turno del jugador correspondiente. Si solo hay un jugador, solo puede marcar X
        with self.lock:
            if 0 <= index < 9 and self.game_board[index] == ' ':
                # Determinar el símbolo del jugador
                if len(self.players) == 1:
                    # Solo hay un jugador, solo puede marcar X
                    if self.turn != 'X' or self.players[0] != player_id:
                        return False
                    symbol = 'X'
                else:
                    # Dos jugadores: el primero es X, el segundo es O
                    if self.players[0] == player_id and self.turn == 'X':
                        symbol = 'X'
                    elif self.players[1] == player_id and self.turn == 'O':
                        symbol = 'O'
                    else:
                        return False
                self.game_board[index] = symbol
                winner = self.check_winner()
                if winner:
                    self.winner = winner
                    self.available = False
                else:
                    self.turn = 'O' if self.turn == 'X' else 'X'
                return True
            return False

    def check_winner(self):
        #Verifica si hay un ganador y retorna 'X', 'O', o 'Draw'
        #Filas-Columnas-Diagonales
        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  
            [0, 3, 6], [1, 4, 7], [2, 5, 8], 
            [0, 4, 8], [2, 4, 6]              
        ]
        
        for combo in winning_combinations:
            if (self.game_board[combo[0]] == self.game_board[combo[1]] == 
                self.game_board[combo[2]] != ' '):
                return self.game_board[combo[0]]

        if ' ' not in self.game_board:
            return 'Draw'

        return None

    def get_state(self):
        #Obtiene el estado actual de la sala
        with self.lock:
            return {
                'id': self.id,
                'board': self.game_board,
                'turn': self.turn,
                'winner': self.winner,
                'players': len(self.players),
                'available': self.available
            }

    def to_json(self):
        #Convierte el estado de la sala a formato JSON
        with self.lock:
            return json.dumps(self.get_state())

    """def reset(self):
        #Reinicia el estado de la sala para una nueva partida.
        with self.lock:
            self.game_board = [' ' for _ in range(9)]
            self.available = True
            self.winner = None
            self.turn = 'X' """