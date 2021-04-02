from .supervisor import Supervisor
from .normalizer import normalize_to_schedulable


def run(*args):
    return supervise(*args).run()


def supervise(*args):
    schedulable = [normalize_to_schedulable(x) for x in args]
    return Supervisor(*schedulable)
