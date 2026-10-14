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


if __name__ == "__main__":
    check_profiles()
