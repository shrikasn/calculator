from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from databases import Database
import sqlalchemy
from datetime import datetime
import os
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI()

# Database URL (ensure it's correct and properly URL-encoded)
DATABASE_URL = "mysql+aiomysql://root:Prasad@8@localhost/my_database"
database = Database(DATABASE_URL)

# SQLAlchemy setup
metadata = sqlalchemy.MetaData()

operations_table = sqlalchemy.Table(
    "operations",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("num1", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column("num2", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column("operator", sqlalchemy.String(10), nullable=False),
    sqlalchemy.Column("result", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column("operation_date", sqlalchemy.DateTime, nullable=False),
)

# Pydantic model for the calculation result
class CalculationResult(BaseModel):
    num1: float
    num2: float
    operator: str
    result: float

# Operation limit (default to 10 if not set)
operation_limit = int(os.getenv("OPERATION_LIMIT", 10))

@app.on_event("startup")
async def connect_to_db():
    """Connect to the database."""
    await database.connect()
    logger.info("Database connected.")

    # Create table if it doesn't exist
    query = """
    CREATE TABLE IF NOT EXISTS operations (
        id INT AUTO_INCREMENT PRIMARY KEY,
        num1 FLOAT NOT NULL,
        num2 FLOAT NOT NULL,
        operator VARCHAR(10) NOT NULL,
        result FLOAT NOT NULL,
        operation_date DATETIME NOT NULL
    );
    """
    try:
        await database.execute(query)
        logger.info("Table created or already exists.")
    except Exception as e:
        logger.error(f"Error during database setup: {e}")
        raise HTTPException(status_code=500, detail="Database setup failed.")

@app.on_event("shutdown")
async def disconnect_from_db():
    """Disconnect from the database."""
    await database.disconnect()
    logger.info("Database connection closed.")

@app.post("/calculate/", response_model=CalculationResult)
async def calculate(operator: str, num1: float, num2: float):
    """
    Perform a calculation and store the result in the database.
    Supports basic operations: +, -, *, /
    """
    try:
        # Get the current date (without time)
        today = datetime.now().date()

        # Check operation count for today
        query = """
        SELECT COUNT(*) 
        FROM operations 
        WHERE DATE(operation_date) = :today
        """
        operation_count = await database.fetch_val(query, values={"today": today})

        if operation_count >= operation_limit:
            raise HTTPException(status_code=400, detail="Operation limit exceeded for today!")

        # Perform the calculation based on the operator
        if operator == "+":
            result = num1 + num2
        elif operator == "-":
            result = num1 - num2
        elif operator == "*":
            result = num1 * num2
        elif operator == "/":
            if num2 == 0:
                raise HTTPException(status_code=400, detail="Division by zero is not allowed!")
            result = num1 / num2
        else:
            raise HTTPException(status_code=400, detail="Invalid operator!")

        # Insert the operation into the database
        query = operations_table.insert().values(
            num1=num1,
            num2=num2,
            operator=operator,
            result=result,
            operation_date=datetime.now()  # Storing the complete timestamp
        )
        await database.execute(query)

        return CalculationResult(num1=num1, num2=num2, operator=operator, result=result)

    except Exception as e:
        logger.error(f"Error during calculation: {e}")
        raise HTTPException(status_code=500, detail="Calculation failed due to an internal error.")

@app.get("/")
async def read_root():
    """
    Root endpoint to verify the API is running.
    """
    return {"message": "Calculator API with database is running and ready!"}
