import argparse
from pathlib import Path

import cv2
from PIL import Image, ImageSequence


IMAGE_EXTENSIONS = {".gif"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
DEFAULT_INPUT = Path("image") / "itachi_skill.gif"
DEFAULT_OUTPUT_ROOT = Path("output") / "extracted_frames"


def ensure_output_dir(input_path: Path, output_dir: Path | None) -> Path:
    target = output_dir or DEFAULT_OUTPUT_ROOT / input_path.stem
    target.mkdir(parents=True, exist_ok=True)
    return target


def extract_gif_frames(input_path: Path, output_dir: Path, prefix: str) -> int:
    with Image.open(input_path) as gif:
        for index, frame in enumerate(ImageSequence.Iterator(gif)):
            frame_path = output_dir / f"{prefix}_{index:04d}.png"
            frame.convert("RGBA").save(frame_path)
        return index + 1 if "index" in locals() else 0


def extract_video_frames(input_path: Path, output_dir: Path, prefix: str, every: int) -> int:
    video = cv2.VideoCapture(str(input_path))
    if not video.isOpened():
        raise RuntimeError(f"Cannot open video: {input_path}")

    saved_count = 0
    frame_index = 0
    while True:
        ok, frame = video.read()
        if not ok:
            break

        if frame_index % every == 0:
            frame_path = output_dir / f"{prefix}_{saved_count:04d}.png"
            cv2.imwrite(str(frame_path), frame)
            saved_count += 1

        frame_index += 1

    video.release()
    return saved_count


def extract_frames(input_path: Path, output_dir: Path | None, every: int) -> tuple[Path, int]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if every < 1:
        raise ValueError("--every must be at least 1")

    target_dir = ensure_output_dir(input_path, output_dir)
    prefix = input_path.stem
    suffix = input_path.suffix.lower()

    if suffix in IMAGE_EXTENSIONS:
        count = extract_gif_frames(input_path, target_dir, prefix)
    elif suffix in VIDEO_EXTENSIONS:
        count = extract_video_frames(input_path, target_dir, prefix, every)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    return target_dir, count


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract frames from a GIF or video into PNG images.")
    parser.add_argument("input", nargs="?", default=str(DEFAULT_INPUT), help="Path to GIF/video file.")
    parser.add_argument("-o", "--output", default=None, help="Output folder. Defaults to output/extracted_frames/<file_name>.")
    parser.add_argument("--every", type=int, default=1, help="For videos, save every Nth frame.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output) if args.output else None
    target_dir, count = extract_frames(input_path, output_dir, args.every)
    print(f"Extracted {count} frame(s) to {target_dir}")


if __name__ == "__main__":
    main()
