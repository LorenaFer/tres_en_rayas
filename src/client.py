"""
Cliente del juego Tres en Raya con interfaz gráfica.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import websockets
import json
import threading
import queue

class GameClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Tres en Raya")
        self.root.geometry("800x600")
        self.root.configure(bg='#2C3E50')
        
        # Configurar estilos
        self.style = ttk.Style()

        
        self.websocket = None
        self.current_table = None
        self.message_queue = queue.Queue()
        
        # Iniciar el bucle de eventos de asyncio en un hilo separado
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.run_async_loop, daemon=True).start()
        
        # Crear frames para diferentes pantallas
        self.lobby_frame = ttk.Frame(self.root)
        self.game_frame = ttk.Frame(self.root)
        
        self.setup_lobby()
        self.setup_game()
        
        # Mostrar el home inicialmente
        self.show_lobby()
        
        self.connect_to_server()
        self.root.after(100, self.process_messages)
        
    def setup_lobby(self):
        """Configura la interfaz del home"""
        # Limpiar el frame anterior
        for widget in self.lobby_frame.winfo_children():
            widget.destroy()

        # Fondo blanco
        self.lobby_frame.configure(style='Modern.TFrame')
        self.style.configure('Modern.TFrame', background='white')
        self.style.configure('Modern.TLabel', background='white', foreground='#2A8682', font=('Helvetica', 18, 'bold'))
        self.style.configure('Modern.TButton', font=('Helvetica', 12), padding=10, foreground='#2A8682')
        self.style.configure('Modern.Treeview', background='white', foreground='black', fieldbackground='#e8f0f7', rowheight=32, font=('Helvetica', 12))
        self.style.configure('Modern.Treeview.Heading', background='#2A8682', foreground='white', font=('Helvetica', 13, 'bold'))

        # Título
        title_label = ttk.Label(self.lobby_frame, text="Tres en Raya", style='Modern.TLabel', anchor='center')
        title_label.pack(pady=(40, 20))

        # Frame para la tabla de salas
        tables_frame = ttk.Frame(self.lobby_frame, style='Modern.TFrame')
        tables_frame.pack(pady=10, padx=20, fill='x', expand=True)

        
        self.tables_tree = ttk.Treeview(tables_frame, columns=("id", "status", "players"), show="headings", height=6, style='Modern.Treeview')
        self.tables_tree.heading("id", text="ID")
        self.tables_tree.heading("status", text="Estado")
        self.tables_tree.heading("players", text="Jugadores")
        self.tables_tree.column("id", width=60, anchor="center")
        self.tables_tree.column("status", width=120, anchor="center")
        self.tables_tree.column("players", width=120, anchor="center")
        self.tables_tree.pack(side='left', fill='both', expand=True)

        
        scrollbar = ttk.Scrollbar(tables_frame, orient="vertical", command=self.tables_tree.yview)
        self.tables_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        
        control_frame = ttk.Frame(self.lobby_frame, style='Modern.TFrame')
        control_frame.pack(pady=30)

        self.create_table_btn = tk.Button(
            control_frame, text="Crear Sala",
            font=('Helvetica', 12, 'bold'),
            bg='#2A8682', fg='white', activebackground='#e8f0f7', activeforeground='#2A8682',
            relief='solid', bd=0, highlightthickness=0, cursor='hand2',
            command=self.create_table
        )
        self.create_table_btn.grid(row=0, column=0, padx=10, ipadx=10, ipady=5)

        self.join_table_btn = tk.Button(
            control_frame, text="Unirse a Sala",
            font=('Helvetica', 12, 'bold'),
            bg='#2A8682', fg='white', activebackground='#e8f0f7', activeforeground='#2A8682',
            relief='solid', bd=0, highlightthickness=0, cursor='hand2',
            command=self.join_selected_table
        )
        self.join_table_btn.grid(row=0, column=1, padx=10, ipadx=10, ipady=5)

        self.refresh_btn = tk.Button(
            control_frame, text="Actualizar",
            font=('Helvetica', 12, 'bold'),
            bg='#2A8682', fg='white', activebackground='#e8f0f7', activeforeground='#2A8682',
            relief='solid', bd=0, highlightthickness=0, cursor='hand2',
            command=self.refresh_tables
        )
        self.refresh_btn.grid(row=0, column=2, padx=10, ipadx=10, ipady=5)

        
        self.status_label = ttk.Label(
            self.lobby_frame,
            text="Conectando al servidor...",
            style='Modern.TLabel',
            anchor='center',
            font=('Helvetica', 14)
        )
        self.status_label.pack(pady=(30, 10))

        self.lobby_frame.pack_propagate(False)
        self.lobby_frame.pack(fill='both', expand=True)
        
    def setup_game(self):
        """Configura la interfaz del juego"""
        # Limpiar el frame anterior
        for widget in self.game_frame.winfo_children():
            widget.destroy()

        # Fondo blanco
        self.game_frame.configure(style='Modern.TFrame')

        # Indicador de turno
        self.table_info_label = ttk.Label(
            self.game_frame,
            text="",
            style='Modern.TLabel',
            anchor='center',
            font=('Helvetica', 18, 'bold')
        )
        self.table_info_label.pack(pady=(40, 10))

        # Tablero
        board_frame = tk.Frame(self.game_frame, bg='white')
        board_frame.pack(pady=10)

        self.board_buttons = []
        for i in range(3):
            for j in range(3):
                btn = tk.Button(
                    board_frame,
                    text="",
                    width=5,
                    height=2,
                    font=('Helvetica', 32, 'bold'),
                    bg='#e8f0f7',
                    fg='#222',
                    activebackground='#b5d0e6',
                    relief='flat',
                    bd=0,
                    highlightthickness=0,
                    cursor='hand2',
                    command=lambda x=i*3+j: self.make_move(x)
                )
                btn.grid(row=i, column=j, padx=10, pady=10, ipadx=10, ipady=10)
                btn.configure(overrelief='ridge')
                self.board_buttons.append(btn)

        # Estado del juego
        self.game_status_label = ttk.Label(
            self.game_frame,
            text="",
            style='Modern.TLabel',
            anchor='center',
            font=('Helvetica', 16)
        )
        self.game_status_label.pack(pady=(20, 10))


        # Botón "Volver al Home" 
        self.back_home_btn = tk.Button(
            self.game_frame,
            text="Volver Al Home",
            font=('Helvetica', 14, 'bold'),
            bg='#2A8682',
            fg='white',
            activebackground='#e8f0f7',
            activeforeground='#222',
            relief='solid',
            bd=0,
            highlightthickness=0,
            cursor='hand2',
            command=self.show_lobby
        )
        self.back_home_btn.pack(pady=(10, 30), ipadx=20, ipady=5)

    
        self.game_frame.pack_propagate(False)
        self.game_frame.pack(fill='both', expand=True)
    
    def connect_to_server(self):
        #Conecta al servidor WebSocket
        async def connect():
            try:
                self.websocket = await websockets.connect('ws://127.0.0.1:8765')
                self.message_queue.put(('status', 'Conectado al servidor'))
                await self.refresh_tables_async()
                
                # Iniciar el bucle de recepción de mensajes
                while True:
                    try:
                        message = await self.websocket.recv()
                        data = json.loads(message)
                        print(f"Mensaje recibido: {data}")  
                        
                        if data.get('type') == 'error':
                            self.message_queue.put(('error', data['message']))
                        elif data.get('type') == 'table_joined':
                            self.message_queue.put(('game_state', data['table']))
                        elif data.get('type') == 'tables':
                            self.message_queue.put(('tables', data['tables']))
                        elif data.get('type') == 'table_state':
                            self.message_queue.put(('game_state', data['table']))
                        elif data.get('type') == 'game_start':
                            self.message_queue.put(('game_state', data['table']))
                        elif data.get('type') == 'game_end':
                            self.message_queue.put(('game_state', data['table']))
                    except websockets.exceptions.ConnectionClosed:
                        self.message_queue.put(('error', 'Conexión con el servidor cerrada'))
                        break
                    except json.JSONDecodeError:
                        self.message_queue.put(('error', 'Error al decodificar mensaje del servidor'))
                        
            except Exception as e:
                self.message_queue.put(('error', f'Error de conexión: {str(e)}'))
        
        asyncio.run_coroutine_threadsafe(connect(), self.loop)
    
    def run_async_loop(self):
        #Ejecuta el bucle de eventos de asyncio
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
    
    def process_messages(self):
        #Procesa los mensajes de la cola
        try:
            while True:
                msg_type, msg_data = self.message_queue.get_nowait()
                if msg_type == 'status':
                    self.status_label.config(text=msg_data)
                elif msg_type == 'error':
                    self.show_custom_popup("Error", msg_data)
                elif msg_type == 'tables':
                    self.update_tables_list(msg_data)
                elif msg_type == 'game_state':
                    self.update_game_state(msg_data)
                elif msg_type == 'info':
                    self.show_custom_popup("Aviso", msg_data)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_messages)
    
    async def refresh_tables_async(self):
        #Actualiza la lista de salas desde el servidor
        if self.websocket:
            await self.websocket.send(json.dumps({'command': 'GET_TABLES'}))
    
    def refresh_tables(self):
        #Actualiza la lista de salas
        asyncio.run_coroutine_threadsafe(self.refresh_tables_async(), self.loop)
    
    def create_table(self):
        #Crea una nueva sala
        if self.websocket:
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(json.dumps({'command': 'CREATE_TABLE'})),
                self.loop
            )
    
    def join_table(self, table_id):
        #Une al jugador a una sala seleccionada
        if self.websocket:
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(json.dumps({
                    'command': 'JOIN_TABLE',
                    'table_id': table_id
                })),
                self.loop
            )
    
    def make_move(self, position):
        #Realiza un movimiento en el tablero
        if self.websocket and self.current_table:
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(json.dumps({
                    'command': 'MAKE_MOVE',
                    'table_id': self.current_table,
                    'position': position
                })),
                self.loop
            )
    
    def update_tables_list(self, tables):
        #Actualiza la lista de salas en la interfaz
        for item in self.tables_tree.get_children():
            self.tables_tree.delete(item)
        
        for table in tables:
            self.tables_tree.insert('', 'end', values=(
                table['id'],
                table['status'],
                f"{table['players']}/2"
            ))
    
    def update_game_state(self, state):
        #Actualiza el estado del juego en la interfaz
        try:
            self.current_table = state['id']
            self.table_info_label.config(text=f"Sala {state['id']} - Turno: {state['turn']}")
            
            # Actualizar el tablero
            for i, cell in enumerate(state['board']):
                self.board_buttons[i].config(
                    text=cell,
                    state='normal' if cell == ' ' and not state.get('winner') else 'disabled'
                )
            
            # Actualizar el estado
            if state.get('winner'):
                if state['winner'] == 'Draw':
                    self.game_status_label.config(text="¡Empate! | Finalizado")
                else:
                    self.game_status_label.config(text=f"¡Ganador: {state['winner']}! | Finalizado")
            else:
                self.game_status_label.config(text=f"Turno de: {state['turn']}")
            
            self.show_game()
        except Exception as e:
            print(f"Error al actualizar estado del juego: {str(e)}")  
    
    def show_lobby(self):
        #Muestra la pantalla del Home
        self.game_frame.pack_forget()
        self.lobby_frame.pack(fill='both', expand=True)
    
    def show_game(self):
        #Muestra la pantalla del juego
        self.lobby_frame.pack_forget()
        self.game_frame.pack(fill='both', expand=True)
    
    def join_selected_table(self):
        #Une al jugador a la sala seleccionada desde el home
        selection = self.tables_tree.selection()
        if selection:
            table_id = self.tables_tree.item(selection[0])['values'][0]
            self.join_table(table_id)
        else:
            self.show_custom_popup("Aviso", "Por favor, selecciona una sala")
    
    
    def show_custom_popup(self, title, message):
        #Muestra notificaciones 
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.configure(bg='#f8fafd')
        popup.attributes('-topmost', True)
        popup.geometry(f"400x120+{self.root.winfo_x()+200}+{self.root.winfo_y()+150}")
        popup.lift()
        popup.config(highlightbackground='#4da3ff', highlightthickness=2)

        
        def close():
            popup.destroy()

        # Barra superior
        bar = tk.Frame(popup, bg='#2A8682', height=32)
        bar.pack(fill='x', side='top')
        close_btn = tk.Button(bar, text='✕', font=('Helvetica', 14, 'bold'), bg='#f0f1f3', fg='#222', bd=0, relief='flat', command=close, activebackground='#e8f0f7', activeforeground='#222', cursor='hand2')
        close_btn.pack(side='right', padx=8, pady=4)
        title_lbl = tk.Label(bar, text=title, font=('Helvetica', 12, 'bold'), bg='#f0f1f3', fg='#222')
        title_lbl.pack(side='left', padx=12)

        # Línea separadora
        sep = tk.Frame(popup, bg='#dbeafe', height=2)
        sep.pack(fill='x')

        # Mensaje
        msg_lbl = tk.Label(
            popup,
            text=message,
            font=('Helvetica', 13, 'bold'),
            bg='#f8fafd',
            fg='#2A8682',
            wraplength=360,
            justify='left',
            anchor='w'
        )
        msg_lbl.pack(pady=(16, 0), padx=20, anchor='w')


    def run(self):
        #Inicia la aplicación
        self.root.mainloop()

if __name__ == '__main__':
    client = GameClient()
    client.run() 