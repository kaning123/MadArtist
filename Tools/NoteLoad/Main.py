"""Load a ``.note`` file and render it to one WAV file with ``Tools.TTS``.

The note format is intentionally small and line-oriented.  For example::

    ~?bpm=120
    [00:00.0]一二三四
    c3-c3-c3-c3

Metadata lines start with ``~?`` and are ignored by the renderer.  A text line
may be followed by a note line; note names are separated by ``-``, commas, or
whitespace.  A text line without a note line is also accepted and is rendered
with ``None`` notes.

The TTS implementation in this repository requires ``VoicePth`` and
``IndexPath``.  They are stored in JSON so callers do not have to provide them
on every invocation.  Values passed explicitly to :func:`NoteLoadMain` update
that JSON file.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import wave
import copy
from pathlib import Path
from typing import Any, Iterable

from rich.logging import RichHandler
from rich.console import Console
console = Console()
console.print("[bold purple]MadArtist NoteLoad Module[/bold purple] - Version [bold blue]Alpha_0.0.1_202607[/bold blue]")

import file_lib as fl
ROOT_DIR = fl.get_parent_dir(fl.get_my_dir(),2)
import sys
new_path = copy.deepcopy(sys.path)
sys.path.append(str(ROOT_DIR))

try:
    import Tools.TTS as tts_module
except ImportError:
    sys.path = new_path
    raise ImportError("Tools.AutoTranslate module not found.")
finally:
    sys.path = new_path

# Keep logging configuration local to this module and use Rich for readable
# command-line diagnostics without changing the application's root logger.
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%Y-%m-%d %H:%M:%S]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)

_NOTE_SEPARATOR = re.compile(r"[-,\s]+")
_TEXT_LINE = re.compile(r"^\s*(?:\[[^\]]+\])?(?P<text>.*?)\s*$")
_DEFAULT_CONFIG = Path(__file__).with_name("tts_config.json")


def _load_tts_config(config_path: Path) -> dict[str, Any]:
    """Read the persisted TTS settings, returning an empty config if absent."""
    if not config_path.exists():
        return {}
    if not config_path.is_file():
        raise OSError(f"TTS config path is not a file: {config_path}")
    with config_path.open("r", encoding="utf-8") as config_file:
        config = json.load(config_file)
    if not isinstance(config, dict):
        raise ValueError(f"TTS config must contain a JSON object: {config_path}")
    return config


def _save_tts_config(config_path: Path, config: dict[str, Any]) -> None:
    """Persist TTS settings as UTF-8 JSON, creating the parent directory."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as config_file:
        json.dump(config, config_file, ensure_ascii=False, indent=2)
        config_file.write("\n")


def _parse_note_file(input_note: Path) -> tuple[list[str], list[list[str | None]]]:
    """Parse text and optional pitch lines from a ``.note`` file."""
    texts: list[str] = []
    notes: list[list[str | None]] = []
    lines = input_note.read_text(encoding="utf-8-sig").splitlines()
    index = 0

    while index < len(lines):
        raw_line = lines[index].strip()
        index += 1
        if not raw_line or raw_line.startswith("~?") or raw_line.startswith("#"):
            continue

        text_match = _TEXT_LINE.match(raw_line)
        if text_match is None:
            raise ValueError(f"Invalid .note text line {index}: {raw_line!r}")
        text = text_match.group("text").strip()
        if not text:
            raise ValueError(f"Empty .note text line {index}")

        pitch_values: list[str | None] = [None]
        if index < len(lines):
            candidate = lines[index].strip()
            if candidate and not candidate.startswith(("~?", "#", "[")):
                index += 1
                pitch_values = [
                    pitch for pitch in _NOTE_SEPARATOR.split(candidate) if pitch
                ]
                if not pitch_values:
                    pitch_values = [None]

        texts.append(text)
        notes.append(pitch_values)

    if not texts:
        raise ValueError(f".note file contains no renderable text: {input_note}")
    return texts, notes


def _iter_audio_paths(value: Any) -> Iterable[Path]:
    """Flatten the nested path structure returned by ``Tools.TTS``."""
    if isinstance(value, (str, Path)):
        yield Path(value)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _iter_audio_paths(item)
    elif isinstance(value, int):
        # 忽略整数，不产生任何路径，继续执行（生成器不终止）
        pass
    else:
        raise TypeError(f"Unsupported audio path returned by Tools.TTS: {value!r}, type: {type(value)}")


