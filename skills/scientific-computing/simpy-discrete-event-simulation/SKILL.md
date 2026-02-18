---
name: simpy-discrete-event-simulation
description: "Process-based discrete-event simulation framework. Model systems with queues, shared resources, and time-based events: manufacturing lines, service operations, network traffic, logistics. Processes are Python generators that yield events. Resource types include capacity-limited (Resource, PriorityResource, PreemptiveResource), bulk material (Container), and object storage (Store, FilterStore). For continuous simulation use SciPy ODE solvers; for agent-based modeling use Mesa."
license: MIT
---

# SimPy — Discrete-Event Simulation

## Overview

SimPy is a process-based discrete-event simulation framework using standard Python generators. Model systems where entities (customers, vehicles, packets) interact with shared resources (servers, machines, bandwidth) over time, with event-driven scheduling and optional real-time synchronization.

## When to Use

- Modeling queue-based systems with resource contention (servers, machines, staff)
- Manufacturing process simulation (production lines, scheduling, bottleneck analysis)
- Network simulation (packet routing, bandwidth allocation, latency analysis)
- Capacity planning (determining optimal resource levels for target throughput)
- Healthcare operations (ER patient flow, staff allocation, bed management)
- Logistics and transportation (warehouse operations, vehicle routing)
- **For continuous-time ODE systems** → use SciPy `solve_ivp`
- **For agent-based modeling** → use Mesa

## Prerequisites

```python
# pip install simpy
import simpy
import random
```

## Quick Start

```python
import simpy
import random

def customer(env, name, server):
    """Customer arrives, waits for server, gets served, departs."""
    arrival = env.now
    with server.request() as req:
        yield req  # Wait in queue
        wait = env.now - arrival
        yield env.timeout(random.expovariate(1/3))  # Service time
        print(f'{name}: waited {wait:.1f}, served at {env.now:.1f}')

def arrivals(env, server):
    for i in range(20):
        yield env.timeout(random.expovariate(1/2))  # Inter-arrival
        env.process(customer(env, f'C{i}', server))

env = simpy.Environment()
server = simpy.Resource(env, capacity=2)
env.process(arrivals(env, server))
env.run(until=50)
```

## Core API

### 1. Environment & Processes

```python
import simpy

# Standard environment
env = simpy.Environment(initial_time=0)

# Processes are Python generators that yield events
def machine(env, name, repair_time):
    while True:
        yield env.timeout(random.expovariate(1/10))  # Time to failure
        print(f'{name} broke at {env.now:.1f}')
        yield env.timeout(repair_time)
        print(f'{name} repaired at {env.now:.1f}')

# Start processes — returns a Process event
proc = env.process(machine(env, 'Machine-1', repair_time=2))

# Run until time limit or no events remain
env.run(until=100)
# env.run()  # Run until no more events

# Current simulation time
print(f'Final time: {env.now}')
```

```python
# Processes can return values and be awaited
def subtask(env, duration):
    yield env.timeout(duration)
    return f'completed in {duration}'

def main_task(env):
    # Sequential: wait for one process
    result = yield env.process(subtask(env, 5))
    print(f'Subtask {result} at {env.now}')

    # Parallel: wait for ALL (AllOf)
    t1 = env.process(subtask(env, 3))
    t2 = env.process(subtask(env, 4))
    results = yield t1 & t2  # AllOf — resumes when both done
    print(f'Both done at {env.now}')

    # Race: wait for ANY (AnyOf)
    t3 = env.process(subtask(env, 2))
    t4 = env.process(subtask(env, 6))
    result = yield t3 | t4  # AnyOf — resumes when first completes
    print(f'First done at {env.now}')

env = simpy.Environment()
env.process(main_task(env))
env.run()
```

### 2. Resources

```python
import simpy

env = simpy.Environment()

# Basic resource — capacity-limited (e.g., 2 servers)
server = simpy.Resource(env, capacity=2)
print(f'Capacity: {server.capacity}, In use: {server.count}, Queue: {len(server.queue)}')

# Priority resource — lower number = higher priority
priority_server = simpy.PriorityResource(env, capacity=1)

def vip_customer(env, res):
    with res.request(priority=1) as req:  # Higher priority
        yield req
        yield env.timeout(3)

def regular_customer(env, res):
    with res.request(priority=10) as req:  # Lower priority
        yield req
        yield env.timeout(3)

# Preemptive resource — high priority interrupts low priority
preemptive = simpy.PreemptiveResource(env, capacity=1)

def urgent_job(env, res):
    with res.request(priority=0, preempt=True) as req:
        yield req  # May interrupt current user
        yield env.timeout(1)
```

