# ARCHIVED: This is outdated and has been incorporated into the Aragorn repo.

# ROBOKOP-ARA

to deploy:

```bash
docker run \
--name robokop-ara \
-e PORT=7092 -p 7092:7092 \
-e OPENAPI_SERVER_URL=http://robokop.renci.org:7092 \
-d \
docker.pkg.github.com/ranking-agent/robokop-ara/robokop-ara:latest
```

or, from the source:

```bash
docker-compose up --build
```

Access Swagger UI at [`http://localhost:7092/docs`](http://localhost:7092/docs).



### Testing ROBOKOP-ARA
```
python -m pytest --cov=app --cov-report=term-missing tests
```
