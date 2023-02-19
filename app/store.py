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

    async def save(self, name, state):
        ts = datetime.datetime.utcnow().timestamp()
        state["modified"] = ts
        self.game_states[name] = state

        _path = self.path / name
        _path.mkdir(exist_ok=True, parents=True)

        fn = _path / f"{ts}.json"
        async with aiofiles.open(fn, "w") as fp:
            await fp.write(json.dumps(state))
            # symlink to current version
            _link = _path / "default.json"
            _link.unlink(missing_ok=True)
            _link.symlink_to(fn)
        return

    async def load(self, name):
        if name in self.game_states:
            return self.game_states.get(name)

        fn = self.path / name / "default.json"
        if fn.exists():
            async with aiofiles.open(fn, "r") as fp:
                return json.loads(await fp.read())
        return
