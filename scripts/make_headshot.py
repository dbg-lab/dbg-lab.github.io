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


def local_background(rgb, bg, fallback):
    """Per-pixel estimate of the backdrop, for scenes with no single colour.

    Normalized convolution over the known-background pixels: a box average of
    the backdrop that simply skips the subject. Run coarse to fine so the
    smallest window with enough background behind it wins, which keeps the
    estimate local where the backdrop changes fast (a brick edge against sky)
    and lets it widen where the subject blocks most of the window.
    """
    est = np.broadcast_to(fallback, rgb.shape).astype(np.float32).copy()
    w = bg.astype(np.float32)
    for r in (257, 129, 65, 33):
        num = cv2.blur(rgb * w[..., None], (r, r), borderType=cv2.BORDER_REPLICATE)
        den = cv2.blur(w, (r, r), borderType=cv2.BORDER_REPLICATE)
        ok = den > 0.05  # enough backdrop in the window to average
        est[ok] = (num / np.maximum(den, 1e-6)[..., None])[ok]
    return est


def decontaminate(cut, raw):
    """Strip the old background's colour out of semi-transparent edge pixels.

    A soft alpha edge (flyaway hair) is a blend of subject and original
    background: C = a*F + (1-a)*B. Composited onto the blue, the leftover B
    shows up as a pale halo. Solving for F removes it.

    A uniform backdrop gives one B for the whole image. A busy one (steps,
    brick, foliage) has no single B, so B is estimated per pixel from the
    backdrop immediately around each strand -- outdoor phone photos are the
    common case and their halo is the most visible.
    """
    arr = np.asarray(cut).astype(np.float32)
    a = arr[..., 3:4] / 255.0
    rgb = np.asarray(raw).astype(np.float32)

    bg = arr[..., 3] < 10
    bg_px = rgb[bg]
    if len(bg_px) < 500:
        return cut  # nothing identifiable as background to undo
    median = np.median(bg_px, axis=0)
    uniform = bg_px.std(axis=0).mean() <= 25
    B = median if uniform else local_background(rgb, bg, median)

    edge = ((a > 0.04) & (a < 0.98))[..., 0]
    fixed = rgb.copy()
    B_edge = B if uniform else B[edge]
    fixed[edge] = np.clip(
        (rgb[edge] - (1 - a[edge]) * B_edge) / np.maximum(a[edge], 0.04), 0, 255
    )
    return Image.fromarray(
        np.dstack([fixed.astype(np.uint8), arr[..., 3].astype(np.uint8)]), "RGBA"
    )


def main(src, dst):
    from rembg import new_session, remove

    raw = Image.open(src).convert("RGB")
    cut = decontaminate(remove(raw, session=new_session("u2net")), raw)

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
