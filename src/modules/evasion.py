import time
import numpy as np
from src.core.config import settings

def poisson_jitter(mean_delay: float) -> float:
    """Generate human-like delay using a Poisson distribution.
    A simple uniform random isn't human. Poisson models the number 
    of events occurring within a fixed time interval. We use it to 
    determine the wait time.
    """
    delay = np.random.poisson(mean_delay)
    # Ensure minimum 1 second delay so we don't accidentally DDoSing
    return max(1.0, float(delay))

def apply_jitter(speed: str = "normal"):
    """Pauses execution applying an evasion jitter logic."""
    if speed == "fast":
        mean = settings.JITTER_MEAN_FAST
    elif speed == "slow":
        mean = settings.JITTER_MEAN_SLOW
    else:
        mean = settings.JITTER_MEAN_NORMAL
        
    delay = poisson_jitter(mean)
    time.sleep(delay)
