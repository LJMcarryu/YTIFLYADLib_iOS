#!/usr/bin/env python3
"""校验 CI 的发布版本契约，按渠道既有模式读取固定 Tag 状态。"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess

from release_metadata_control import read_release_control


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--channel", required=True)
    parser.add_argument("--validation-mode", required=True)
    parser.add_argument("--tag-state-mode", action="append", default=[])
    arguments = parser.parse_args(argv)
    mode = arguments.validation_mode
    state_path = Path("release-state.json")
    if mode in arguments.tag_state_mode:
        state_path = Path(os.environ["RUNNER_TEMP"]) / "release-control-state.json"
        with state_path.open("wb") as output:
            subprocess.run(
                ["git", "show", f"refs/tags/{os.environ['RELEASE_TAG']}:release-state.json"],
                check=True, stdout=output,
            )
    read_release_control(
        Path(__file__).resolve().with_name("release-control.json"),
        repository=arguments.repository,
        channel=arguments.channel,
        release_state_path=state_path,
        validation_mode=mode,
    )
    print("release-control 版本契约校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
