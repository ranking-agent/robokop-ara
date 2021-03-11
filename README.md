# Filter results (top-n) TRAPI operation reference implementation

## deployment

### native

```bash
./main.sh --port <PORT>
```

### docker

```bash
docker build . -t filter_results_top_n
docker run --name filter_results_top_n --rm -p <PORT>:7092 -it filter_results_top_n
```

### docker-compose

```bash
PORT=<PORT> docker-compose up --build
```

The "docker-compose" option requires either a) an environment variable called `PORT`, or b) a `.env` file containing a definition for `PORT`.

The default port is 7092.

Access Swagger UI at `http://localhost:<PORT>/docs`.
