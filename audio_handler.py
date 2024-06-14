class AudioHandler:
    def __init__(self, bot):
        self.bot = bot
        self._queue = []
        self._current = None

    def clear_queue(self):
        self._queue = []

    def get_queue(self):
        return self._queue

    def set_current(self, current):
        self._current = current

    def get_current(self):
        return self._current

    def clear_current(self):
        self._current = None