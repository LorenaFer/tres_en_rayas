"""
Servidor del juego Tres en Raya que gestiona las conexiones y el estado del juego.
"""

import asyncio
import websockets
import json
#import threading
from models.Game import Game

class GameServer:
    def __init__(self, host='127.0.0.1', port=8765):
        self.host = host
        self.port = port
        self.game = Game()
        self.clients = {}  # {websocket: {'player_id': str, 'table_id': int}}

    async def handle_client(self, websocket, path):
        #Maneja la conexión de un cliente
        client_id = str(websocket)
        self.clients[websocket] = {'player_id': client_id, 'table_id': None}
        
        try:
            async for message in websocket:
                await self.process_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            print(f"Cliente desconectado: {client_id}")
        finally:
            await self.handle_disconnect(websocket)

    async def process_message(self, websocket, message):
        #Procesa los mensajes recibidos de los clientes
        try:
            data = json.loads(message)
            command = data.get('command')
            
            if command == 'CREATE_TABLE':
                await self.handle_create_table(websocket)
            elif command == 'JOIN_TABLE':
                table_id = data.get('table_id')
                await self.handle_join_table(websocket, table_id)
            elif command == 'MAKE_MOVE':
                table_id = data.get('table_id')
                position = data.get('position')
                await self.handle_make_move(websocket, table_id, position)
            elif command == 'GET_TABLES':
                await self.send_tables_info(websocket)
        except json.JSONDecodeError:
            print(f"Error al decodificar mensaje: {message}")

    async def handle_create_table(self, websocket):
        #Maneja la creación de una nueva sala
        table = self.game.create_table()
        if table:
            await self.handle_join_table(websocket, table.id)
            # Notificar a todos los clientes sobre la nueva sala
            await self.broadcast_tables_update()
        else:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'No se pueden crear más salas en este momento.'
            }))

    async def handle_join_table(self, websocket, table_id):
        #Maneja la unión de un jugador a una sala
        table = self.game.get_table(table_id)
        if not table:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Sala no encontrada.'
            }))
            return

        client_id = self.clients[websocket]['player_id']
        if table.add_player(client_id, websocket):
            self.clients[websocket]['table_id'] = table_id
            
            # Notificar al jugador que se unió
            await websocket.send(json.dumps({
                'type': 'table_joined',
                'table': table.get_state()
            }))

            # Notificar a todos los jugadores de la sala
            await self.broadcast_table_state(table)
            
            # Notificar a todos los clientes sobre el cambio en las salas
            await self.broadcast_tables_update()

            # Si la sala está llena, iniciar el juego
            if len(table.players) == 2:
                await self.broadcast_game_start(table)
        else:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'No se puede unir a esta sala.'
            }))

    async def handle_make_move(self, websocket, table_id, position):
        #Maneja un movimiento en el juego, solo permite marcar al jugador correcto en su turno
        try:
            table = self.game.get_table(table_id)
            if not table:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Sala no encontrada.'
                }))
                return

            client_id = self.clients[websocket]['player_id']
            if client_id not in table.players:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'No eres un jugador de esta sala.'
                }))
                return

            if table.make_move(position, client_id):
                await self.broadcast_table_state(table)
                
                if table.winner:
                    await self.broadcast_game_end(table)
                    # Notificar a todos los clientes sobre el cambio en las salas
                    await self.broadcast_tables_update()
                    # Eliminar salas finalizadas
                    self.game.remove_finished_tables()
            else:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Movimiento inválido o no es tu turno.'
                }))
        except Exception as e:
            print(f"Error al procesar movimiento: {str(e)}")  # Debug
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Error al procesar el movimiento.'
            }))

    async def handle_disconnect(self, websocket):
        #Maneja la desconexión de un cliente
        if websocket in self.clients:
            client_info = self.clients[websocket]
            table_id = client_info['table_id']
            
            if table_id:
                table = self.game.get_table(table_id)
                if table:
                    table.remove_player(client_info['player_id'])
                    await self.broadcast_table_state(table)
                    
                    if len(table.players) == 0:
                        self.game.remove_table(table_id)
            
            del self.clients[websocket]

    async def broadcast_table_state(self, table):
        #Envía el estado actual de la sala a todos sus jugadores."""
        state = table.get_state()
        for player_id in table.players:
            websocket = table.player_sockets[player_id]
            await websocket.send(json.dumps({
                'type': 'table_state',
                'table': state
            }))

    async def broadcast_game_start(self, table):
        #Notifica a los jugadores que el juego ha comenzado
        for player_id in table.players:
            websocket = table.player_sockets[player_id]
            await websocket.send(json.dumps({
                'type': 'game_start',
                'table': table.get_state()
            }))

    async def broadcast_game_end(self, table):
        #Notifica a los jugadores que el juego ha terminado
        for player_id in table.players:
            websocket = table.player_sockets[player_id]
            await websocket.send(json.dumps({
                'type': 'game_end',
                'table': table.get_state()
            }))

    async def send_tables_info(self, websocket):
        #Envía la información de las salas disponibles a un cliente
        await websocket.send(json.dumps({
            'type': 'tables',
            'tables': self.game.get_tables_info()
        }))

    async def broadcast_tables_update(self):
        #Notifica a todos los clientes sobre cambios en las salas
        tables_info = self.game.get_tables_info()
        for websocket in self.clients:
            try:
                await websocket.send(json.dumps({
                    'type': 'tables',
                    'tables': tables_info
                }))
            except websockets.exceptions.ConnectionClosed:
                continue

    async def start(self):
        #Inicia el servidor
        async with websockets.serve(self.handle_client, self.host, self.port):
            print(f"Servidor iniciado en ws://{self.host}:{self.port}")
            await asyncio.Future()  # Mantener el servidor en ejecución

if __name__ == '__main__':
    server = GameServer()
    asyncio.run(server.start()) 