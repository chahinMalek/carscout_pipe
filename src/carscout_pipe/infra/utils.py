import signal
from contextlib import contextmanager


@contextmanager
def timeout(seconds):
    """
    Context manager that raises TimeoutError if the code block takes longer than specified seconds.
    
    Args:
        seconds (int): Maximum time to allow the code block to run
        
    Raises:
        TimeoutError: If the code block execution exceeds the timeout
        
    Example:
        >>> with timeout(5):
        ...     time.sleep(10)  # This will raise TimeoutError after 5 seconds
    """
    def timeout_handler(signum, frame):
        raise TimeoutError("Timed out!")

    # Set the signal handler and alarm
    original_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        # Disable the alarm and restore the original handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler)
