import os
import sys
from functools import lru_cache
from pathlib import Path

import miniworlds.base.app as app


class FileManager:

    @staticmethod
    def _platform():
        return app.App.get_platform()

    @staticmethod
    def _base_path():
        return app.App.get_path()

    @staticmethod
    def clear_cache():
        FileManager._get_path_with_file_ending_cached.cache_clear()

    @staticmethod
    def relative_to_absolute_path(path):
        return FileManager._platform().relative_to_absolute_path(str(path))

    @staticmethod
    def has_ending(path):
        return "." in path

    @staticmethod
    def get_path_with_file_ending(path, file_endings):
        return FileManager._get_path_with_file_ending_cached(
            path,
            tuple(file_endings),
            FileManager._base_path(),
        )

    @staticmethod
    @lru_cache(maxsize=2048)
    def _get_path_with_file_ending_cached(path, file_endings, base_path):
        return FileManager._platform().resolve_path_with_file_endings(
            path,
            file_endings,
            base_path=base_path,
        )

    @staticmethod
    def _get_full_path_for_endings(prefix, path, file_endings):
        for filename_extension in file_endings:
            relative_path = prefix + path + "." + filename_extension
            if FileManager._base_path():
                relative_path = FileManager._platform().join_path(FileManager._base_path(), relative_path)
            if FileManager._platform().path_is_file(relative_path):
                full_path = FileManager.relative_to_absolute_path(relative_path)
                return full_path

    @staticmethod
    def get_image_path(path):
        canonical_path = FileManager.relative_to_absolute_path(path)
        if FileManager._platform().path_is_file(canonical_path):
            return Path(canonical_path)
        else:
            return FileManager.get_path_with_file_ending(path, ["jpg", "jpeg", "png", "JPG", "JPEG", "PNG"])
            # else:
            #    return file_manager.FileManager.get_path_with_file_ending(
            #        canonical_path.split(".")[0], ["jpg", "jpeg", "png"]
            #    )
