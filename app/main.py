import enum
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from fastapi import Cookie, FastAPI, Query, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .games.maumau import MauMau
from .names import new_name
from .store import Store

app = FastAPI()
store = Store()


def create_user():
    return str(uuid.uuid4())


class GameKind(str, enum.Enum):
    maumau: str = "maumau"


@dataclass
class Game:
    name: str
    players: list[str]
    kind: GameKind
    host: str
    state: Optional[dict] = None
    instance: Optional[Union[MauMau]] = None
    modified: Optional[str] = None


async def load_game(name: str):
    _game = await store.load(name)
    if _game:
        if isinstance(_game, dict):
            game = Game(**_game)
            if game.state and not game.instance:
                if game.kind == "maumau":
                    print(f"create new game instance: {name}")
                    g = MauMau(game.name, game.players)
                    g.load(game.state)
                    game.instance = g
                    # maybe unsafe!
                    store.game_states[name] = game
            return game
        return _game


@app.get("/new/{kind}")
@app.get("/new")
async def new(
    kind: Optional[GameKind] = Query(None),
    user_id: Union[str, None] = Cookie(default=create_user()),
):
    name = new_name()
    kind = kind if kind else GameKind.maumau
    game = Game(name=name, players=[user_id], kind=kind, host=user_id)
    await store.save(name, game)

    response = HTMLResponse(
        "new game created - link to add other players: "
        + f'<a href="/{name}/join">{name}</a><br/> you are: {user_id}<br/>Kind of game: {kind}'
    )
    response.set_cookie(key="user_id", value=user_id)
    return response


@app.get("/games")
async def games():
    all_games = [i.name for i in await store.keys()]
    active_games = [(k, hasattr(v, "instance")) for k, v in store.game_states.items()]
    return HTMLResponse(
        "games found:<br/><ul><li>"
        + "<li>".join([f'<a href="/{i}">{i}</a>' for i in all_games])
        + "</ul>active games:<ul><li>"
        + "<li>".join([f'<a href="/{i}">{i}</a> (started: {j})' for i, j in active_games])
        + '</ul><br/>create a <a href="/new">new game</a>'
    )


@app.get("/{name}/start")
async def start(name: str, user_id: Union[str, None] = Cookie(default=create_user())):
    game = await load_game(name)
    if game:
        if user_id == game.host:
            if game.instance:
                return "game already started"
            if len(game.players) < 2:
                return "not enough players to start game"
            if game.kind == "maumau":
                game.instance = MauMau(game.name, game.players)
            else:
                return "only maumau supported atm"
        await store.save(name, game)

        response = HTMLResponse(
            f"{name} found, players: {game.players}<br/> you are: {user_id}<br/>game started"
        )
        response.set_cookie(key="user_id", value=user_id)
        return response
    return "game not found"


@app.get("/{name}/join")
async def join(name: str, user_id: Union[str, None] = Cookie(default=create_user())):
    game = await load_game(name)
    if game:
        if game.instance:
            return "game already started"

        if user_id not in game.players:
            game.players.append(user_id)
        await store.save(name, game)

        response = HTMLResponse(
            f"{name} found, players: {game.players}<br/> you are: {user_id}"
        )
        response.set_cookie(key="user_id", value=user_id)
        return response
    return "game not found"


@app.get("/{name}")
async def update(
    name, response: Response, user_id: Union[str, None] = Cookie(default=create_user())
):
    game = await load_game(name)
    if game:
        # await store.save(name, game)

        if game.instance:
            return game.instance.status(user_id)

        if user_id in game.players:
            user_msg = "you are in this game"
        else:
            user_msg = f'<br/><a href="/{name}/join">join this game</a>'
        if user_id == game.host:
            user_msg = f'<br/>you are game host, do you want to <a href="/{name}/start">start this game</a>'

        return HTMLResponse(
            f"{name} found, players: {game.players}<br/>"
            + f"last_change: {game.modified}<br/>"
            + user_msg
        )
    return "game not found"


@app.get("/")
async def index():
    return "nothing to see"


app.mount(
    "/assets", StaticFiles(directory=Path(__file__).parent / "assets"), name="assets"
)
