from collections import defaultdict

class EventBus:
    _subscribers = defaultdict(list)

    @classmethod
    def subscribe(cls, event_type: str, callback):
        cls._subscribers[event_type].append(callback)

    @classmethod
    async def emit(cls, event_type: str, data):
        for callback in cls._subscribers[event_type]:
            await callback(data)
