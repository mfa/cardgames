import enum
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

from fastapi import (
    Cookie,
    FastAPI,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .games.maumau import MauMau
from .names import new_name
from .store import Store
from .utils import WebsocketConnectionManager, create_user, gen_templates

app = FastAPI()
store = Store()
ws_manager = WebsocketConnectionManager()
templates = gen_templates()


class GameKind(str, enum.Enum):
    maumau: str = "maumau"


@dataclass
class Game:
    name: str
    players: List[str]
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


@app.get("/games")
async def games(request: Request):
    all_games = [i.name for i in await store.keys()]
    active_games = {
        k: store.get(k, "instance") is not None for k in store.game_states.keys()
    }
    return templates.TemplateResponse(
        "games.html",
        {"request": request, "all_games": all_games, "active_games": active_games},
    )


@app.get("/new/{kind}")
@app.get("/new")
async def game_new(
    request: Request,
    kind: Optional[GameKind] = Query(None),
    user_id: Union[str, None] = Cookie(default=None),
):
    if not user_id:
        user_id = create_user()
    name = new_name()
    kind = kind if kind else GameKind.maumau
    game = Game(name=name, players=[user_id], kind=kind, host=user_id)
    await store.save(name, game)

    response = templates.TemplateResponse(
        "game_meta.html",
        {
            "request": request,
            "msg": "new game created",
            "user_id": user_id,
            "name": name,
            "game": game,
        },
    )
    response.set_cookie(key="user_id", value=user_id)
    return response


@app.get("/{name}/start")
async def game_start(
    name: str,
    request: Request,
    user_id: Union[str, None] = Cookie(default=None),
):
    if not user_id:
        user_id = create_user()
    game = await load_game(name)
    msg = ""
    if game:
        if game.instance:
            return RedirectResponse(f"/{name}")
        if user_id == game.host:
            if len(game.players) < 2:
                msg = "not enough players to start game"
            else:
                if game.kind == "maumau":
                    game.instance = MauMau(game.name, game.players)
                    await store.save(name, game)
                else:
                    msg = "only maumau supported atm"

    response = templates.TemplateResponse(
        "game_meta.html",
        {
            "request": request,
            "user_id": user_id,
            "name": name,
            "msg": msg,
            "game": game,
        },
    )
    response.set_cookie(key="user_id", value=user_id)
    return response


@app.get("/{name}/join")
async def game_join(
    name: str,
    request: Request,
    user_id: Union[str, None] = Cookie(default=None),
):
    if not user_id:
        user_id = create_user()
    game = await load_game(name)
    msg = ""
    if game:
        if game.instance:
            return RedirectResponse(f"/{name}")
        elif len(game.players) == 5:
            msg = "max players for this game is 5."
        else:
            if user_id not in game.players:
                game.players.append(user_id)
            await store.save(name, game)

    response = templates.TemplateResponse(
        "game_meta.html",
        {
            "request": request,
            "user_id": user_id,
            "name": name,
            "msg": msg,
            "game": game,
        },
    )
    response.set_cookie(key="user_id", value=user_id)
    return response


@app.get("/{name}/status")
async def trigger_game_status(
    name: str,
    user_id: Union[str, None] = Cookie(default=None),
):
    if not user_id:
        user_id = create_user()
    await ws_manager.broadcast(await status_html(name, user_id), name)
    return ""


async def status_html(name, user_id):
    game = await load_game(name)
    if game and game.instance:
        template = templates.env.get_template("partials/status.html")
        return template.render(state=game.instance.status(user_id))
    return ""


@app.get("/{name}/action")
async def game_action(
    name,
    request: Request,
    response: Response,
    action: Union[str, None] = None,
    card: Union[str, None] = None,
    user_id: Union[str, None] = Cookie(default=None),
):
    if not user_id:
        user_id = create_user()
    game = await load_game(name)
    if game and game.instance:
        r = {}
        if action:
            r = game.instance.action(action=action, card=card, player_id=user_id)
            await store.save(name, game)
            await ws_manager.broadcast(await status_html(name, user_id), name)

        return templates.TemplateResponse(
            "partials/action_area.html",
            {
                "request": request,
                "user_id": user_id,
                "state": game.instance.status(user_id),
                "name": name,
                "msg": r.get("msg", ""),
            },
        )


@app.get("/{name}")
async def game_index(
    name,
    request: Request,
    response: Response,
    user_id: Union[str, None] = Cookie(default=None),
):
    if not user_id:
        user_id = create_user()
    game = await load_game(name)
    if game:
        if game.instance:
            await ws_manager.broadcast(await status_html(name, user_id), name)
            return templates.TemplateResponse(
                "game_state.html",
                {
                    "request": request,
                    "you": user_id,
                    "state": game.instance.status(user_id),
                    "name": name,
                },
            )
        return "game not started, yet"
    return "game not found"


@app.websocket("/ws/{game}")
async def websocket_endpoint(
    game: str,
    websocket: WebSocket,
):
    await ws_manager.connect(websocket, game)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(data)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, game)


@app.get("/")
async def index():
    return "nothing to see"


app.mount(
    "/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static"
)
app.mount(
    "/assets", StaticFiles(directory=Path(__file__).parent / "assets"), name="assets"
)
