"""Isolated sound preview worker: mixer only, no game window or engine import."""

import json
import sys
import threading
import time


def main():
    try:
        from pygame import mixer

        mixer.init()
        mixer.music.load(sys.argv[1])
        mixer.music.set_volume(float(sys.argv[2]))
        mixer.music.play()

        def commands():
            for line in sys.stdin:
                try:
                    mixer.music.set_volume(max(0, min(1, float(line))))
                except ValueError:
                    pass

        threading.Thread(target=commands, daemon=True).start()
        while mixer.music.get_busy():
            time.sleep(0.05)
        mixer.quit()
    except Exception as error:  # noqa: BLE001 -- report worker failures to the GUI
        print(json.dumps({"error": str(error)}, ensure_ascii=False), flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
