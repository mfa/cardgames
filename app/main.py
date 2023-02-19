import uuid
from typing import Union

from fastapi import Cookie, FastAPI, Response
from fastapi.responses import HTMLResponse

from .names import new_name
from .store import Store

app = FastAPI()
store = Store()


def create_user():
    return str(uuid.uuid4())


@app.get("/new")
async def new(
    response: Response, user_id: Union[str, None] = Cookie(default=create_user())
):
    name = new_name()
    state = {"name": name, "players": [user_id]}
    await store.save(name, state)

    response.set_cookie(key="user_id", value=user_id)
    return HTMLResponse(
        "new game created - link to add other players: "
        + f'<a href="/join/{name}">{name}</a><br/> you are: {user_id}'
    )


@app.get("/join/{name}")
async def join(
    name, response: Response, user_id: Union[str, None] = Cookie(default=create_user())
):
    state = await store.load(name)
    if state:
        if user_id not in state["players"]:
            state["players"].append(user_id)
        await store.save(name, state)

        response.set_cookie(key="user_id", value=user_id)
        return HTMLResponse(
            f"{name} found, players: {state['players']}<br/> you are: {user_id}"
        )
    return "game not found"


@app.get("/games")
async def games():
    games = [i.name for i in await store.keys()]
    return HTMLResponse(
        "games found:<br/><ul><li>"
        + "<li>".join([f'<a href="/{i}">{i}</a>' for i in games])
        + '</ul><br/>create a <a href="/new">new game</a>'
    )


@app.get("/{name}")
async def update(
    name, response: Response, user_id: Union[str, None] = Cookie(default=create_user())
):
    state = await store.load(name)
    if state:
        if "counter" in state:
            state["counter"] += 1
        else:
            state["counter"] = 1
        await store.save(name, state)

        if user_id in state["players"]:
            user_msg = "you are in this game"
        else:
            user_msg = f'<br/><a href="/join/{name}">join this game</a>'

        return HTMLResponse(
            f"{name} found, players: {state['players']}<br/>"
            + f"counter: {state['counter']}, last_change: {state['modified']}<br/>"
            + user_msg
        )
    return "game not found"


@app.get("/")
async def index():
    return "nothing to see"
