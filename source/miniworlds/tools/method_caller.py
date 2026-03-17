from inspect import signature
from collections.abc import Iterable
from functools import lru_cache
from miniworlds.base.exceptions import (
    FirstArgumentShouldBeSelfError,
    NotCallableError,
    WrongArgumentsError,
    NotNullError,
)
from typing import Optional
import logging
import traceback
import sys
import os


logger = logging.getLogger(__name__)


@lru_cache(maxsize=4096)
def _cached_signature(method: callable):
    return signature(method)


def get_signature(method: callable, arguments: tuple, allow_none=True):
    check_signature(method, arguments, allow_none)
    return _cached_signature(method)


def check_signature(method: callable, arguments: tuple, allow_none=False):
    if not callable(method):
        raise NotCallableError(method)
    if arguments is None and not allow_none:
        raise NotNullError(method)
    if type(arguments) is not list and type(arguments) is not tuple and type(arguments) is not dict:
        arguments = [arguments]
    try:
        sig = _cached_signature(method)
    except ValueError:
        raise FirstArgumentShouldBeSelfError(method)
    i = 0
    for key, param in sig.parameters.items():
        if param.default == param.empty and i >= len(arguments):
            raise WrongArgumentsError(method, arguments)
        i = i + 1


def call_method(method: callable, arguments: Optional[tuple], allow_none=True):
    try:
        check_signature(method, arguments, allow_none=True)
        if arguments is None:
            method()
        else:
            if isinstance(arguments, Iterable):
                method(*arguments)
            else:
                method(arguments)
    except (ReferenceError, AttributeError) as e:
        # do nothing, if object does not exist.
        #print_filtered_traceback(e)
        raise 


def print_filtered_traceback(exc: Exception, match: str = None):
    if match is None:
        match = os.getcwd()

    tb = exc.__traceback__
    filtered_trace = []

    while tb:
        frame = tb.tb_frame
        filename = frame.f_code.co_filename
        if match in filename:
            lineno = tb.tb_lineno
            name = frame.f_code.co_name
            filtered_trace.append(f'  File "{filename}", line {lineno}, in {name}')
        tb = tb.tb_next

    logger.error("Traceback (most recent call last):")
    for line in filtered_trace:
        logger.error(line)
    logger.error("%s: %s", type(exc).__name__, exc)