```python
# Container — bulk material (fuel, water, inventory)
tank = simpy.Container(env, capacity=100, init=50)

def refuel(env, tank):
    yield tank.put(30)  # Add 30 units
    print(f'Tank level: {tank.level}/{tank.capacity}')

def consume(env, tank):
    yield tank.get(20)  # Remove 20 units
    print(f'Tank level: {tank.level}/{tank.capacity}')

# Store — FIFO object storage
warehouse = simpy.Store(env, capacity=10)

def producer(env, store):
    for i in range(5):
        yield env.timeout(2)
        yield store.put(f'Item-{i}')

def consumer(env, store):
    while True:
        item = yield store.get()
        print(f'Got {item} at {env.now}')
        yield env.timeout(3)

# FilterStore — selective retrieval
parts = simpy.FilterStore(env, capacity=20)

def picker(env, store):
    # Get specific item matching condition
    item = yield store.get(lambda x: x['color'] == 'red')
    print(f'Found red item: {item}')
```

### 3. Events & Synchronization

```python
import simpy

env = simpy.Environment()

# Basic event — manual trigger for signaling between processes
signal = env.event()

def waiter(env, event):
    print(f'Waiting at {env.now}')
    value = yield event  # Blocks until triggered
    print(f'Got signal "{value}" at {env.now}')

def sender(env, event):
    yield env.timeout(5)
    event.succeed(value='go')  # Trigger with value

env.process(waiter(env, signal))
env.process(sender(env, signal))
env.run()
# Output: Waiting at 0, Got signal "go" at 5

# Timeout — most common event
yield env.timeout(delay=5)

# Process interruption
def interruptible(env, name):
    try:
        yield env.timeout(10)
    except simpy.Interrupt as interrupt:
        print(f'{name} interrupted: {interrupt.cause} at {env.now}')

def interruptor(env, proc):
    yield env.timeout(3)
    proc.interrupt('maintenance')

proc = env.process(interruptible(env, 'Worker'))
env.process(interruptor(env, proc))
```

```python
# Barrier synchronization — wait for N processes
class Barrier:
    def __init__(self, env, n):
        self.env = env
        self.n = n
        self.count = 0
        self.event = env.event()

    def wait(self):
        self.count += 1
        if self.count >= self.n:
            self.event.succeed()
        return self.event

def phase_worker(env, name, barrier):
    yield env.timeout(random.uniform(1, 5))  # Phase work
    print(f'{name} reached barrier at {env.now:.1f}')
    yield barrier.wait()  # Wait for all workers
    print(f'{name} passed barrier at {env.now:.1f}')

env = simpy.Environment()
barrier = Barrier(env, n=3)
for i in range(3):
    env.process(phase_worker(env, f'W{i}', barrier))
env.run()
```

### 4. Monitoring & Statistics

```python
import simpy

# Inline statistics collection
class Stats:
    def __init__(self):
        self.wait_times = []
        self.queue_lengths = []

    def report(self):
        if self.wait_times:
            avg_wait = sum(self.wait_times) / len(self.wait_times)
            max_wait = max(self.wait_times)
            print(f'Avg wait: {avg_wait:.2f}, Max wait: {max_wait:.2f}')
            print(f'Customers served: {len(self.wait_times)}')

def customer(env, name, server, stats):
    arrival = env.now
    with server.request() as req:
        yield req
        wait = env.now - arrival
        stats.wait_times.append(wait)
        stats.queue_lengths.append(len(server.queue))
        yield env.timeout(random.expovariate(1/3))

env = simpy.Environment()
server = simpy.Resource(env, capacity=2)
stats = Stats()

def gen(env, server, stats):
    for i in range(100):
        yield env.timeout(random.expovariate(1/2))
        env.process(customer(env, f'C{i}', server, stats))

env.process(gen(env, server, stats))
env.run(until=200)
stats.report()
```

