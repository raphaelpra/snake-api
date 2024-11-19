from datetime import datetime
import random
import enum
from typing import Optional
from sqlalchemy import Column, Enum
from sqlmodel import Field, SQLModel, Session, create_engine, Relationship, select
from collections import Counter

X_RANGE = 100
Y_RANGE = 100
PADDING = 10
SNAKE_INITIAL_LENGTH = 2

class Direction(str, enum.Enum):
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"

# Define the models first
class Game(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    slug: str = Field(index=True, unique=True)
    players: list["Player"] = Relationship(back_populates="game")

class Player(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    direction: Direction = Field(sa_column=Column(Enum(Direction)))
    name: str = Field(index=True)
    game_id: int = Field(foreign_key="game.id")
    game: Game = Relationship(back_populates="players")
    color: str = Field(index=True)
    positions: list["SnakePosition"] = Relationship(back_populates="player", sa_relationship_kwargs={"order_by": "desc(SnakePosition.created_at)"})
    
class SnakePosition(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.id")
    player: Player = Relationship(back_populates="positions")
    x: int = Field(index=True)
    y: int = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

def get_game(slug: str, session: Session) -> Game | None:
    return session.exec(select(Game).where(Game.slug == slug)).one_or_none()
        
def get_player(id: int, session: Session) -> Player | None:
    return session.exec(select(Player).where(Player.id == id)).one_or_none()


def move_position(x: int, y: int, direction: Direction) -> tuple[int, int]:
    if direction == Direction.UP:
        y -= 1
    elif direction == Direction.DOWN:
        y += 1
    elif direction == Direction.LEFT:
        x -= 1
    elif direction == Direction.RIGHT:
        x += 1

    return x, y

def create_new_snake(player: Player, session: Session):
    x = random.randint(PADDING, X_RANGE - PADDING)
    y = random.randint(PADDING, Y_RANGE - PADDING)

    positions = []
    for i in range(SNAKE_INITIAL_LENGTH, 0, -1):
        position = SnakePosition(x=x, y=y, player=player)
        positions.append(position)
        x, y = move_position(x, y, player.direction)

    session.add_all(positions)

def move_all_game(session: Session):
    games = session.exec(select(Game)).all()
    for game in games:
        remove_old_positions(game, session)
        generate_new_positions(game, session)

def remove_old_positions(game: Game, session: Session):
    """ 
    Remove the oldest position for each player as long as it has more than 1 positions
    """
    for player in game.players:
        positions = session.exec(select(SnakePosition).where(SnakePosition.player_id == player.id).order_by(SnakePosition.created_at.desc())).all()
        if len(positions) > 1:
            session.delete(positions[-1])

def generate_new_positions(game: Game, session: Session):
    """
    Get the new positions for each player
    """
    new_positions = []
    for player in game.players:
        x, y = move_position(player.positions[0].x, player.positions[0].y, player.direction)
        new_positions.append(SnakePosition(x=x, y=y, player=player))
    
    # Remove duplicate positions based on x,y coordinates
    position_by_coords = Counter()
    for position in new_positions:
        pos_tuple = (position.x, position.y)
        position_by_coords[pos_tuple] += 1

    new_positions = [position for position in new_positions if position_by_coords[pos_tuple] == 1]

    for position in new_positions:
        if can_create_position(game, position, session):
            session.add(position)

def can_create_position(game: Game, position: SnakePosition, session: Session):
    """
    Check if the position can be created
    """

    # Check if the position is within the bounds of the game
    if not 0 < position.x < X_RANGE or not 0 < position.y < Y_RANGE:
        return False
    
    # Check if the position is already occupied
    if session.exec(select(SnakePosition).where(SnakePosition.x == position.x, SnakePosition.y == position.y)).first() is not None:
        return False

    return True

if __name__ == "__main__":
    create_db_and_tables()
