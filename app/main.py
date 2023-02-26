import enum
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from fastapi import Cookie, FastAPI, Query, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .games.maumau import MauMau
from .names import new_name
from .store import Store

app = FastAPI()
store = Store()


templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def to_svg(value):
    value = value.replace("-", "_").lower()
    return f"white_{value}.svg"


templates.env.filters["to_svg"] = to_svg


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

    def serialize(self):
        return {k: v for k, v in self.__dict__.items() if k != "instance"}


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
                    store.set(name, "instance", g)
            return game
        return _game


@app.get("/new/{kind}")
@app.get("/new")
async def game_new(
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


@app.get("/games", response_class=HTMLResponse)
async def games(request: Request):
    all_games = [i.name for i in await store.keys()]
    active_games = {
        k: store.get(k, "instance") is not None for k in store.game_states.keys()
    }
    return templates.TemplateResponse(
        "games.html",
        {"request": request, "all_games": all_games, "active_games": active_games},
    )


@app.get("/{name}/start")
async def game_start(
    name: str, user_id: Union[str, None] = Cookie(default=create_user())
):
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
async def game_join(
    name: str, user_id: Union[str, None] = Cookie(default=create_user())
):
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
async def game_index(
    name,
    request: Request,
    response: Response,
    action: Union[str, None] = None,
    card: Union[str, None] = None,
    user_id: Union[str, None] = Cookie(default=create_user()),
):
    game = await load_game(name)
    if game:
        if game.instance:
            r = {}
            if action:
                r = game.instance.action(action=action, card=card, player_id=user_id)
                await store.save(name, game)

            return templates.TemplateResponse(
                "game_state.html",
                {
                    "request": request,
                    "you": user_id,
                    "state": game.instance.status(user_id),
                    "name": name,
                    "msg": r.get("msg", ""),
                },
            )

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
    "/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static"
)
app.mount(
    "/assets", StaticFiles(directory=Path(__file__).parent / "assets"), name="assets"
)
