from inspect import Parameter, signature
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


@lru_cache(maxsize=4096)
def _callable_shape(method: callable) -> tuple[bool, int, int, int]:
    """Precompute the parameter shape used by ``check_signature``.

    Returns ``(has_var_positional, positional_count, required_count,
    required_max_index)`` so that the per-call checks only compare integers
    instead of walking the parameter list on every dispatch.
    """
    sig = _cached_signature(method)
    has_var_positional = False
    positional_count = 0
    required_count = 0
    required_max_index = -1
    index = 0
    for param in sig.parameters.values():
        kind = param.kind
        if kind == Parameter.VAR_POSITIONAL:
            has_var_positional = True
            continue
        if kind == Parameter.VAR_KEYWORD:
            continue
        if kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD):
            positional_count += 1
        if param.default == param.empty:
            required_count += 1
            required_max_index = index
        index += 1
    return has_var_positional, positional_count, required_count, required_max_index


def get_signature(method: callable, arguments: tuple, allow_none=True):
    check_signature(method, arguments, allow_none)
    return _cached_signature(method)


def check_signature(method: callable, arguments: tuple, allow_none=False):
    if not callable(method):
        raise NotCallableError(method)
    if arguments is None and not allow_none:
        raise NotNullError(method)
    # `None` means the method is called without arguments (see `call_method`);
    # remember this before `arguments` is normalized below.
    arguments_mean_no_call = arguments is None
    if type(arguments) is not list and type(arguments) is not tuple and type(arguments) is not dict:
        arguments = [arguments]
    try:
        (
            has_var_positional,
            positional_count,
            required_count,
            required_max_index,
        ) = _callable_shape(method)
    except ValueError:
        raise FirstArgumentShouldBeSelfError(method)
    # A required parameter sits at an index that receives no argument.
    if required_max_index >= len(arguments):
        raise WrongArgumentsError(method, arguments)
    argument_count = 0 if arguments_mean_no_call else len(arguments)
    # Required parameters that would never receive a value.
    if required_count > argument_count:
        raise WrongArgumentsError(method, arguments)
    # More arguments than the method can accept positionally.
    if not has_var_positional and argument_count > positional_count:
        raise WrongArgumentsError(method, arguments)


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
