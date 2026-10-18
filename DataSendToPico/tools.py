import functools
import time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

class Colors:
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def t():
    """time """
    return time.strftime("%H:%M:%S",
             time.gmtime(time.time()))

def RequestReport(func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        # drop `self` (first positional arg) so we only show the real arguments
        shown_args = args[1:] if args else ()
        arg_str = ", ".join(
            [repr(a) for a in shown_args] +
            [f"{k}={v!r}" for k, v in kwargs.items()]
        )

        start = time.perf_counter()
        print(
            f"{Colors.OKBLUE}{t()}{Colors.ENDC} | requesting: "
            f"{Colors.BOLD}{func.__name__}{Colors.ENDC}({arg_str}) ",
            end="", flush=True,
        )
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = round((time.perf_counter() - start) * 1000, ndigits=2)
            print(f"| finished in {Colors.UNDERLINE}{elapsed}ms{Colors.ENDC}", flush=True)

    return wrapper

class Error(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

def RequestFailCheck(rec:bool, fin:bool)->None:
    # case of both being true (failing is not handled) (hoping for the best)
    # both false : all good
    if not rec and not fin:
        return

    # rec fail
    if rec:
        raise Error("\n" + Colors.FAIL + "="*20 + "\n" + "    RECEIVE ERROR " + "\n" + "="*20 + Colors.ENDC)

    # rec fail
    if fin:
        raise Error("\n" + Colors.FAIL + "="*20 + "\n" + "    FINISH ERROR " + "\n" + "="*20 + Colors.ENDC)

