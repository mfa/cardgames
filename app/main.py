import uuid

from asgiref.wsgi import WsgiToAsgi
from flask import Flask, make_response, request

from .names import new_name
from .store import Store

wsgi_app = Flask(__name__)
store = Store()


@wsgi_app.route("/new")
async def new():
    name = new_name()
    user = request.cookies.get("user_id", str(uuid.uuid4()))
    state = {"name": name, "players": [user]}
    await store.save(name, state)

    resp = make_response(
        f'new game created - link to add other players: <a href="/join/{name}">{name}</a><br/> you are: {user}'
    )
    resp.set_cookie("user_id", user)
    return resp


@wsgi_app.route("/join/<name>")
async def join(name):
    state = await store.load(name)
    if state:
        user = request.cookies.get("user_id", str(uuid.uuid4()))
        if user not in state["players"]:
            state["players"].append(user)
        await store.save(name, state)

        resp = make_response(
            f"{name} found, players: {state['players']}<br/> you are: {user}"
        )
        resp.set_cookie("user_id", user)
        return resp
    return "game not found"


@wsgi_app.route("/<name>")
async def update(name):
    state = await store.load(name)
    if state:
        if "counter" in state:
            state["counter"] += 1
        else:
            state["counter"] = 1
        r = await store.save(name, state)
        print(r)
        user = request.cookies.get("user_id", str(uuid.uuid4()))
        if user in state["players"]:
            user_msg = "you are in this game"
        else:
            user_msg = f'<br/><a href="/join/{name}">join this game</a>'

        return (
            f"{name} found, players: {state['players']}<br/>counter: {state['counter']}, last_change: {state['modified']}<br/>"
            + user_msg
        )
    return "game not found"


@wsgi_app.route("/status")
async def status():
    return "redis ping: " + str(await store.ping())


@wsgi_app.route("/games")
async def games():
    games = [i.decode()[5:] for i in await store.keys()]
    return (
        "games found:<br/><ul><li>"
        + "<li>".join([f'<a href="/{i}">{i}</a>' for i in games])
        + '</ul><br/>create a <a href="/new">new game</a>'
    )


@wsgi_app.route("/")
async def index():
    print(await store.ping())
    return "nothing to see"


app = WsgiToAsgi(wsgi_app)
