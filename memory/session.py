import threading
import time
from collections import OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Message:
    role: Literal["user", "assistant"]
    content: str
    ts: float


class SessionStore:
    """In-memory chat history: the last `max_messages` messages per session.

    Sessions expire after `ttl_seconds` of inactivity, and at most `max_sessions`
    are kept (least recently used is evicted). Fine for a single-process demo;
    a multi-instance deployment would swap this for Redis behind the same API.
    """

    def __init__(
        self,
        max_messages: int = 5,
        ttl_seconds: int = 1800,
        max_sessions: int = 1000,
        clock: Callable[[], float] = time.time,
    ):
        self._max_messages = max_messages
        self._ttl = ttl_seconds
        self._max_sessions = max_sessions
        self._clock = clock
        self._sessions: OrderedDict[str, deque[Message]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, session_id: str) -> list[Message]:
        with self._lock:
            self._evict_expired()
            messages = self._sessions.get(session_id)
            return list(messages) if messages else []

    def append(self, session_id: str, user: str, assistant: str) -> None:
        now = self._clock()
        with self._lock:
            self._evict_expired()
            messages = self._sessions.setdefault(session_id, deque(maxlen=self._max_messages))
            messages.append(Message("user", user, now))
            messages.append(Message("assistant", assistant, now))
            self._sessions.move_to_end(session_id)
            while len(self._sessions) > self._max_sessions:
                self._sessions.popitem(last=False)

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def _evict_expired(self) -> None:
        cutoff = self._clock() - self._ttl
        expired = [sid for sid, msgs in self._sessions.items() if msgs[-1].ts < cutoff]
        for sid in expired:
            del self._sessions[sid]
