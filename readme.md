## cardgames project

[![Run Tests](https://github.com/mfa/cardgames/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/mfa/cardgames/actions/workflows/tests.yml)

### features

- video-conference view (for screen share)
- every client is an agent
- a client can be a human or code

deployed version: <https://cards.with.cress.space/>

### run locally

run fastapi
```
uvicorn app.main:app --reload
```


### deploy to fly.io

(example for instance maintained by @mfa)

create volume:
```
flyctl volumes create cardgames_data --app floral-wave-1444 --region ams --size 1
```

initially create folder for data:
```
# ssh to instance
fly ssh console
# create folder
mkdir -p /data/store
```


### source for assets

cards: http://nicubunu.ro/cards/ (public domain)
