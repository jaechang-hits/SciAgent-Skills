# SimPy Process & Events Guide

Event lifecycle, composite events, process interaction patterns, and advanced synchronization.

## Event Lifecycle

Events progress through three states:

1. **Not triggered** — initial state (`triggered=False`, `processed=False`)
2. **Triggered** — scheduled in event queue (`triggered=True`, `processed=False`)
3. **Processed** — removed from queue, callbacks executed (`triggered=True`, `processed=True`)

```python
import simpy

env = simpy.Environment()
event = env.event()
print(f'Triggered: {event.triggered}, Processed: {event.processed}')  # False, False

event.succeed(value='result')
print(f'Triggered: {event.triggered}')  # True, not yet processed

env.run()
print(f'Processed: {event.processed}, Value: {event.value}')  # True, 'result'
```

## Event Triggering Methods

```python
# succeed(value=None) — mark as successful
event = env.event()
event.succeed(value='Success!')

# fail(exception) — mark as failed
event2 = env.event()
event2.fail(ValueError('Something went wrong'))

def catcher(env, event):
    try:
        yield event
    except ValueError as e:
        print(f'Caught: {e}')

# trigger(event) — copy another event's outcome
event3 = env.event()
event3.trigger(event)  # Same outcome as event
```

## Composite Events

### AllOf — Wait for All

```python
def parallel_tasks(env):
    t1 = env.timeout(3, value='Task 1')
    t2 = env.timeout(5, value='Task 2')
    t3 = env.timeout(4, value='Task 3')

    # Explicit form
    results = yield simpy.AllOf(env, [t1, t2, t3])
    print(f'All done at {env.now}')  # 5
    print(f'Results: {results}')  # Dict mapping events → values

    # Operator shorthand
    t4 = env.timeout(2)
    t5 = env.timeout(3)
    yield t4 & t5
    print(f'Both done at {env.now}')  # 8
```

### AnyOf — Wait for First

```python
def race(env):
    fast = env.timeout(2, value='Fast')
    slow = env.timeout(10, value='Slow')

    results = yield simpy.AnyOf(env, [fast, slow])
    print(f'First at {env.now}')  # 2
    # results contains only completed events

    # Operator shorthand
    yield env.timeout(5) | env.timeout(3)  # Resumes at 3
```

### Timeout with Cancellation Pattern

```python
def process_with_timeout(env):
    work = env.timeout(10, value='Work complete')
    timeout = env.timeout(5, value='Timeout!')

    result = yield work | timeout
    if work in result:
        print(f'Work completed: {result[work]}')
    else:
        print(f'Timed out: {result[timeout]}')
```

## Callbacks

```python
def my_callback(event):
    print(f'Callback: event value = {event.value}')

event = env.timeout(5, value='Done')
event.callbacks.append(my_callback)
# Callback fires when event is processed
# Note: yielding an event automatically adds the process resume as callback
```

## Event Sharing (Broadcasting)

Multiple processes can yield the same event — all resume when it triggers.

```python
def waiter(env, name, event):
    value = yield event
    print(f'{name} got "{value}" at {env.now}')

def broadcaster(env, event):
    yield env.timeout(5)
    event.succeed(value='Go!')

env = simpy.Environment()
signal = env.event()
env.process(waiter(env, 'P1', signal))
env.process(waiter(env, 'P2', signal))
env.process(waiter(env, 'P3', signal))
env.process(broadcaster(env, signal))
env.run()
# All three waiters resume at time 5
```

## Process Interaction Patterns

### Sequential Execution

```python
def task(env, name, duration):
    yield env.timeout(duration)
    return f'{name} result'

def sequential(env):
    r1 = yield env.process(task(env, 'A', 5))
    r2 = yield env.process(task(env, 'B', 3))
    r3 = yield env.process(task(env, 'C', 4))
    # Total time: 12
```

### Parallel Execution

