from typing import Callable

from celery import Celery, states
import os
import time
from dotenv import load_dotenv
import math
from random import random
from decimal import Decimal, getcontext

load_dotenv()

app = Celery('tasks', broker=os.getenv('CELERY_BROKER_URL'), backend=os.getenv('CELERY_RESULT_BACKEND'))


class PiCalculator:
    """
    Compute pi to n decimal places using the Chudnovsky algorithm.
    Tracks progress during computation.
    """

    def __init__(self, n: int, update_state: Callable):
        if n < 0:
            raise ValueError("n must be non-negative")
        self.n = n
        self.update_state = update_state
        self._progress = 0.0
        self.pi_value = None
        self.time_started = time.time()

    def compute(self):
        """
        Compute pi to n decimal
        """
        n = self.n
        guard = 10
        getcontext().prec = n + guard

        # determine number of terms needed
        terms = n // 14 + 3
        S = Decimal(0)

        for k in range(terms):
            num = Decimal(math.factorial(6 * k)) * Decimal(13591409 + 545140134 * k)
            den = (Decimal(math.factorial(3 * k)) *
                   (Decimal(math.factorial(k)) ** 3) *
                   (Decimal(640320) ** (3 * k)))
            term = (Decimal(-1) ** k) * num / den
            S += term
            # code works too fast – lets fix it
            time.sleep(random()*0.03)
            self.progress = (k + 1) / terms

        C = Decimal(426880) * Decimal(10005).sqrt()
        pi = C / S

        # quantize to n decimal places
        quant = Decimal(1).scaleb(-n)
        pi_q = pi.quantize(quant)

        s = format(pi_q, 'f')
        if '.' not in s:
            s += '.' + '0' * n
        else:
            have = len(s) - s.index('.') - 1
            if have < n:
                s += '0' * (n - have)
        self.pi_value = s
        self.progress = 1  # mark complete
        return s

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value: float):
        self.update_state(
            state=states.STARTED,
            meta={
                "progress": value,
                "comment": self.comment
            }
        )
        self._progress = value
    @property
    def comment(self):
        elapsed = time.time() - self.time_started
        if self.progress == 0:
            return "Starting up..."
        elif self.progress < 0.4:
            return f"Working... {self.progress*100:.1f}% done, elapsed {elapsed:.1f}s"
        elif self.progress < 0.6:
            eta = elapsed / self.progress * (1 - self.progress)
            return f"More than halfway there! {self.progress*100:.1f}% done, elapsed {elapsed:.1f}s, ETA {eta:.1f}s"
        elif self.progress < 1:
            return """I'm tired, boss. Tired of bein' on the road, lonely as a sparrow in the rain. Tired of not ever having me a buddy to be with, or tell me where we's coming from or goin' to or why. Mostly, I'm tired of people bein' ugly to each other. It feels like pieces of glass in my head. I'm tired of all the times I've wanted to help and couldn't. I'm tired of bein' in the dark. Mostly it's the pain. There's too much. If I could end it, I would. But I can't."""
        else:
            return f"Completed in {elapsed:.1f}s"

@app.task(bind=True)
def calculate_pi_with_things(self, digits: int):
    worker = PiCalculator(digits, update_state=self.update_state)
    result = worker.compute()
    return {"state": "SUCCESS", "result": result}
