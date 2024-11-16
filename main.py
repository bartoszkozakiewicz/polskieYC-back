from enum import Enum
from fastapi import FastAPI


class UserType(str, Enum):
    investors = "investors"
    academia = "academia"
    business = "business"


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/search/{user_type}")
async def get_model(user_type: UserType):
    if user_type is UserType.investors:
        return {"msg": "test"}

    elif user_type is UserType.academia:
        return {"msg": "test"}

    elif user_type is UserType.business:
        return {"msg": "test"}



