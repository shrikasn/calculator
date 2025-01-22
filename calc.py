from unittest import result
from fastapi import FastAPI, HTTPException

app = FastAPI()

# Use a dictionary for operation count
app.state.operation_count = 0
app.state.operation_limit = 10


@app.post("/calculate/")
async def calculate(operation: str, num1: float, num2: float):
    if app.state.operation_count >= app.state.operation_limit:
        raise HTTPException(status_code=400, detail="Operation limit exceeded!")

    result = None
    if operation == "+":
        result = num1 + num2
    elif operation == "-":
        result = num1 - num2
    elif operation == "*":
        result = num1 * num2
    elif operation == "/":
        if num2 == 0:
            raise HTTPException(status_code=400, detail="Division by zero is not allowed!")
        result = num1 / num2
    else:
        raise HTTPException(status_code=400, detail="Invalid operation!")

    app.state.operation_count += 1

    return {
        "operation": operation,
        "num1": num1,
        "num2": num2,
        "result": result,
        "operation_count": app.state.operation_count,
    }


@app.get("/reset_operations/")
async def reset_operations():
    app.state.operation_count = 0
    return {"message": "Operation count reset successfully!"}


@app.get("/")
async def read_root():
    return {"message": "Calculator API is running!"}
