#!/usr/bin/env python3
"""Test typical student errors to see the error messages."""

import sys
sys.path.insert(0, '/app/source')

from miniworlds import World, Actor
from miniworlds.positions import vector

def test_error_1_position_format():
    """Error: Wrong position format"""
    print("\n=== TEST 1: Wrong position format ===")
    try:
        world = World()
        actor = Actor()
        actor.position = [100, 200]  # Wrong: list instead of tuple
    except Exception as e:
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")

def test_error_2_vector_direction():
    """Error: Wrong direction string"""
    print("\n=== TEST 2: Wrong Vector direction ===")
    try:
        v = vector.Vector()
        v.direction = "forward"  # Wrong: should be "up", "down", etc.
    except Exception as e:
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")

def test_error_3_timer_negative():
    """Error: Negative timer interval"""
    print("\n=== TEST 3: Negative timer interval ===")
    try:
        from miniworlds import Timer
        timer = Timer(interval=-5)
    except Exception as e:
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")

def test_error_4_timer_wrong_type():
    """Error: Wrong timer type"""
    print("\n=== TEST 4: Wrong timer type ===")
    try:
        from miniworlds import Timer
        timer = Timer(interval="5")  # Wrong: string instead of number
    except Exception as e:
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")

def test_error_5_vector_multiply():
    """Error: Wrong vector operation"""
    print("\n=== TEST 5: Unsupported Vector operation ===")
    try:
        v = vector.Vector(10, 20)
        result = v * "hello"  # Wrong type
    except Exception as e:
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")

def test_error_6_wrong_filter():
    """Error: Wrong sensor filter"""
    print("\n=== TEST 6: Wrong sensor filter type ===")
    try:
        world = World()
        actor = Actor()
        # Try to filter with wrong type
        actors = actor.detect_actors(actor_type=123)  # Should be Actor class or string
    except Exception as e:
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")

def test_error_7_button_text():
    """Error: Wrong button text type"""
    print("\n=== TEST 7: Wrong button text type ===")
    try:
        from miniworlds.actors.widgets import Button
        button = Button(position=(100, 100), text=123)  # Should be string
    except Exception as e:
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")

def test_error_8_origin_invalid():
    """Error: Invalid origin value"""
    print("\n=== TEST 8: Invalid origin value ===")
    try:
        world = World()
        actor = Actor()
        actor.origin = "middle"  # Should be "center" or "topleft"
    except Exception as e:
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")

if __name__ == "__main__":
    test_error_1_position_format()
    test_error_2_vector_direction()
    test_error_3_timer_negative()
    test_error_4_timer_wrong_type()
    test_error_5_vector_multiply()
    test_error_6_wrong_filter()
    test_error_7_button_text()
    test_error_8_origin_invalid()
