import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]


def compile_document(root, name, source, expected_error=None):
    (root / f"{name}.tex").write_text(source)
    result = subprocess.run(
        [
            "latexmk",
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"{name}.tex",
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if expected_error:
        assert result.returncode != 0, f"{name}: invalid settings were accepted"
        assert expected_error in result.stdout + result.stderr
        return None
    assert result.returncode == 0, result.stdout + result.stderr
    assert (
        "No hyphenation patterns were preloaded"
        not in (root / f"{name}.log").read_text()
    )
    if output := os.environ.get("CV_TEST_ARTIFACTS"):
        destination = Path(output)
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copy(root / f"{name}.pdf", destination / f"{name}.pdf")
    return fitz.open(root / f"{name}.pdf")


def check_profiles():
    with tempfile.TemporaryDirectory(prefix="resume-profile-") as directory:
        root = Path(directory)
        shutil.copy(ROOT / "tex" / "resume.cls", root)
        with compile_document(
            root, "hr", (ROOT / "example.tex").read_text()
        ) as document:
            text = "".join(page.get_text() for page in document)
            assert "Анна Петрова" in text
            assert "anna@example.com" in text
            assert "alchemmist" not in text
            assert not document[0].get_image_info()
        source = r"""\documentclass[margin,line]{resume}
\resumesetup{language=english,name={Alex Example},contacts={
\contact{}{https://unused.example}
\contact{Portfolio}{https://example.com}
},footer-left={Custom footer}}
\begin{document}\begin{resume}
\section{Experience}Example work.
\end{resume}\end{document}
"""
        with compile_document(root, "english", source) as document:
            text = document[0].get_text()
            assert "Alex Example" in text and "Custom footer" in text
            assert "alchemmist" not in text
            urls = [link.get("uri") for link in document[0].get_links()]
            assert "https://example.com" in urls
            assert "https://unused.example" not in urls
        print(
            "Profiles: Russian HR example, English profile, optional contacts and custom footer passed"
        )


def check_options():
    with tempfile.TemporaryDirectory(prefix="resume-options-") as directory:
        root = Path(directory)
        shutil.copy(ROOT / "tex" / "resume.cls", root)
        image = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 120, 160), False)
        image.set_rect(image.irect, (100, 150, 200))
        image.save(root / "portrait.png")
        positions = []
        for density, color, size, width in [
            ("compact", "accent=forest", "small", 20),
            ("normal", "accent-html=6C1A36", "standard", 25.5),
            ("spacious", "accent=charcoal", "none", None),
        ]:
            source = r"""\documentclass[margin,line]{resume}
\resumesetup{name={Alex Example},location={London},
contacts={\contact{first@example.com}{}\contact{Second}{}\contact{Third}{}\contact{Fourth}{}},
OPTIONS,photo={portrait.png}}
\begin{document}\begin{resume}
\section{Experience}First paragraph.

Second paragraph.
\begin{itemize}\item First achievement.\item Second achievement.\end{itemize}
\section{Education}Final marker.
\end{resume}\end{document}
""".replace("OPTIONS", f"density={density},{color},photo-size={size}")
            with compile_document(root, density, source) as document:
                assert len(document) == 1
                page = document[0]
                positions.append(
                    page.search_for("Final marker")[0].y0
                    - page.search_for("First paragraph")[0].y0
                )
                images = page.get_image_info()
                if width is None:
                    assert not images
                else:
                    assert len(images) == 1
                    assert (
                        page.search_for("First paragraph")[0].y0 > images[0]["bbox"][3]
                    )
                    assert (
                        abs(fitz.Rect(images[0]["bbox"]).width - width * 72 / 25.4)
                        < 0.05
                    )
                stripe = next(d for d in page.get_drawings() if d["rect"].height > 700)
                expected = {
                    "compact": (47, 79, 79),
                    "normal": (108, 26, 54),
                    "spacious": (51, 51, 51),
                }[density]
                assert all(
                    abs(a - b / 255) < 0.001 for a, b in zip(stripe["fill"], expected)
                )
        assert positions[0] < positions[1] < positions[2], positions
        print(
            "Options: accent colors, photo presets and increasing density spacing passed"
        )


