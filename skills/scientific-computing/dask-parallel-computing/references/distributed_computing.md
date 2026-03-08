# Dask Distributed Computing Guide

Futures API, coordination primitives, scheduler configuration, and cluster deployment.

## Futures — Detailed API

### Client Setup

```python
from dask.distributed import Client

# Local cluster (auto-detect cores)
client = Client()

# Custom local resources
client = Client(n_workers=4, threads_per_worker=2, memory_limit='4GB')

# Remote cluster
client = Client('scheduler-address:8786')

print(client.dashboard_link)  # Dashboard URL
```

### Task Submission

```python
# Single task
future = client.submit(func, arg1, arg2, key='my-task')
result = future.result()  # Block until done

# Map over inputs
futures = client.map(func, [1, 2, 3, 4, 5])
results = client.gather(futures)

# Non-blocking check
print(future.done())    # True/False
print(future.status)    # 'pending', 'finished', 'error'

# Callbacks
def on_complete(f):
    print(f"Done: {f.result()}")
future.add_done_callback(on_complete)
```

### Error Handling

```python
future = client.submit(risky_function, data)
try:
    result = future.result()
except Exception as e:
    print(f"Task failed: {e}")
    # Retry or handle
    future = client.submit(fallback_function, data)
```

### Data Movement

```python
# Scatter large data to workers (once)
big_data = load_large_dataset()
data_future = client.scatter(big_data, broadcast=True)

# Use scattered data in tasks
futures = [client.submit(process, data_future, param) for param in params]

# Fire-and-forget (side effects only, don't need result)
from dask.distributed import fire_and_forget
future = client.submit(log_to_database, result)
fire_and_forget(future)
```

### Progressive Processing

```python
from dask.distributed import as_completed

futures = client.map(slow_function, range(100))

# Process results as they arrive
for batch in as_completed(futures, with_results=True).batches():
    for future, result in batch:
        process_result(result)
```

## Coordination Primitives

### Locks

```python
from dask.distributed import Lock

lock = Lock('file-write-lock')

def write_safely(data, filename):
    with lock:
        with open(filename, 'a') as f:
            f.write(data)

futures = [client.submit(write_safely, d, 'output.txt') for d in data_list]
```

### Queues

```python
from dask.distributed import Queue

q = Queue('work-queue')

# Producer
for item in items:
    q.put(item)

# Consumer (on workers)
def consumer():
    while True:
        item = q.get(timeout=10)
        if item is None:
            break
        process(item)
```

### Events

```python
from dask.distributed import Event

event = Event('data-ready')

def producer():
    prepare_data()
    event.set()  # Signal data is ready

def consumer():
    event.wait()  # Block until data ready
    process_data()
```

### Variables

```python
from dask.distributed import Variable

var = Variable('shared-config')
var.set({'batch_size': 32, 'learning_rate': 0.01})

def worker_func():
    config = Variable('shared-config').get()
    return train(batch_size=config['batch_size'])
```

## Actors — Stateful Workers

```python
class ModelServer:
    def __init__(self):
        self.model = load_model()
        self.count = 0

    def predict(self, x):
        self.count += 1
        return self.model.predict(x)

    def get_count(self):
        return self.count

# Create actor on a worker (~1ms roundtrip per method call)
actor = client.submit(ModelServer, actor=True).result()
prediction = actor.predict(input_data).result()
print(f"Predictions served: {actor.get_count().result()}")
```

## Scheduler Configuration

### Configuration Methods

```python
import dask

# Method 1: Global
dask.config.set(scheduler='threads')

# Method 2: Context manager
with dask.config.set(scheduler='processes'):
    result = computation.compute()

# Method 3: Per-compute
result = computation.compute(scheduler='synchronous')

# Method 4: Via Client (distributed becomes default)
client = Client()  # All compute() calls use distributed
```

### Scheduler Decision Matrix

