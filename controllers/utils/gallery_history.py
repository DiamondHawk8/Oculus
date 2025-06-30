class GalleryHistory:
    def __init__(self):
        self._history: list[str] = []
        self._cursor: int = -1

    def push(self, folder: str) -> bool:
        """
        Adds a folder to the history stack if it's different from the current entry.
        :param folder: Folder to add to the history stack.
        :return: Returns True if the history changed
        """
        if self._cursor >= 0 and self._history[self._cursor] == folder:
            return False

        self._history = self._history[: self._cursor + 1]
        self._history.append(folder)
        self._cursor += 1
        return True

    def step(self, delta: int) -> str | None:
        """
        Moves cursor by delta and returns new folder, or None if invalid
        :param delta: step to move cursor by
        :return:
        """
        next_cursor = self._cursor + delta
        if 0 <= next_cursor < len(self._history):
            self._cursor = next_cursor
            return self._history[self._cursor]
        return None

    def can_go_back(self) -> bool:
        return self._cursor > 0

    def can_go_forward(self) -> bool:
        return self._cursor + 1 < len(self._history)

    def current(self) -> str | None:
        """
        Returns current position in history stack
        :return:
        """
        if 0 <= self._cursor < len(self._history):
            return self._history[self._cursor]
        return None
