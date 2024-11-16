from typing import Optional
from neo4j import AsyncDriver, AsyncGraphDatabase

class Neo4jService:
    def __init__(self, url: str, user: str, password: str, database_name: str):
        self.url = url
        self.user = user
        self.password = password
        self.database_name = database_name
        self.driver: Optional[AsyncDriver] = None

    def open(self):
        self.driver = AsyncGraphDatabase.driver(self.url, auth=(self.user, self.password))

    async def close(self):
        await self.driver.close()