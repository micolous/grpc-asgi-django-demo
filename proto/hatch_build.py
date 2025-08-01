"""
Build hook to write empty `__init__.py` and `py.typed` as artifacts, and a
FileDescriptorSet with imports.

This works around `hatch` not being able to exclude generated `_pb2.py` files
from the `sdist`, while also marking the module as "type friendly".

Adding a `descriptor_set` generator option to `hatch-protobuf` doesn't allow us
to set extra flags like `--include_imports`.
"""

import shlex
import subprocess
import sys
from functools import cached_property
from pathlib import Path
from sysconfig import get_path
from typing import Any, Dict, List

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


# Empty files to write
FILES = {
    "__init__.py",
    "py.typed",
}


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: Dict[str, Any]) -> None:
        del version
        self.app.display_info(f"Writing empty files to: {self._output_path}")

        self._output_path.mkdir(parents=True, exist_ok=True)

        output_files = [(self._output_path / f) for f in FILES]

        for f in output_files:
            f.touch()
            build_data["artifacts"].append(f.as_posix())

        # Build a FileDescriptorSet with imports
        fds_path = self._output_path / "service.binpb"
        args = [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            "-I",
            get_path("purelib"),
            "-I",
            "proto",
            "--include_imports",
            f"--descriptor_set_out={fds_path}",
            "proto/grpc_asgi_django_demo/proto/v1/service.proto",
        ]
        self.app.display_info(f"Running {shlex.join(args)}")
        subprocess.run(args, cwd=Path(self.root), check=True)
        build_data["artifacts"].append(fds_path.as_posix())

    @cached_property
    def _output_path(self) -> Path:
        return Path(self.config.get("output_path", "."))

    def clean(self, versions: List[str]) -> None:
        del versions
        (self._output_path / "__init__.py").unlink(missing_ok=True)
        (self._output_path / "py.typed").unlink(missing_ok=True)
        (self._output_path / "service.binpb").unlink(missing_ok=True)
