
def idle_minutes(start_timestamp, end_timestamp):
    """Return elapsed idle duration in whole minutes."""
    seconds = max(0, (end_timestamp - start_timestamp).total_seconds())
    return round(seconds / 60, 2)