```python
# Resource monitoring via monkey-patching
def patch_resource(resource, data):
    """Patch resource to log request/release events."""
    original_request = resource.request
    original_release = resource.release

    def monitored_request(*args, **kwargs):
        req = original_request(*args, **kwargs)
        data.append((resource._env.now, 'request', resource.count, len(resource.queue)))
        return req

    def monitored_release(*args, **kwargs):
        result = original_release(*args, **kwargs)
        data.append((resource._env.now, 'release', resource.count, len(resource.queue)))
        return result

    resource.request = monitored_request
    resource.release = monitored_release

log = []
patch_resource(server, log)
# After simulation: analyze log for utilization, queue dynamics
```

### 5. Real-Time Simulation

```python
import simpy.rt

# Real-time environment — synchronized with wall clock
env = simpy.rt.RealtimeEnvironment(factor=1.0)  # 1 sim unit = 1 second
# factor=0.1 → 10x faster (1 sim unit = 0.1 seconds)
# factor=60 → 1 sim unit = 1 minute

# Strict mode raises RuntimeError if simulation can't keep up
env_strict = simpy.rt.RealtimeEnvironment(factor=1.0, strict=True)

# Non-strict mode (default) allows slower-than-real-time execution
env_relaxed = simpy.rt.RealtimeEnvironment(factor=1.0, strict=False)

def periodic_task(env, interval):
    while True:
        print(f'Tick at sim time {env.now:.1f}')
        yield env.timeout(interval)

env = simpy.rt.RealtimeEnvironment(factor=1.0)
env.process(periodic_task(env, 2.0))
env.run(until=10)
# Prints "Tick" every ~2 real seconds
```

## Key Concepts

### Resource Selection Guide

| Need | Resource Type | Key Feature |
|------|--------------|-------------|
| Limited servers/machines | `Resource` | FIFO queue, capacity limit |
| Priority queuing | `PriorityResource` | Lower number = higher priority |
| Preemptive scheduling | `PreemptiveResource` | High priority interrupts current user |
| Bulk material (fuel, water) | `Container` | `put(amount)` / `get(amount)`, continuous level |
| Object queue (FIFO) | `Store` | `put(item)` / `get()`, ordered retrieval |
| Conditional retrieval | `FilterStore` | `get(lambda x: condition)` |
| Priority-ordered items | `PriorityStore` | Items sorted by priority |

### Process Interaction Mechanisms

| Mechanism | Use When | Code Pattern |
|-----------|----------|-------------|
| Event signaling | Broadcast to multiple waiters | `event = env.event()` → `yield event` / `event.succeed()` |
| Process yield | Sequential or parallel execution | `yield env.process(func())` or `yield p1 & p2` |
| Interruption | Preemption, maintenance, cancellation | `proc.interrupt(cause)` + `try/except simpy.Interrupt` |
| Timeout racing | Timeout with cancellation | `yield event | env.timeout(limit)` |

## Common Workflows

### 1. Manufacturing Line Simulation

```python
import simpy
import random

def part(env, name, machines, buffer, stats):
    """Part flows through sequential machines with intermediate buffer."""
    for i, machine in enumerate(machines):
        with machine.request() as req:
            yield req
            process_time = random.triangular(1, 3, 2)
            yield env.timeout(process_time)

    if buffer.level < buffer.capacity:
        yield buffer.put(1)
        stats['produced'] += 1

def part_generator(env, machines, buffer, stats):
    i = 0
    while True:
        yield env.timeout(random.expovariate(1/2))
        env.process(part(env, f'Part-{i}', machines, buffer, stats))
        i += 1

random.seed(42)
env = simpy.Environment()
machines = [simpy.Resource(env, capacity=1) for _ in range(3)]
output_buffer = simpy.Container(env, capacity=100, init=0)
stats = {'produced': 0}
env.process(part_generator(env, machines, output_buffer, stats))
env.run(until=480)  # 8-hour shift
print(f'Parts produced: {stats["produced"]}')
print(f'Buffer level: {output_buffer.level}')
```

### 2. Multi-Server Queue with Priority

