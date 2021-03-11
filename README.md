# Filter results (top-n) TRAPI operation reference implementation

## deployment

### native

```bash
./main.sh --port <PORT>
```

The default port is 7092.

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

### kubernetes (minikube)

```bash
eval $(minikube -p minikube docker-env)  # point session to minikube's docker daemon
docker build . -t filter_results_top_n  # build image
kubectl create -f k8s-deployment.yml  # references local image
kubectl port-forward service/filter-results-top-n <PORT>:7092  # forward to port of your choice
```

Access Swagger UI at `http://localhost:<PORT>/docs`.
