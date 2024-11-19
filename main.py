from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from sqlmodel import Session
from fastapi_utils.tasks import repeat_every
import uvicorn

from model import Game, Player, create_new_snake, create_db_and_tables, get_game, get_player, get_session, Direction, move_all_game, engine

create_db_and_tables()

app = FastAPI()

class GameSchema(BaseModel):
    name: Annotated[str, Field(example="Game Name")]
    slug: Annotated[str, Field(example="game-slug")]

    class Config:
        from_attributes = True

class SnakePositionSchema(BaseModel):
    x: Annotated[int, Field(description="The x coordinate of the snake position")]
    y: Annotated[int, Field(description="The y coordinate of the snake position")]
    created_at: Annotated[datetime, Field(description="The created at date of the snake position")]

class CreatePlayerSchema(BaseModel):
    direction: Annotated[Direction, Field(example="UP", description="The direction the player is facing", default=Direction.UP)]
    name: Annotated[str, Field(example="Player Name")]
    color: Annotated[str, Field(example="#000000")]

    class Config:
        from_attributes = True

class PlayerSchema(CreatePlayerSchema):
    id: Annotated[int, Field(description="The ID of the player")]

class PlayerWithSnakeSchema(PlayerSchema):
    positions: list[SnakePositionSchema] = []

class GameWithPlayersSchema(GameSchema):
    players: list[PlayerWithSnakeSchema] = []


@app.post("/game", response_model=GameSchema)
def create_game(game: GameSchema, session: Annotated[Session, Depends(get_session)]):
    if get_game(game.slug, session) is not None:
        raise HTTPException(status_code=400, detail="Game already exists for this slug")
    
    new_game = Game.model_validate(game)
    session.add(new_game)
    session.commit()
    session.refresh(new_game)
    return new_game

@app.post("/game/{slug}/register", response_model=GameWithPlayersSchema)
def register_player(slug: str, player: CreatePlayerSchema, session: Annotated[Session, Depends(get_session)]):
    game = get_game(slug, session)

    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    
    player_data = player.model_dump()
    player_data["game_id"] = game.id
    new_player = Player.model_validate(player_data)
    session.add(new_player)

    create_new_snake(new_player, session)

    session.commit()
    session.refresh(new_player)
    return new_player.game

@app.get("/game/{slug}", response_model=GameWithPlayersSchema)
def show_game(slug: str, session: Annotated[Session, Depends(get_session)]):
    game = get_game(slug, session)

    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return game

@app.patch("/player/{id}", response_model=PlayerSchema)
def update_player(id: int, direction: Direction, session: Annotated[Session, Depends(get_session)]):
    player = get_player(id, session)

    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player.direction = direction
    session.add(player)
    session.commit()
    session.refresh(player)
    return player

@app.on_event("startup")
@repeat_every(seconds=5, raise_exceptions=True)
def tick() -> None:
    print("tick")
    with Session(bind=engine) as session:
        move_all_game(session)
        session.commit()

if __name__ == '__main__':
    uvicorn.run(app)
