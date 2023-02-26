import datetime
import json
from pathlib import Path

import aiofiles


class Store:
    def __init__(self):
        self.path = Path("/data/store")
        if not (self.path.exists() and self.path.is_dir()):
            # local setup
            self.path = Path(__file__).parent / "data"

        self.game_states = {}

    async def keys(self):
        return self.path.glob("*")

    async def save(self, name, game):
        print(f"save {name}")
        ts = datetime.datetime.utcnow().timestamp()
        game.modified = ts
        self.game_states[name] = game

        g = game.__dict__
        # save serialized state, not instance
        if g["instance"]:
            g["state"] = game.instance.serialize()
            del g["instance"]

        _path = self.path / name
        _path.mkdir(exist_ok=True, parents=True)

        fn = _path / f"{ts}.json"
        async with aiofiles.open(fn, "w") as fp:
            await fp.write(json.dumps(g))
            # symlink to current version
            _link = _path / "default.json"
            _link.unlink(missing_ok=True)
            _link.symlink_to(fn)
        return

    async def load(self, name):
        if name in self.game_states:
            print(f"local load: {name}")
            return self.game_states.get(name)

        fn = self.path / name / "default.json"
        if fn.exists():
            print(f"disc load: {name}")
            async with aiofiles.open(fn, "r") as fp:
                data = json.loads(await fp.read())
                self.game_states[name] = data
                return data
        return

    def set(self, name, attribute, value):
        self.game_states[name][attribute] = value
        return
