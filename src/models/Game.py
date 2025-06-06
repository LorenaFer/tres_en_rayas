"""
Modelo principal del juego que gestiona las salas y el estado global
"""

from models.Table import Table
import threading
import json

class Game:
    def __init__(self):
        self.tables = []
        self.table_id = 1
        self.lock = threading.Lock()  # Lock para sincronización
        
    def create_table(self):
        # Crea una nueva sala si hay menos de 50 salas disponibles 
        with self.lock:
            try:
                waiting_tables = [table for table in self.tables if len(table.players) < 2]
                if len(waiting_tables) < 50:
                    table = Table(self.table_id)
                    self.tables.append(table)
                    self.table_id += 1
                    table.start_thread()  # Inicia el hilo de la sala
                    return table
                return None
            except Exception as e:
                print(f"Error al crear sala: {str(e)}")
                return None

    def remove_table(self, table_id):
        # Elimina una sala del juego
        with self.lock:
            table = next((t for t in self.tables if t.id == table_id), None)
            if table:
                table.stop_thread()  # Detiene el hilo de la sala
                self.tables = [t for t in self.tables if t.id != table_id]

    def get_tables_info(self):
        #Obtiene información de todas las salas disponibles, excluyendo las finalizadas
        with self.lock:
            tables_info = []
            for table in self.tables:
                if table.winner is not None:
                    continue  # No mostrar salas finalizadas
                status = 'Esperando' if len(table.players) == 1 else \
                        'Jugando' if len(table.players) == 2 else \
                        'Disponible'
                tables_info.append({
                    'id': table.id,
                    'available': table.available,
                    'players': len(table.players),
                    'status': status
                })
            print(f"Información de salas: {tables_info}")  
            return tables_info

    def get_table(self, table_id):
        #Obtiene una sala específica por su ID
        with self.lock:
            return next((table for table in self.tables if table.id == table_id), None)

    def to_json(self):
        #Convierte el estado del juego a formato JSON
        with self.lock:
            return json.dumps({
                'tables': self.get_tables_info()
            })

    def remove_finished_tables(self):
        #Elimina todas las salas que ya han finalizado
        with self.lock:
            self.tables = [table for table in self.tables if table.winner is None]