def check_edge_cases():
    from check_layout import check_right_margin, check_text

    with tempfile.TemporaryDirectory(prefix="resume-edge-") as directory:
        root = Path(directory)
        shutil.copy(ROOT / "tex" / "resume.cls", root)
        image = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 120, 160), False)
        image.set_rect(image.irect, (100, 150, 200))
        image.save(root / "portrait.png")
        for name, settings, error in [
            ("invalid-color", "accent-html=invalid", "Invalid accent color"),
            ("invalid-width", "photo-width=0mm", "Photo width must be positive"),
            (
                "oversized-photo",
                "photo={portrait.png},photo-width=130mm",
                "Photo leaves too little space",
            ),
        ]:
            source = (
                r"\documentclass[margin,line]{resume}\resumesetup{"
                + settings
                + r"}\begin{document}\begin{resume}Body.\end{resume}\end{document}"
            )
            compile_document(root, name, source, expected_error=error)
        long_url = "https://example.com/" + "verylongunbrokensegment" * 8
        source = r"""\documentclass[margin,line]{resume}
\resumesetup{language=english,
name={Alexandra Catherine Elizabeth Montgomery Robertson},
title={Senior international people operations and organizational development partner},
location={London, United Kingdom},photo={portrait.png},photo-width=50mm,
contacts={\contact[\faEnvelope]{LONGURL}{LONGURL}\contact{Portfolio}{https://example.com}}}
\begin{document}\begin{resume}
\section{About}Body starts here. Working across international teams.
\section{Links}\url{LONGURL}
\section{Experience}
\begin{resumeentry}{Senior international people operations and organizational development partner}{Example company with a long name}{September 2020 -- October 2026}
First achievement in this role.
\end{resumeentry}
\end{resume}\end{document}
""".replace("LONGURL", long_url)
        with compile_document(root, "long-fields", source) as document:
            check_right_margin(root / "long-fields.pdf")
            page = document[0]
            photo = fitz.Rect(page.get_image_info()[0]["bbox"])
            assert page.search_for("Body starts here")[0].y0 > photo.y1
            assert not any(
                fitz.Rect(span["bbox"]).intersects(photo)
                for block in page.get_text("dict")["blocks"]
                for line in block.get("lines", [])
                for span in line["spans"]
            )
            assert len(page.search_for("Alexandra")) == 1
            assert any(link.get("uri") == long_url for link in page.get_links())
        base = r"""\documentclass[margin,line]{resume}
\resumesetup{language=english,name={Alex Example},SETTINGS}
\begin{document}\begin{resume}
\section{About}First body paragraph.
\end{resume}\end{document}
"""
        with compile_document(root, "empty", base.replace("SETTINGS", "")) as empty:
            reference = empty.tobytes()
        with (
            compile_document(
                root,
                "blank-contacts",
                base.replace(
                    "SETTINGS", r"contacts={\contact{}{}\contact[\faPhone]{}{tel:123}}"
                ),
            ) as blank,
            fitz.open(stream=reference, filetype="pdf") as empty,
        ):
            check_text(empty, blank)
        with compile_document(
            root, "photo-only", base.replace("SETTINGS", "photo={portrait.png}")
        ) as document:
            page = document[0]
            assert len(page.get_image_info()) == 1
            assert "Personal" not in page.get_text()
            assert (
                page.search_for("First body")[0].y0
                > page.get_image_info()[0]["bbox"][3]
            )
        for kind, content, heading, body in [
            (
                "section",
                r"\section{Boundary}Following marker.",
                "Boundary",
                "Following marker",
            ),
            (
                "entry",
                r"\begin{resumeentry}{Boundary role}{Example}{2020--2026}Entry marker.\par "
                + (r"More details about this role.\par " * 70)
                + r"\end{resumeentry}",
                "Boundary role",
                "Entry marker",
            ),
        ]:
            source = r"""\documentclass[margin,line]{resume}
\resumesetup{language=english,name={Alex Example}}
\begin{document}\begin{resume}
Initial paragraph.
\newpage
\null\vspace*{\dimexpr\textheight-3\baselineskip\relax}\par
CONTENT
\end{resume}\end{document}
""".replace("CONTENT", content)
            with compile_document(root, kind + "-boundary", source) as document:
                heading_page = next(
                    i for i, page in enumerate(document) if page.search_for(heading)
                )
                body_page = next(
                    i for i, page in enumerate(document) if page.search_for(body)
                )
                assert heading_page == body_page, f"{kind}: orphaned heading"
                assert heading_page >= 2
                if kind == "entry":
                    assert len(document) > body_page + 1, "Entry body should span pages"
        for name in ("long-fields", "photo-only", "section-boundary", "entry-boundary"):
            assert "Overfull" not in (root / f"{name}.log").read_text(), (
                f"{name}: overflow"
            )
        print(
            "Edge cases: long headings and URLs, photo clearance, empty fields and page boundaries passed"
        )


if __name__ == "__main__":
    check_profiles()
    check_options()
    check_edge_cases()
