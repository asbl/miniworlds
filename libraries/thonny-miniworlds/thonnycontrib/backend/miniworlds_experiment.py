"""Thonny 4.1 CPython adapter; loaded from Thonny's frontend plugin path."""

from thonnycontrib.miniworlds.live_runtime import RuntimeHost


def load_plugin(backend):
    def prepare(source, command):
        configuration = command.get("miniworlds_experiment")
        if configuration is None:
            return source
        try:
            from miniworlds.base import runtime_host
        except ImportError as error:
            raise RuntimeError(
                "Das Objektlabor benötigt miniworlds mit IDE-Host-API 1. Bitte die Bibliothek aktualisieren und Thonnys Stop/Restart verwenden."
            ) from error
        if getattr(runtime_host, "API_VERSION", 0) != 1:
            raise RuntimeError(
                "Die IDE-Host-API dieser miniworlds-Version passt nicht zum Plugin. Bitte Bibliothek und Plugin aktualisieren."
            )

        runtime_host.install(
            RuntimeHost(configuration, backend.get_main_module().__dict__)
        )
        # Compile with the original filename; the editor snapshot is never
        # written back into pupil files or rewritten to change run semantics.
        return configuration["source"]

    backend.add_source_preprocessor(prepare)