```python
def parallel(env):
    t1 = env.process(task(env, 'A', 5))
    t2 = env.process(task(env, 'B', 3))
    t3 = env.process(task(env, 'C', 4))

    results = yield t1 & t2 & t3
    # Total time: 5 (max of individual times)
    print(f'A: {t1.value}, B: {t2.value}, C: {t3.value}')
```

### First-to-Complete

```python
def first_responder(env):
    s1 = env.process(task(env, 'Server1', 5))
    s2 = env.process(task(env, 'Server2', 3))
    s3 = env.process(task(env, 'Server3', 7))

    result = yield s1 | s2 | s3
    winner = list(result.values())[0]
    print(f'{winner} responded first at {env.now}')  # Server2 at 3
```

## Process Interruption

### Basic Interrupt

```python
def worker(env):
    try:
        yield env.timeout(10)
        print('Work completed')
    except simpy.Interrupt as interrupt:
        print(f'Interrupted: {interrupt.cause} at {env.now}')

def boss(env, worker_proc):
    yield env.timeout(5)
    worker_proc.interrupt(cause='urgent task')

env = simpy.Environment()
w = env.process(worker(env))
env.process(boss(env, w))
env.run()
```

### Resumable Work After Interrupt

```python
def resumable_worker(env):
    work_left = 10
    while work_left > 0:
        try:
            start = env.now
            yield env.timeout(work_left)
            work_left = 0
            print(f'Completed at {env.now}')
        except simpy.Interrupt:
            work_left -= (env.now - start)
            print(f'Interrupted! {work_left:.1f} left at {env.now}')
```

### Interrupt with Cause Dispatch

```python
def machine(env, name):
    while True:
        try:
            yield env.timeout(5)  # Operate
        except simpy.Interrupt as interrupt:
            if interrupt.cause == 'maintenance':
                yield env.timeout(2)  # Maintenance
            elif interrupt.cause == 'emergency':
                print(f'{name}: emergency stop')
                break
```

## Barrier Synchronization

```python
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

def worker(env, barrier, name, work_time):
    yield env.timeout(work_time)
    print(f'{name} reached barrier at {env.now}')
    yield barrier.wait()
    print(f'{name} passed barrier at {env.now}')

env = simpy.Environment()
barrier = Barrier(env, 3)
env.process(worker(env, barrier, 'A', 3))
env.process(worker(env, barrier, 'B', 5))
env.process(worker(env, barrier, 'C', 7))
env.run()
# All pass barrier at time 7
```

## Handshake Protocol

```python
def sender(env, req_event, ack_event):
    for i in range(3):
        req_event.succeed(value=f'Request {i}')
        yield ack_event
        print(f'Sender: ack received at {env.now}')
        req_event = env.event()
        ack_event = env.event()
        yield env.timeout(1)

def receiver(env, req_event, ack_event):
    for i in range(3):
        request = yield req_event
        print(f'Receiver: got {request} at {env.now}')
        yield env.timeout(2)  # Process
        ack_event.succeed()
        req_event = env.event()
        ack_event = env.event()
```

## Event Chaining

```python
def chained(env):
    events = [env.event() for _ in range(3)]

    def trigger_sequence(env):
        for i, e in enumerate(events):
            yield env.timeout(2)
            e.succeed(value=f'Step {i}')

    env.process(trigger_sequence(env))

    for e in events:
        val = yield e
        print(f'{val} at {env.now}')
    # Step 0 at 2, Step 1 at 4, Step 2 at 6
```

Condensed from original: events.md (375 lines) + process-interaction.md (425 lines) = 800 lines total. Retained: event lifecycle, all trigger methods (succeed/fail/trigger), AllOf/AnyOf with operator syntax, callbacks, event sharing/broadcasting, timeout-with-cancellation, sequential/parallel/first-to-complete patterns, all interrupt patterns (basic, resumable, cause dispatch), barrier synchronization, handshake protocol, event chaining. Omitted: conditional events (trivial if/else with timeout — covered in SKILL.md Core API), verbose prose introductions.
