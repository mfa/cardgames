## (private) cardgames project

### features

- video-conference view (for screen share)
- every client is an agent
- a client can be a human or code

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
