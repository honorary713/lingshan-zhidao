from collections import defaultdict


class ConversationMemory:
    def __init__(self, max_messages=20):
        self._history = defaultdict(list)
        self.max_messages = max_messages

    def add(self, session_id: str, role: str, content: str) -> None:
        self._history[session_id].append({
            "role": role,
            "content": content,
        })

        if len(self._history[session_id]) > self.max_messages:
            self._history[session_id] = self._history[session_id][-self.max_messages:]

    def get(self, session_id: str) -> list[dict]:
        return list(self._history.get(session_id, []))


conversation_memory = ConversationMemory()