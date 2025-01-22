from fastapi import FastAPI
from databases import Database
import sqlalchemy
from sqlalchemy import MetaData

app = FastAPI()
DATABASE_URL = "mysql+aiomysql://root:Prasad@8@localhost/my_database"
database = Database(DATABASE_URL)

metadata = MetaData()

items_table = sqlalchemy.Table(
    "items",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("name", sqlalchemy.String(255), nullable=False),
    sqlalchemy.Column("description", sqlalchemy.Text),
    sqlalchemy.Column("price", sqlalchemy.Numeric(10, 2)),
    sqlalchemy.Column("tax", sqlalchemy.Numeric(10, 2)),
)

@app.on_event("startup")
async def connect_to_db():
    await database.connect()

    create_table_query = """
    CREATE TABLE IF NOT EXISTS items (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        price DECIMAL(10, 2),
        tax DECIMAL(10, 2)
    );
    """

    await database.execute(create_table_query)

@app.on_event("shutdown")
async def disconnect_from_db():
    await database.disconnect()

@app.post("/add_item/")
async def add_item(name: str, description: str = None, price: int = 0, tax: int = 0):
    insert_query = """
    INSERT INTO items (name, description, price, tax)
    VALUES (:name, :description, :price, :tax);
    """

    await database.execute(insert_query, values={"name": name, "description": description, "price": price, "tax": tax})
    
    return {"message": "Item added successfully!"}

@app.get("/")
async def read_root():
    return {"message": "Connected to the database and table created!"}
