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

    resp = make_response(f"new game created: {name}<br/> you are: {user} (cookie set)")
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

        resp = make_response(f"{name} found, players: {state['players']}")
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
        return f"{name} found, players: {state['players']}, counter: {state['counter']}, last_change: {state['modified']}"
    return "game not found"


@wsgi_app.route("/status")
async def status():
    return "redis ping: " + str(await store.ping())


@wsgi_app.route("/")
async def index():
    print(await store.ping())
    return "nothing to see"


app = WsgiToAsgi(wsgi_app)
