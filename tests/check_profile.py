import shutil
import subprocess
import tempfile
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]


def compile_document(root, name, source):
    (root / f"{name}.tex").write_text(source)
    result = subprocess.run(
        ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", f"{name}.tex"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "No hyphenation patterns were preloaded" not in (root / f"{name}.log").read_text()
    return fitz.open(root / f"{name}.pdf")


def check_profiles():
    with tempfile.TemporaryDirectory(prefix="resume-profile-") as directory:
        root = Path(directory)
        shutil.copy(ROOT / "tex" / "resume.cls", root)
        with compile_document(root, "hr", (ROOT / "examples" / "hr.tex").read_text()) as document:
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
        print("Profiles: Russian HR example, English profile, optional contacts and custom footer passed")



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
                positions.append(page.search_for("Final marker")[0].y0 - page.search_for("First paragraph")[0].y0)
                images = page.get_image_info()
                if width is None:
                    assert not images
                else:
                    assert len(images) == 1
                    assert page.search_for("First paragraph")[0].y0 > images[0]["bbox"][3]
                    assert abs(fitz.Rect(images[0]["bbox"]).width - width * 72 / 25.4) < 0.05
                stripe = next(d for d in page.get_drawings() if d["rect"].height > 700)
                expected = {"compact": (47, 79, 79), "normal": (108, 26, 54), "spacious": (51, 51, 51)}[density]
                assert all(abs(a - b / 255) < 0.001 for a, b in zip(stripe["fill"], expected))
        assert positions[0] < positions[1] < positions[2], positions
        print("Options: accent colors, photo presets and increasing density spacing passed")


if __name__ == "__main__":
    check_profiles()
    check_options()
