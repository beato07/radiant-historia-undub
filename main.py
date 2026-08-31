"""Module for building undub CIA for Radiant Historia."""

import logging
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def run(cmd: list[str]) -> None:
    """Run a command."""
    subprocess.run(cmd, check=True, shell=False)


def clean_build(build_dir: Path) -> None:
    """Clean the build directory."""
    if not build_dir.exists():
        return
    for item in build_dir.iterdir():
        if item.suffix == ".cia":
            continue
        if item.is_file():
            logger.info("Removing %s", item.name)
            item.unlink()
        elif item.is_dir():
            logger.info("Removing %s", item.name)
            shutil.rmtree(item)


def get_rsf_path(rsf_dir: Path) -> Path:
    """Select region (EUR/USA) and return the RSF file path."""
    region_map = {
        1: "Radiant_Historia_EUR.rsf",
        2: "Radiant_Historia_USA.rsf",
    }
    while True:
        try:
            region = int(input("Select a region (1 - EUR, 2 - USA): "))
            if region not in region_map:
                logger.info("Invalid number. Please enter 1 or 2.\n")
                continue
            return rsf_dir / region_map[region]
        except ValueError:
            logger.info("Please enter a number (1 or 2).\n")
    return rsf_dir / region_map[1]


def extract_cia(build_dir: Path, cia_path: Path, ctrtool: Path, tdstool: Path) -> None:
    """Extract CIA from build directory."""
    run([
        ctrtool,
        "--contents", str(build_dir / "contents"),
        cia_path,
    ])

    run([
        tdstool,
        "-xvtf",
        "cxi", str(build_dir / "contents.0000.00000000"),
        "--header", str(build_dir / "header.bin"),
        "--logo", str(build_dir / "logo.bin"),
        "--plain", str(build_dir / "plain.bin"),
        "--exh", str(build_dir / "exh.bin"),
        "--exefs", str(build_dir / "exefs.bin"),
        "--romfs", str(build_dir / "romfs.bin"),
    ])

    run([
        tdstool,
        "-xvtf",
        "romfs", str(build_dir / "romfs.bin"),
        "--romfs-dir", str(build_dir / "romfs"),
    ])


def apply_mod(src_dir: Path, dst_dir: Path) -> None:
    """Apply MOD."""
    if not src_dir.exists():
        logger.error("[ERROR] %s directory does not exist.", src_dir)
        sys.exit(1)
    shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)


def build_cia(build_dir: Path, tdstool: Path, makerom: Path, rsf_eur: Path) -> None:
    """Build CIA."""
    run([
        tdstool,
        "-cvtf",
        "romfs", str(build_dir / "new_romfs.bin"),
        "--romfs-dir", str(build_dir / "romfs"),
    ])

    run([
        tdstool,
        "-cvtf",
        "cxi", str(build_dir / "content0.cxi"),
        "--header", str(build_dir / "header.bin"),
        "--exh", str(build_dir / "exh.bin"),
        "--logo", str(build_dir / "logo.bin"),
        "--plain", str(build_dir / "plain.bin"),
        "--exefs", str(build_dir / "exefs.bin"),
        "--romfs", str(build_dir / "new_romfs.bin"),
    ])

    run([
        makerom,
        "-v",
        "-f", "cia",
        "-o", str(build_dir / "Radiant_Historia.cia"),
        "-rsf", str(rsf_eur),
        "-content", str(build_dir / "content0.cxi") + ":0:0",
        "-content", str(build_dir / "contents.0001.00000001") + ":1:1",
        "-target", "t",
    ])


def build_undub(
        build_dir: Path,
        cia_path: Path,
        ctrtool: Path,
        tdstool: Path,
        makerom: Path,
        src_dir: Path,
        dst_dir: Path,
        rsf_path: Path,
) -> None:
    """Build undub CIA."""
    extract_cia(build_dir, cia_path, ctrtool, tdstool)
    apply_mod(src_dir, dst_dir)
    build_cia(build_dir, tdstool, makerom, rsf_path)
    clean_build(build_dir)


def main() -> None:
    """Run the main entry point of the program."""
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    if len(sys.argv) > 1 and sys.argv[1]:
        cia_path = Path(sys.argv[1])
        if not cia_path.exists():
            logger.error("File not found: %s", cia_path)
            sys.exit(1)
    else:
        cia_files = list(Path(".").glob("*.cia"))
        if len(cia_files) != 1:
            logger.error("Expected exactly one .cia file, found %d.", len(cia_files))
            sys.exit(1)
        cia_path = cia_files[0]

    # Paths
    script_dir = Path(__file__).resolve().parent.absolute()
    build_dir = script_dir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    mods_dir = script_dir / "mods"
    rsf_dir = script_dir / "rsf"
    tools_dir = script_dir / "tools"

    # Tools
    ctrtool = tools_dir / "ctrtool.exe"
    tdstool = tools_dir / "3dstool.exe"
    makerom = tools_dir / "makerom.exe"

    # RSF
    rsf_path = get_rsf_path(rsf_dir)

    # Mod src and dst
    src_dir = mods_dir / "romfs" / "Sound" / "se_voice"
    dst_dir = build_dir / "romfs" / "Sound" / "se_voice"

    build_undub(
        build_dir,
        cia_path,
        ctrtool,
        tdstool,
        makerom,
        src_dir,
        dst_dir,
        rsf_path,
    )

if __name__ == "__main__":
    main()
