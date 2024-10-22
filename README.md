# Snake Multiplayer Game API

This project is a simple API server built with FastAPI for a multiplayer Snake game.


## Requirements

- Python 3.10+
- FastAPI

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/raphaelpra/snake-api.git
   cd snake-api
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the server:
   ```
   uvicorn main:app --reload
   ```

2. Connect to the WebSocket endpoint at `ws://localhost:8000/ws/{player_id}` to join the game.

## API Endpoints

- `WebSocket /ws/{player_id}`: WebSocket connection for real-time game updates
- `GET /game_state`: Get the current game state
- `POST /move`: Submit a move for a player

## Project Structure

- `main.py`: Contains the FastAPI application, WebSocket handling, and game logic

## Game Rules

- Players control snakes that move around the game board
- Snakes grow by eating food
- The game ends when a snake collides with another snake or the game boundaries

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

