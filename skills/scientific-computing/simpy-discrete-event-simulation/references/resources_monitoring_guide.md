# SimPy Resources, Monitoring & Real-Time Guide

Complete resource types, monitoring techniques, data collection, export, and real-time simulation.

## Resource Types — Detailed

### Resource (Basic Semaphore)

```python
import simpy

env = simpy.Environment()
resource = simpy.Resource(env, capacity=2)

def user(env, name, resource):
    with resource.request() as req:
        yield req
        print(f'{name}: capacity={resource.capacity}, count={resource.count}, queue={len(resource.queue)}')
        yield env.timeout(5)

# queue property: list of pending requests
# count property: current number of active users
```

### PriorityResource

Lower priority number = higher priority. Does NOT preempt current users.

```python
resource = simpy.PriorityResource(env, capacity=1)

def user(env, name, priority, resource):
    with resource.request(priority=priority) as req:
        yield req
        print(f'{name} (pri={priority}) at {env.now}')
        yield env.timeout(5)

# Queued requests sorted by priority
```

### PreemptiveResource

High-priority requests interrupt lower-priority current users via `simpy.Interrupt`.

```python
resource = simpy.PreemptiveResource(env, capacity=1)

def user(env, name, priority, resource):
    with resource.request(priority=priority) as req:
        try:
            yield req
            print(f'{name} acquired at {env.now}')
            yield env.timeout(10)
        except simpy.Interrupt:
            print(f'{name} preempted at {env.now}')

# preempt=True (default): interrupts lower-priority user
# preempt=False: waits in queue without interrupting
```

### Container

Homogeneous bulk material — fuel, water, inventory levels.

```python
container = simpy.Container(env, capacity=100, init=50)
# capacity: max level (default: float('inf'))
# init: initial level (default: 0)
# level: current amount

def producer(env, c):
    while True:
        yield env.timeout(5)
        yield c.put(20)  # Blocks if would exceed capacity
        print(f'Level: {c.level}')

def consumer(env, c):
    while True:
        yield env.timeout(7)
        yield c.get(15)  # Blocks if insufficient
        print(f'Level: {c.level}')
```

### Store (FIFO)

```python
store = simpy.Store(env, capacity=10)

def producer(env, store):
    for i in range(5):
        yield env.timeout(2)
        yield store.put(f'Item-{i}')  # Blocks if full

def consumer(env, store):
    while True:
        item = yield store.get()  # Blocks if empty
        yield env.timeout(3)
```

### FilterStore

Selective retrieval with filter function.

```python
store = simpy.FilterStore(env, capacity=10)

def producer(env, store):
    for color in ['red', 'blue', 'green', 'red']:
        yield env.timeout(1)
        yield store.put({'color': color, 'time': env.now})

def consumer(env, store, target_color):
    item = yield store.get(lambda x: x['color'] == target_color)
    print(f'Got {target_color} from time {item["time"]}')
```

### PriorityStore

Items retrieved in priority order (lowest first). Items must implement `__lt__`.

```python
class PriorityItem:
    def __init__(self, priority, data):
        self.priority = priority
        self.data = data
    def __lt__(self, other):
        return self.priority < other.priority

store = simpy.PriorityStore(env, capacity=10)

def producer(env, store):
    for pri, name in [(10, 'Low'), (1, 'High'), (5, 'Med')]:
        yield store.put(PriorityItem(pri, name))

def consumer(env, store):
    item = yield store.get()
    print(f'Got: {item.data}')  # 'High' (priority 1)
```

## Monitoring Techniques

### Resource Monitoring via Monkey-Patching

```python
def patch_resource(resource, data_log):
    """Patch to log all requests and releases."""
    original_request = resource.request
    original_release = resource.release

    def logged_request(*args, **kwargs):
        req = original_request(*args, **kwargs)
        data_log.append(('request', resource._env.now, resource.count, len(resource.queue)))
        return req

    def logged_release(*args, **kwargs):
        result = original_release(*args, **kwargs)
        data_log.append(('release', resource._env.now, resource.count, len(resource.queue)))
        return result

    resource.request = logged_request
    resource.release = logged_release

# Usage
log = []
patch_resource(server, log)
# After simulation: analyze for utilization, queue dynamics
```

