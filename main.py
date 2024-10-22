
from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Field, Session, SQLModel, create_engine, select
from typing import List, Optional
from typing_extensions import Annotated

# Define the SQLModel
class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str

# Create the database engine
DATABASE_URL = "sqlite:///database.db"
engine = create_engine(DATABASE_URL)

# Create tables
SQLModel.metadata.create_all(engine)

app = FastAPI()

# Dependency to get DB session
def get_session():
    with Session(engine) as session:
        yield session

@app.post("/items/", response_model=Item)
def create_item(item: Item, session: Annotated[Session, Depends(get_session)]):
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@app.get("/items/", response_model=List[Item])
def read_items(session: Annotated[Session, Depends(get_session)]):
    items = session.exec(select(Item)).all()
    return items

@app.get("/items/{item_id}", response_model=Item)
def read_item(item_id: int, session: Annotated[Session, Depends(get_session)]):
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, item_update: Item, session: Annotated[Session, Depends(get_session)]):
    db_item = session.get(Item, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item_data = item_update.dict(exclude_unset=True)
    for key, value in item_data.items():
        setattr(db_item, key, value)
    
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

@app.delete("/items/{item_id}", response_model=dict)
def delete_item(item_id: int, session: Annotated[Session, Depends(get_session)]):
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    session.delete(item)
    session.commit()
    return {"message": "Item deleted successfully"}
