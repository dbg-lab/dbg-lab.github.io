#!/usr/bin/env python3
"""Convert a raw headshot into the site's people-photo house style.

    python3 scripts/make_headshot.py raw.jpg static/images/people/first-last.png

Produces a 1000x1000 PNG: subject cut out of its original background and placed
on the flat brand blue (RGB 186,223,255) used by the other member photos.

Keep the untouched source alongside it in static/images/people/orig/ so the crop
can be redone later without re-downloading.

Requires: pip install rembg pillow opencv-python numpy
The YuNet face model is downloaded once into scripts/.cache/.

Alignment
---------
Reference numbers were measured from seth-anderson.png. The head is placed by
averaging two scale estimates:

  * interocular distance  -- tracks face size, but ignores hair volume, so tall
    hair alone comes out oversized and jammed against the top edge;
  * crown-to-eye distance -- accounts for hair, but over-shrinks those faces.

Averaging them keeps heads visually equal across very different hairstyles.
The photo is then aligned on the eye line, which is what reads as consistent
when the cards sit in a row. Cards render the image as a 170px circle
(border-radius: 50%), so the square's corners are never visible.
"""

import sys
import urllib.request
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

BG = (186, 223, 255)
SIZE = 1000

# Measured from static/images/people/seth-anderson.png at 1000x1000.
REF_HEAD_TOP = 53.0
REF_EYE_Y = 358.3
REF_IOD = 189.4
REF_BLOCK = REF_EYE_Y - REF_HEAD_TOP

MODEL_URL = (
    "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/"
    "models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
)
MODEL = Path(__file__).parent / ".cache" / "face_detection_yunet_2023mar.onnx"


def model_path():
    if not MODEL.exists():
        MODEL.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(MODEL_URL, MODEL)
    return str(MODEL)


def detect(img):
    """Return (eye midpoint, interocular distance, face-box center x)."""
    h, w = img.shape[:2]
    det = cv2.FaceDetectorYN.create(model_path(), "", (w, h), 0.6, 0.3, 5000)
    _, faces = det.detect(img)
    if faces is None:
        raise SystemExit("no face detected -- crop closer to the head and retry")
    f = max(faces, key=lambda f: f[-1])  # highest-confidence face
    right_eye, left_eye = f[4:6], f[6:8]
    eye_mid = np.array(
        [(right_eye[0] + left_eye[0]) / 2, (right_eye[1] + left_eye[1]) / 2], float
    )
    iod = float(np.hypot(left_eye[0] - right_eye[0], left_eye[1] - right_eye[1]))
    return eye_mid, iod, float(f[0] + f[2] / 2)


def main(src, dst):
    from rembg import new_session, remove

    raw = Image.open(src).convert("RGB")
    cut = remove(raw, session=new_session("u2net"))

    alpha = np.asarray(cut)[..., 3]
    crown = float(np.where((alpha > 128).any(axis=1))[0].min())

    eye_mid, iod, box_cx = detect(cv2.cvtColor(np.asarray(raw), cv2.COLOR_RGB2BGR))
    scale = (REF_IOD / iod + REF_BLOCK / (eye_mid[1] - crown)) / 2

    cut = cut.resize(
        (round(cut.width * scale), round(cut.height * scale)), Image.LANCZOS
    )
    canvas = Image.new("RGBA", (SIZE, SIZE), BG + (255,))
    canvas.alpha_composite(
        cut, (round(SIZE / 2 - box_cx * scale), round(REF_EYE_Y - eye_mid[1] * scale))
    )
    canvas.convert("RGB").save(dst, "PNG", optimize=True)
    print(f"wrote {dst} (scale {scale:.3f})")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