### Resource Subclassing

```python
class MonitoredResource(simpy.Resource):
    def __init__(self, env, capacity):
        super().__init__(env, capacity)
        self.data = []

    def request(self, *args, **kwargs):
        req = super().request(*args, **kwargs)
        utilization = self.count / self.capacity
        self.data.append((self._env.now, 'request', len(self.queue), utilization))
        return req

    def release(self, *args, **kwargs):
        result = super().release(*args, **kwargs)
        utilization = self.count / self.capacity
        self.data.append((self._env.now, 'release', len(self.queue), utilization))
        return result

    def average_utilization(self):
        utils = [u for _, _, _, u in self.data]
        return sum(utils) / len(utils) if utils else 0
```

### Container Level Monitoring

```python
class MonitoredContainer(simpy.Container):
    def __init__(self, env, capacity, init=0):
        super().__init__(env, capacity, init)
        self.level_data = [(0, init)]

    def put(self, amount):
        result = super().put(amount)
        self.level_data.append((self._env.now, self.level))
        return result

    def get(self, amount):
        result = super().get(amount)
        self.level_data.append((self._env.now, self.level))
        return result
```

### Time-Series Collection

```python
def system_monitor(env, state, log, interval):
    """Periodic sampling of system state."""
    while True:
        log.append((env.now, state['queue'], state['utilization']))
        yield env.timeout(interval)

# After simulation
for time, queue, util in log:
    print(f't={time}: queue={queue}, util={util:.2%}')
```

### Queue Statistics Class

```python
class QueueStatistics:
    def __init__(self):
        self.wait_times = []
        self.queue_lengths = []

    def record(self, arrival, departure, queue_len):
        self.wait_times.append(departure - arrival)
        self.queue_lengths.append(queue_len)

    def summary(self):
        return {
            'avg_wait': sum(self.wait_times) / len(self.wait_times) if self.wait_times else 0,
            'max_wait': max(self.wait_times) if self.wait_times else 0,
            'avg_queue': sum(self.queue_lengths) / len(self.queue_lengths) if self.queue_lengths else 0,
            'n': len(self.wait_times),
        }
```

## Event Tracing

### Environment Step Monitoring

```python
def trace(env, callback):
    """Trace all events processed by the environment."""
    def _trace_step():
        if env._queue:
            time, priority, event_id, event = env._queue[0]
            callback(time, priority, event_id, event)
        return original_step()

    original_step = env.step
    env.step = _trace_step

def event_callback(time, priority, event_id, event):
    print(f'Event: t={time}, pri={priority}, type={type(event).__name__}')

env = simpy.Environment()
trace(env, event_callback)
```

### MonitoredEnvironment

```python
class MonitoredEnvironment(simpy.Environment):
    def __init__(self):
        super().__init__()
        self.scheduled_events = []

    def schedule(self, event, priority=simpy.core.NORMAL, delay=0):
        super().schedule(event, priority, delay)
        self.scheduled_events.append((self.now + delay, type(event).__name__))
```

## Data Export

### CSV Export

```python
import csv

def export_to_csv(data, filename, headers=('Time', 'Metric', 'Value')):
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(data)
```

### Matplotlib Plotting

```python
import matplotlib.pyplot as plt

class SimPlotter:
    def __init__(self):
        self.times = []
        self.values = []

    def update(self, time, value):
        self.times.append(time)
        self.values.append(value)

    def plot(self, title='Simulation Results', ylabel='Value'):
        plt.figure(figsize=(10, 6))
        plt.plot(self.times, self.values)
        plt.xlabel('Time')
        plt.ylabel(ylabel)
        plt.title(title)
        plt.grid(True)
        plt.savefig('simulation_plot.png', dpi=150)
```

## Real-Time Simulation

