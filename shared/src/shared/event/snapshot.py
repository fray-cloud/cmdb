class SnapshotStrategy:
    def __init__(self, every_n_events: int = 100) -> None:
        self.every_n_events = every_n_events

    def should_snapshot(self, current_version: int, last_snapshot_version: int) -> bool:
        return (current_version - last_snapshot_version) >= self.every_n_events
