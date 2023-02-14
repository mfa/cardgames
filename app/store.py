import datetime
import json
import os

import redis.asyncio as redis


class Store:
    def __init__(self):
        self.r = redis.from_url(os.environ.get("REDIS_URL"))

    async def ping(self):
        return await self.r.ping()

    async def keys(self):
        return await self.r.keys()

    async def save(self, name, state):
        state["modified"] = datetime.datetime.utcnow().timestamp()
        return await self.r.set(f"game-{name}", json.dumps(state))

    async def load(self, name):
        game = await self.r.get(f"game-{name}")
        if game:
            return json.loads(game)
        return game
