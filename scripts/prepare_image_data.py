"""Inventory a downloaded Roboflow YOLO export without changing its images."""

import argparse
import csv
from collections import Counter
from pathlib import Path

SOURCE_URL = "https://universe.roboflow.com/rnomo/lost-and-found-nlb4x-e6ayk/dataset/2"
FIELDS = ["image_id", "original_filename", "class", "split", "source_dataset", "source_creator",
          "source_version", "licence", "width", "height", "annotation_type", "annotation_file", "processing_status"]


def prepare(source: Path, output: Path) -> dict:
    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError as exc:
        raise RuntimeError("Install Pillow to validate downloaded images") from exc
    if not source.is_dir():
        raise FileNotFoundError(f"Downloaded dataset directory absent: {source}")
    classes_file = next((p for p in (source / "data.yaml", source / "data.yml") if p.exists()), None)
    if classes_file is None:
        raise FileNotFoundError("YOLO data.yaml missing; cannot verify class indices")
    # PyYAML is optional; keep this script dependency-light for a standard Roboflow export.
    import ast
    names_line = next((line.partition(":")[2].strip() for line in classes_file.read_text(encoding="utf-8").splitlines()
                       if line.startswith("names:")), None)
    if not names_line:
        raise ValueError("Expected inline names list in data.yaml")
    names = ast.literal_eval(names_line)
    if not isinstance(names, list):
        raise ValueError("Class names must be a list")
    rows = []
    counts = Counter()
    for split in ("train", "valid", "test"):
        image_dir = source / split / "images"
        if not image_dir.exists():
            continue
        for path in sorted(image_dir.iterdir()):
            if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            status, width, height = "ok", "", ""
            try:
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    width, height = image.size
            except (OSError, UnidentifiedImageError):
                status = "unreadable"
            annotation = source / split / "labels" / (path.stem + ".txt")
            class_ids = set()
            if annotation.exists():
                for line in annotation.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        class_ids.add(int(line.split()[0]))
            else:
                status = "missing_annotation" if status == "ok" else status
            if any(index < 0 or index >= len(names) for index in class_ids):
                status = "invalid_class_index"
            if not class_ids:
                class_ids = {None}
            for index in sorted(class_ids, key=lambda item: -1 if item is None else item):
                label = names[index] if index is not None and 0 <= index < len(names) else ""
                rows.append({"image_id": path.stem, "original_filename": path.name, "class": label,
                             "split": split, "source_dataset": SOURCE_URL, "source_creator": "rnomo",
                             "source_version": "2", "licence": "CC BY 4.0", "width": width, "height": height,
                             "annotation_type": "YOLO bounding box", "annotation_file": str(annotation.relative_to(source)) if annotation.exists() else "",
                             "processing_status": status})
                counts[(split, label, status)] += 1
    if not rows:
        raise ValueError("No images found in train/valid/test folders")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return {"unique_images": len({(r["split"], r["original_filename"]) for r in rows}),
            "metadata_rows": len(rows), "counts": {str(key): value for key, value in counts.items()}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Path to downloaded YOLO export")
    parser.add_argument("--output", type=Path, default=Path("data/metadata/image_metadata.csv"))
    args = parser.parse_args()
    print(prepare(args.source, args.output))