def _combine_wavs(audio_paths: Iterable[Path], output_wav: Path) -> None:
    """Concatenate WAV files, requiring compatible audio stream parameters."""
    paths = list(audio_paths)
    if not paths:
        raise ValueError("Tools.TTS returned no audio files")

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    first_params: wave._wave_params | None = None
    with output_wav.open("wb") as output_file:
        with wave.open(output_file, "wb") as output:
            for audio_path in paths:
                if not audio_path.is_file():
                    print(f"type of audiopath:{type(audio_path)}")
                    raise FileNotFoundError(f"TTS audio file does not exist: {audio_path}")
                with wave.open(str(audio_path), "rb") as source:
                    params = source.getparams()
                    if first_params is None:
                        first_params = params
                        output.setparams(params)
                    elif (params[:3], params[4:]) != (
                        first_params[:3],
                        first_params[4:],
                    ):
                        raise ValueError(
                            "TTS returned WAV files with incompatible audio parameters"
                        )
                    output.writeframes(source.readframes(source.getnframes()))


def NoteLoadMain(
    input_note: str | Path,
    output_wav: str | Path | None = None,
    *,
    VoicePth: str | Path | None = None,
    IndexPath: str | Path | None = None,
    tts_config: str | Path | None = None,
) -> str:
    """Render ``input_note`` through ``Tools.TTS`` and return the WAV path.

    ``VoicePth`` and ``IndexPath`` are optional when they have already been
    saved in the JSON config.  Supplying either value persists the new value.
    """
    input_path = Path(input_note)
    if not input_path.is_file():
        raise FileNotFoundError(f"Input .note file does not exist: {input_path}")

    output_path = (
        Path(output_wav) if output_wav is not None else input_path.with_suffix(".wav")
    )
    config_path = Path(tts_config) if tts_config is not None else _DEFAULT_CONFIG
    config = _load_tts_config(config_path)
    if VoicePth is not None:
        config["VoicePth"] = str(VoicePth)
    if IndexPath is not None:
        config["IndexPath"] = str(IndexPath)
    if VoicePth is not None or IndexPath is not None or not config_path.exists():
        _save_tts_config(config_path, config)

    voice_path = config.get("VoicePth")
    index_path = config.get("IndexPath")
    if not voice_path or not index_path:
        raise ValueError(
            f"TTS config must define VoicePth and IndexPath: {config_path}"
        )

    texts, notes = _parse_note_file(input_path)
    # Import lazily because Tools.TTS loads optional audio dependencies and
    # callers can validate note files without initializing the TTS backend.


    try:
        logger.info("Rendering %d note records from %s", len(texts), input_path)
        generated_audio = tts_module.TTS_Main(
            texts,
            notes=notes,
            VoicePth=voice_path,
            IndexPath=index_path,
        )
        _combine_wavs(_iter_audio_paths(generated_audio), output_path)
        logger.info("WAV generated: %s", output_path)
        return str(output_path)
    finally:
        # Tools.TTS starts a non-daemon VoiceChange thread during import.
        # Always stop it so a completed CLI invocation can exit normally.
        tts_module.KillServers()


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-note", required=True, help="Path to the .note file")
    parser.add_argument(
        "--output-wav",
        default=None,
        help="Output WAV path (default: input path with .wav suffix)",
    )
    parser.add_argument("--voice-pth", help="TTS VoicePth; persisted in JSON")
    parser.add_argument("--index-path", help="TTS IndexPath; persisted in JSON")
    parser.add_argument(
        "--tts-config",
        default=None,
        help=f"TTS JSON config path (default: {_DEFAULT_CONFIG})",
    )
    return parser


def main() -> int:
    """Run the command-line interface and return a process exit code."""
    arguments = _build_parser().parse_args()
    try:
        NoteLoadMain(
            arguments.input_note,
            arguments.output_wav,
            VoicePth=arguments.voice_pth,
            IndexPath=arguments.index_path,
            tts_config=arguments.tts_config,
        )
    except Exception:
        logger.exception("NoteLoad failed")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())