```python
import simpy
import random

def patient(env, name, priority, er, stats):
    arrival = env.now
    with er.request(priority=priority) as req:
        yield req
        wait = env.now - arrival
        stats['waits'].append((name, priority, wait))
        service = random.expovariate(1/15)  # ~15 min avg
        yield env.timeout(service)

def patient_arrivals(env, er, stats):
    i = 0
    while True:
        yield env.timeout(random.expovariate(1/5))  # ~5 min between arrivals
        pri = random.choices([1, 2, 3], weights=[0.1, 0.3, 0.6])[0]
        env.process(patient(env, f'P{i}', pri, er, stats))
        i += 1

random.seed(42)
env = simpy.Environment()
er = simpy.PriorityResource(env, capacity=3)
stats = {'waits': []}
env.process(patient_arrivals(env, er, stats))
env.run(until=480)

# Analyze by priority
for pri in [1, 2, 3]:
    waits = [w for _, p, w in stats['waits'] if p == pri]
    if waits:
        print(f'Priority {pri}: avg wait {sum(waits)/len(waits):.1f}, n={len(waits)}')
```

### 3. Producer-Consumer with Monitoring

Text-only workflow (combines Core API modules 2, 3, 4):
1. Create `simpy.Store` with bounded capacity (Module 2: Resources)
2. Implement producer process that `yield store.put(item)` with production delay (Module 2)
3. Implement consumer process that `yield store.get()` with processing delay (Module 2)
4. Add event signaling for backpressure when store full (Module 3: Events)
5. Collect throughput, queue length, and idle time statistics (Module 4: Monitoring)
6. Run simulation and generate report

## Key Parameters

| Parameter | Module | Default | Range | Effect |
|-----------|--------|---------|-------|--------|
| `capacity` | Resource | 1 | 1–∞ | Number of concurrent users |
| `priority` | PriorityResource.request | 0 | int | Lower = higher priority |
| `preempt` | PreemptiveResource.request | True | bool | Whether to interrupt lower-priority |
| `capacity` | Container | float('inf') | 0–∞ | Maximum level |
| `init` | Container | 0 | 0–capacity | Initial level |
| `capacity` | Store | float('inf') | 0–∞ | Maximum items |
| `factor` | RealtimeEnvironment | 1.0 | >0 | Sim-to-wall-clock ratio |
| `strict` | RealtimeEnvironment | False | bool | Raise error if behind schedule |
| `initial_time` | Environment | 0 | any float | Simulation start time |

## Best Practices

1. **Always use context managers for resources**: `with resource.request() as req: yield req` ensures automatic release even on exceptions
2. **Set random seeds for reproducibility**: `random.seed(42)` before creating processes; use `numpy.random` for more distributions
3. **Collect statistics inline**: Append to lists during simulation, compute aggregates after `env.run()` — don't query mid-simulation
4. **Use triangular distribution for process times**: `random.triangular(min, max, mode)` is more realistic than uniform for service times
5. **Anti-pattern — forgetting yield**: `env.timeout(5)` without `yield` creates the event but doesn't pause the process. Always `yield env.timeout(5)`
6. **Anti-pattern — reusing events**: Events can only be triggered once. Create new `env.event()` for each signal cycle; for repeatable signals, create fresh events in a loop

## Common Recipes

### Recipe: Simulation with Multiple Replications

```python
import simpy
import random
import statistics

def run_single(seed, sim_time=480, n_servers=2):
    random.seed(seed)
    env = simpy.Environment()
    server = simpy.Resource(env, capacity=n_servers)
    waits = []

    def customer(env, server):
        arrival = env.now
        with server.request() as req:
            yield req
            waits.append(env.now - arrival)
            yield env.timeout(random.expovariate(1/3))

    def gen(env, server):
        while True:
            yield env.timeout(random.expovariate(1/2))
            env.process(customer(env, server))

    env.process(gen(env, server))
    env.run(until=sim_time)
    return sum(waits) / len(waits) if waits else 0

# Run 30 replications
results = [run_single(seed=i) for i in range(30)]
print(f'Mean avg wait: {statistics.mean(results):.2f}')
print(f'95% CI: ±{1.96 * statistics.stdev(results) / len(results)**0.5:.2f}')
```

### Recipe: Interrupt-Based Maintenance

