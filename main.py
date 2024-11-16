from enum import Enum
from fastapi import FastAPI


class UserType(str, Enum):
    investors = "investors"
    academia = "academia"
    business = "business"


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "root"}


@app.get("/test")
async def test():
    return {"message": "Hello World"}


@app.get("/search/{user_type}")
async def search(user_type: UserType):
    if user_type is UserType.investors:
        return {"message": "investors"}

    elif user_type is UserType.academia:
        return {"message": "academia"}

    elif user_type is UserType.business:
        return {"message": "business"}
