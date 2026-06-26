from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Literal

import cv2
import numpy as np

Category = Literal[
    "male_tall",
    "male_rich",
    "male_handsome",
    "female_fair",
    "female_rich",
    "female_beautiful",
]

CARD_CATEGORIES: Dict[str, str] = {
    "male_tall": "男高",
    "male_rich": "男富",
    "male_handsome": "男帅",
    "female_fair": "女白",
    "female_rich": "女富",
    "female_beautiful": "女美",
}


def crop_big_card(
    source_path: Path,
    output_dir: Path,
    card_id: str,
    margin_ratio: float = 0.02,
) -> List[Path]:
    """Crop one 9x3 big card into left 4x3 and right 5x3 images.

    MVP assumption:
    - The uploaded photo is already close to a full-card crop.
    - We do not delete or deduplicate anything.
    - Left crop uses columns 1-4, right crop uses columns 5-9.

    TODO:
    - Detect outer card boundary.
    - Apply perspective correction.
    - Let users manually adjust crop box and split line.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    image = cv2.imdecode(np.fromfile(str(source_path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Cannot read image: {source_path}")

    h, w = image.shape[:2]
    margin_x = int(w * margin_ratio)
    margin_y = int(h * margin_ratio)

    # Trim a tiny outer margin only if requested. This is conservative to avoid losing content.
    x0 = max(0, margin_x)
    y0 = max(0, margin_y)
    x1 = min(w, w - margin_x)
    y1 = min(h, h - margin_y)
    card = image[y0:y1, x0:x1]

    card_h, card_w = card.shape[:2]
    col_w = card_w / 9.0

    # Use a 1-2 pixel neutral gap around the split to avoid duplicate visual content.
    split_x = int(round(col_w * 4))
    gap = max(1, int(card_w * 0.002))

    left = card[:, : max(0, split_x - gap)]
    right = card[:, min(card_w, split_x + gap) :]

    left_path = output_dir / f"{card_id}_left_4x3.png"
    right_path = output_dir / f"{card_id}_right_5x3.png"
    _write_image(left_path, left)
    _write_image(right_path, right)
    return [left_path, right_path]


def _write_image(path: Path, image) -> None:
    success, encoded = cv2.imencode(path.suffix, image)
    if not success:
        raise ValueError(f"Cannot encode image: {path}")
    encoded.tofile(str(path))
