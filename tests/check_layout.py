import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
TEXT_TOLERANCE = 0.02
PHOTO_TOLERANCE = 0.05
RASTER_TOLERANCE = 2
RIGHT_MARGIN_TOLERANCE = 1


def characters(page):
    return [
        (char["c"], char["origin"])
        for block in page.get_text("rawdict")["blocks"]
        if block["type"] == 0
        for line in block["lines"]
        for span in line["spans"]
        for char in span["chars"]
    ]


def check_text(before, after):
    assert len(before) == len(after), "Page count changed"
    for old_page, new_page in zip(before, after):
        assert old_page.rect == new_page.rect, "Page size changed"
        old_chars, new_chars = characters(old_page), characters(new_page)
        assert len(old_chars) == len(new_chars), "Character count changed"
        for old, new in zip(old_chars, new_chars):
            assert old[0] == new[0], f"Text changed: {old[0]!r} -> {new[0]!r}"
            assert max(abs(a - b) for a, b in zip(old[1], new[1])) <= TEXT_TOLERANCE, (
                f"Character moved: {old!r} -> {new!r}"
            )


def check_regression(baseline):
    avatar = fitz.Pixmap(str(ROOT / "images" / "avatar.png"))
    for source in sorted((ROOT / "tex").glob("*.tex")):
        name = source.with_suffix(".pdf").name
        with (
            fitz.open(baseline / name) as before,
            fitz.open(ROOT / "pdf" / name) as after,
        ):
            check_text(before, after)
            changed = 0
            for old_page, new_page in zip(before, after):
                old_pix = old_page.get_pixmap(dpi=144)
                new_pix = new_page.get_pixmap(dpi=144)
                for info in old_page.get_image_info() + new_page.get_image_info():
                    if (info["width"], info["height"]) != (avatar.width, avatar.height):
                        continue
                    rect = fitz.Rect(info["bbox"]) * fitz.Matrix(2, 2)
                    mask = fitz.Rect(rect.x0 - 2, rect.y0 - 2, rect.x1 + 2, rect.y1 + 2)
                    old_pix.set_rect(mask.irect, (255, 255, 255))
                    new_pix.set_rect(mask.irect, (255, 255, 255))
                changed += sum(
                    abs(a - b) > RASTER_TOLERANCE
                    for a, b in zip(old_pix.samples, new_pix.samples)
                )
            assert changed == 0, (
                f"{name}: {changed} raster channels changed outside photos"
            )
            print(
                f"{name}: text and page breaks unchanged; "
                f"pixels outside photos match within {RASTER_TOLERANCE}/255"
            )


def check_right_margin(path):
    with fitz.open(path) as document:
        right = next(
            drawing["rect"].x1
            for drawing in document[0].get_drawings()
            if drawing["type"] == "s"
            and drawing["rect"].width > 300
            and drawing["rect"].height < 1
        )
        for index, page in enumerate(document, 1):
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        assert span["bbox"][2] <= right + RIGHT_MARGIN_TOLERANCE, (
                            f"{path.name}, page {index}: text exceeds the right margin "
                            f"by {span['bbox'][2] - right:.2f} pt: {span['text']!r}"
                        )
    print(f"{path.name}: text stays within the right margin")


def check_photos():
    with tempfile.TemporaryDirectory(prefix="resume-layout-") as directory:
        root = Path(directory)
        shutil.copy(ROOT / "tex" / "resume.cls", root)
        for name, width, height in [("portrait", 120, 160), ("landscape", 160, 80)]:
            image = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, width, height), False)
            image.set_rect(image.irect, (100, 150, 200))
            image.save(root / f"{name}.png")
        for paper, geometry in [
            ("letterpaper", ""),
            (
                "a4paper",
                (
                    r"\setlength{\textwidth}{120mm}\setlength{\hoffset}{15mm}"
                    r"\setlength{\topmargin}{-5mm}"
                ),
            ),
        ]:
            reference = None
            corner = None
            for name, declaration, width in [
                ("none", "", None),
                ("default", r"\photo{portrait.png}", 25.5),
                ("large", r"\photo[40mm]{portrait.png}", 40),
                ("wide", r"\photo[120mm]{landscape.png}", 120),
                ("replacement", r"\photo{missing.png}\photo[30mm]{landscape.png}", 30),
                ("empty", r"\photo{missing.png}\photo{}", None),
            ]:
                stem = f"{paper}-{name}"
                source = (
                    "\\documentclass[margin,line,"
                    + paper
                    + "]{resume}\n"
                    + r"\definecolor{sidebarcolor}{RGB}{0,49,83}"
                    + "\n"
                    + r"\usepackage{fontawesome}"
                    + "\n"
                    + geometry
                    + "\n"
                    + declaration
                    + "\n"
                    + r"\begin{document}\resumeheading{Layout check}\begin{resume}"
                    + "\n"
                    + r"\begin{contactinfo}\rule{1pt}{10pt}Contact information\\"
                    + r"City\\Email\\Phone\end{contactinfo}"
                    + "\n"
                    + r"\section{Body}Body text stays in place."
                    + "\n"
                    + r"\newpage\section{Second page}No repeated photo."
                    + "\n"
                    + r"\end{resume}\end{document}"
                )
                (root / f"{stem}.tex").write_text(source)
                result = subprocess.run(
                    [
                        "latexmk",
                        "-pdf",
                        "-interaction=nonstopmode",
                        "-halt-on-error",
                        f"{stem}.tex",
                    ],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                assert result.returncode == 0, result.stdout + result.stderr
                with fitz.open(root / f"{stem}.pdf") as document:
                    assert len(document) == 2
                    if reference is None:
                        reference = document.tobytes()
                    with fitz.open(stream=reference, filetype="pdf") as before:
                        check_text(before, document)
                    assert not document[1].get_image_info(), f"{stem}: photo repeated"
                    images = document[0].get_image_info()
                    if width is None:
                        assert not images, f"{stem}: unexpected photo"
                        print(f"{stem}: passed")
                        continue
                    assert len(images) == 1
                    photo = fitz.Rect(images[0]["bbox"])
                    drawings = document[0].get_drawings()
                    marker = next(
                        d["rect"]
                        for d in drawings
                        if d["rect"].width < 1.1 and 9.9 < d["rect"].height < 10.1
                    )
                    rule = next(
                        d["rect"]
                        for d in drawings
                        if d["type"] == "s" and d["rect"].width > 100
                    )
                    assert abs(photo.y0 - marker.y0) < PHOTO_TOLERANCE, (
                        f"{stem}: top is not aligned"
                    )
                    assert abs(photo.x1 - rule.x1) < PHOTO_TOLERANCE, (
                        f"{stem}: right edge is not aligned: {photo.x1} vs {rule.x1}"
                    )
                    assert abs(photo.width - width * 72 / 25.4) < PHOTO_TOLERANCE
                    current_corner = (photo.x1, photo.y0)
                    if corner is None:
                        corner = current_corner
                    assert (
                        max(abs(a - b) for a, b in zip(corner, current_corner))
                        < PHOTO_TOLERANCE
                    )
                    ratio = 160 / 80 if name in ("wide", "replacement") else 120 / 160
                    assert abs(photo.width / photo.height - ratio) < 0.001
                print(f"{stem}: passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--pdf", type=Path)
    args = parser.parse_args()
    if args.pdf:
        check_right_margin(args.pdf)
        raise SystemExit(0)
    check_right_margin(ROOT / "pdf" / "short-yandex.pdf")
    check_photos()
    if args.baseline:
        check_regression(args.baseline)
