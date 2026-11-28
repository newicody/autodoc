# ControlProxy operational plan after 0105

0105 locks the priority/admission direction before more runtime wiring.

## Locked roadmap

```text
0101 architecture simplification lock
0102 existing paths audit
0103 RouteRuntimeManager runtime facade
0104 thin ControlProxy route runtime handler
0105 priority/admission lock
0106 EventBus vs data plane cleanup
0107 root graph and individual graph reconciliation
```

## 0105 decision

PriorityQueue is the only deterministic execution ordering mechanism.

PolicyEngine is minimal admission before queue.

Dispatcher is EventType -> Handler only.

ControlProxy / RouteRuntimeManager does not compute global priorities.

ControlProxy / RouteRuntimeManager does not decide policy/zone admission.

EventBus is observation only.

Route mmap/eventfd is data plane, not EventBus.

## What this prevents

```text
ControlProxy becoming a Scheduler bis
Dispatcher becoming a business router
PolicyEngine becoming a specialist strategy engine
EventBus being duplicated by ControlProxy
mmap/eventfd being described as an application bus
priority logic being hidden after enqueue
```

## What remains allowed

A future explicit priority policy may exist if it stays before enqueue:

```text
EventClassPolicy + bounded GlobalContextSnapshot -> explicit priority value
```

A future specialist may produce priority hints if they travel through typed
commands and the normal kernel path.

RouteRuntimeManager may continue to manage ControlFS, generations, lifecycle,
locks, placement, mmap/eventfd data plane, and journal input.
