# Tres en Raya - Juego Multijugador

Este es un juego de Tres en Raya multijugador implementado en Python que permite a los jugadores crear salas y jugar entre sí a través de una interfaz gráfica.

## Requisitos

- Python 3.8 o superior
- Las dependencias listadas en `requirements.txt`

## Instalación

1. Clona este repositorio:
```bash
git clone <url-del-repositorio>
cd tres_en_raya
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Ejecución

1. Inicia el servidor:
```bash
python src/server.py
```

2. Inicia el cliente (en una nueva terminal):
```bash
python src/client.py
```

## Características

- Interfaz gráfica intuitiva
- Creación y unión a salas de juego
- Soporte para múltiples partidas simultáneas
- Sistema de turnos
- Detección automática de victoria/empate
- Notificaciones

## Estructura del Proyecto

```
tres_en_raya/
├── src/
│   ├── models/
│   │   ├── Game.py
│   │   └── Table.py
│   ├── templates/
│   │   └── index.html
│   ├── server.py
│   └── client.py
├── requirements.txt
└── README.md
```

## Notas

- El servidor debe estar ejecutándose antes de iniciar cualquier cliente
- Por defecto, el servidor se ejecuta en localhost (127.0.0.1)
- Cada sala puede albergar 2 jugadores 