| Workload | Scheduler | Rationale |
|----------|-----------|-----------|
| NumPy/pandas operations | `threads` | GIL-releasing, shared memory |
| Pure Python code | `processes` | Avoids GIL contention |
| Text/log processing | `processes` | Python-heavy string operations |
| Debugging with pdb | `synchronous` | Single-threaded, deterministic |
| Need dashboard/monitoring | `distributed` | Real-time task visualization |
| Multi-machine clusters | `distributed` | Network-based task distribution |
| Quick one-off computation | `threads` | Lowest overhead (~10 µs/task) |

### Thread Configuration

```python
# Numeric workloads: fewer workers, more threads
client = Client(n_workers=2, threads_per_worker=4)  # 8 cores total

# Python workloads: more workers, fewer threads
client = Client(n_workers=8, threads_per_worker=1)  # 8 cores total

# Environment variables
# export DASK_NUM_WORKERS=4
# export DASK_THREADS_PER_WORKER=2
```

## Cluster Deployment

### HPC with SLURM

```python
from dask_jobqueue import SLURMCluster
from dask.distributed import Client

cluster = SLURMCluster(
    cores=24, memory='100GB',
    walltime='02:00:00', queue='regular',
    job_extra_directives=['--account=myproject']
)
cluster.scale(jobs=10)
client = Client(cluster)

# Adaptive scaling
cluster.adapt(minimum=2, maximum=20)
```

### Kubernetes

```python
from dask_kubernetes import KubeCluster
from dask.distributed import Client

cluster = KubeCluster()
cluster.adapt(minimum=2, maximum=50)
client = Client(cluster)
```

### Worker Plugins

```python
from dask.distributed import WorkerPlugin

class GPUSetup(WorkerPlugin):
    def setup(self, worker):
        import cupy
        worker.gpu_device = cupy.cuda.Device(0)

client.register_worker_plugin(GPUSetup())
```

## Dashboard and Monitoring

```python
client = Client()
print(client.dashboard_link)  # http://localhost:8787

# Dashboard pages:
# /status     — task progress, worker status
# /workers    — memory usage per worker
# /tasks      — task stream timeline
# /graph      — task graph visualization
# /profile    — profiling information

# Performance report (saves HTML)
client.profile(filename='profile.html')

# Worker information
info = client.scheduler_info()
print(f"Workers: {len(info['workers'])}")
for addr, worker in info['workers'].items():
    print(f"  {addr}: {worker['memory_limit'] / 1e9:.1f} GB")
```

## Common Patterns

### Parameter Sweep

```python
def experiment(data, lr, batch_size):
    return train_model(data, lr=lr, batch_size=batch_size)

data_future = client.scatter(training_data, broadcast=True)

futures = []
for lr in [0.001, 0.01, 0.1]:
    for bs in [16, 32, 64]:
        f = client.submit(experiment, data_future, lr, bs)
        futures.append((lr, bs, f))

for lr, bs, f in futures:
    result = f.result()
    print(f"lr={lr}, bs={bs}: accuracy={result:.4f}")
```

### Iterative Algorithm with Convergence

```python
import dask.dataframe as dd

data = dd.read_parquet('data.parquet').persist()
prev_loss = float('inf')

for i in range(100):
    data = update_step(data).persist()
    loss = compute_loss(data).compute()

    if abs(prev_loss - loss) < 1e-6:
        print(f"Converged at iteration {i}")
        break
    prev_loss = loss

del data  # Release worker memory
```

Condensed from original: futures.md (542 lines) + schedulers.md (505 lines) = 1,047 lines total. Retained: all Futures API (submit, map, gather, scatter, fire_and_forget, as_completed), all coordination primitives (Lock, Queue, Event, Variable), Actors, all 5 scheduler types with decision matrix, thread configuration, HPC/Kubernetes deployment, adaptive scaling, worker plugins, dashboard monitoring, parameter sweep and iterative algorithm patterns. Omitted: verbose rationale prose and duplicate scheduler examples already in SKILL.md; development-to-production pattern (covered inline).