### RealtimeEnvironment

```python
import simpy.rt

# 1:1 mapping (1 sim unit = 1 second)
env = simpy.rt.RealtimeEnvironment(factor=1.0)

# factor=0.1 → 10x faster (1 sim unit = 0.1 seconds)
# factor=60 → 1 sim unit = 1 minute

# Constructor parameters
env = simpy.rt.RealtimeEnvironment(
    initial_time=0,      # Starting simulation time
    factor=1.0,          # Real time per simulation time unit
    strict=True          # Raise RuntimeError if behind schedule
)
```

### Strict vs Non-Strict Mode

```python
import time as walltime

# strict=True: raises RuntimeError if computation exceeds budget
env = simpy.rt.RealtimeEnvironment(factor=1.0, strict=True)
try:
    # If process logic takes longer than the timeout...
    env.run()
except RuntimeError as e:
    print(f'Timing violation: {e}')

# strict=False: silently runs slower than real-time
env = simpy.rt.RealtimeEnvironment(factor=1.0, strict=False)
# Suitable for development, debugging, variable workloads
```

### Hardware-in-the-Loop Pattern

```python
import simpy.rt

def control_loop(env, hardware, setpoint):
    while True:
        sensor = hardware.read_sensor()
        error = setpoint - sensor
        hardware.write_actuator(error * 0.1)
        yield env.timeout(0.5)  # 2 Hz control rate

env = simpy.rt.RealtimeEnvironment(factor=1.0, strict=False)
env.process(control_loop(env, hardware, setpoint=25.0))
env.run(until=60)
```

### Periodic Real-Time Tasks

```python
def periodic_task(env, name, period, work_duration):
    while True:
        start = env.now
        yield env.timeout(work_duration)  # Do work
        wait = period - (env.now - start)
        if wait > 0:
            yield env.timeout(wait)  # Wait for next period

env = simpy.rt.RealtimeEnvironment(factor=1.0)
env.process(periodic_task(env, 'Sensor', period=2.0, duration=0.5))
env.run(until=10)
```

### Real-Time Performance Monitoring

```python
import time as walltime

class RTMonitor:
    def __init__(self):
        self.drift_values = []

    def record(self, sim_time, real_elapsed, expected_elapsed):
        self.drift_values.append(real_elapsed - expected_elapsed)

    def report(self):
        if self.drift_values:
            print(f'Avg drift: {sum(self.drift_values)/len(self.drift_values)*1000:.2f} ms')
            print(f'Max drift: {max(abs(d) for d in self.drift_values)*1000:.2f} ms')
```

### Converting Standard to Real-Time

```python
# Minimal change: replace Environment with RealtimeEnvironment
# Standard (fast)
env = simpy.Environment()

# Real-time (synchronized)
env = simpy.rt.RealtimeEnvironment(factor=1.0)

# Same process code works with both environments
```

## Monitoring Best Practices

1. **Minimize overhead**: Only monitor what's necessary; excessive logging slows simulations
2. **Structured data**: Use classes or namedtuples for complex data points
3. **Always timestamp**: Include `env.now` with every recorded metric
4. **Aggregate post-simulation**: Collect raw data during `env.run()`, compute statistics after
5. **Memory management**: For long simulations, periodically flush data to disk
6. **Separation of concerns**: Keep monitoring code separate from simulation logic
7. **Validate neutrality**: Verify monitoring doesn't affect simulation behavior

Condensed from original: resources.md (276 lines) + monitoring.md (476 lines) + real-time.md (396 lines) = 1,148 lines total. Retained: all 7 resource types with code, monkey-patching + subclassing monitoring, container monitoring, queue statistics, event tracing (step + schedule), CSV export, matplotlib plotting, RealtimeEnvironment (factor, strict mode, HIL, periodic tasks, performance monitoring, conversion). Omitted: multiple-variable tracking class (duplicates SimulationData pattern shown inline), synchronized multi-device example (trivial variation of periodic task), verbose prose introductions already in SKILL.md.