```python
import simpy
import random

def machine(env, name, repair_crew):
    while True:
        try:
            # Operate until failure
            ttf = random.expovariate(1/50)  # Mean 50 time units to failure
            yield env.timeout(ttf)
            print(f'{name} failed at {env.now:.1f}')
        except simpy.Interrupt:
            print(f'{name} interrupted for maintenance at {env.now:.1f}')

        # Repair (needs repair crew)
        with repair_crew.request() as req:
            yield req
            repair = random.uniform(2, 5)
            yield env.timeout(repair)
            print(f'{name} repaired at {env.now:.1f}')

def maintenance_scheduler(env, machines_procs):
    """Periodic preventive maintenance every 40 time units."""
    while True:
        yield env.timeout(40)
        for proc in machines_procs:
            if proc.is_alive:
                proc.interrupt('scheduled maintenance')

env = simpy.Environment()
repair_crew = simpy.Resource(env, capacity=1)
procs = [env.process(machine(env, f'M{i}', repair_crew)) for i in range(3)]
env.process(maintenance_scheduler(env, procs))
env.run(until=200)
```

### Recipe: Container-Based Supply Chain

```python
import simpy
import random

def supplier(env, warehouse):
    """Deliver batch when level drops below reorder point."""
    while True:
        if warehouse.level < 20:  # Reorder point
            yield env.timeout(random.uniform(5, 10))  # Lead time
            amount = min(50, warehouse.capacity - warehouse.level)
            yield warehouse.put(amount)
            print(f'Delivered {amount} units at {env.now:.1f}, level={warehouse.level}')
        yield env.timeout(1)  # Check interval

def demand(env, warehouse, stats):
    while True:
        yield env.timeout(random.expovariate(1/2))
        qty = random.randint(1, 5)
        if warehouse.level >= qty:
            yield warehouse.get(qty)
            stats['fulfilled'] += qty
        else:
            stats['stockouts'] += 1

env = simpy.Environment()
warehouse = simpy.Container(env, capacity=100, init=80)
stats = {'fulfilled': 0, 'stockouts': 0}
env.process(supplier(env, warehouse))
env.process(demand(env, warehouse, stats))
env.run(until=500)
print(f'Fulfilled: {stats["fulfilled"]}, Stockouts: {stats["stockouts"]}')
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|---------|
| Process doesn't pause | Missing `yield` before event | Always `yield env.timeout(x)`, not just `env.timeout(x)` |
| `RuntimeError: Event already triggered` | Reusing a triggered event | Create new `env.event()` for each signal cycle |
| Resource never released | Not using context manager | Use `with resource.request() as req:` pattern |
| Simulation runs forever | No `until` parameter and infinite process | Add `env.run(until=time)` or ensure processes terminate |
| `simpy.Interrupt` not caught | Missing try/except in interruptible process | Wrap `yield` in `try: ... except simpy.Interrupt:` |
| Wrong queue order | Using Resource instead of PriorityResource | Switch to `simpy.PriorityResource` for priority queuing |
| Real-time too slow | Computation exceeds wall-clock budget | Set `strict=False` or increase `factor` |
| Container `put` blocks | Container at capacity | Check `container.level < container.capacity` before put |
| FilterStore `get` blocks forever | No matching items | Ensure producers create items matching the filter criteria |
| Statistics are empty | Collecting before `env.run()` | Call `stats.report()` after `env.run()` completes |

## Bundled Resources

- **`references/process_events_guide.md`** — Detailed event lifecycle (triggered→processed), composite events (AllOf/AnyOf), process interaction patterns (signaling, barriers, interruption, handshake), and advanced synchronization. Consolidated from original events.md (375 lines) + process-interaction.md (425 lines)
- **`references/resources_monitoring_guide.md`** — Complete resource type reference (Resource, Priority, Preemptive, Container, Store, FilterStore, PriorityStore), monitoring via monkey-patching (ResourceMonitor, ContainerMonitor classes), statistical collection patterns, CSV/matplotlib export, and real-time simulation (RealtimeEnvironment, time scaling, strict mode, HIL patterns). Consolidated from original resources.md (276 lines) + monitoring.md (476 lines) + real-time.md (396 lines). Scripts functionality (basic_simulation_template.py, resource_monitor.py) incorporated into Core API monitoring examples and Common Recipes

## Related Skills

- **matplotlib-scientific-plotting** — Visualize simulation results (queue lengths, utilization over time)
- **polars-dataframes** — Analyze large simulation output datasets

## References

- SimPy Documentation: https://simpy.readthedocs.io/
- SimPy GitHub: https://github.com/teamhide/simpy
- Banks et al., "Discrete-Event System Simulation" (textbook reference)
