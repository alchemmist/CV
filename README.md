<h2><img src="./images/logo.svg" alt="Favicon Preview" width="75" align="center"> Resume (CV)</h2>

[![Github](https://img.shields.io/badge/alchemmist%2FCV-blue?logo=github&label=github&color=blue)](https://github.com/alchemmist/CV)
![Last commit](https://img.shields.io/github/last-commit/alchemmist/CV?style=flat) ![Stars](https://img.shields.io/github/stars/alchemmist/CV?style=flat)
![Forks](https://img.shields.io/github/forks/alchemmist/CV?style=flat)
![License](https://img.shields.io/github/license/alchemmist/CV?style=flat)
![Contributors](https://img.shields.io/github/contributors/alchemmist/CV?style=flat)
![Latexmk](https://img.shields.io/badge/4.86-default?label=latexmk)
[![Build](https://github.com/alchemmist/CV/actions/workflows/build.yaml/badge.svg?branch=main)](https://github.com/alchemmist/CV/actions/workflows/build.yaml)

This is my Curriculum Vita (CV) as a software engineer. I have two versions of CV ([english](/pdf/english.pdf) and [russian](/pdf/russian.pdf)) already rednered in [`pdf`](/pdf) directory. This repo have MIT license, so you can use it as a template for your CV or or whatever you want.

The [`resume.cls`](tex/resume.cls) class defines the layout. Resume content lives
in `tex/*.tex`; formatting and photo placement belong to the class.

### Heading, contacts and photo

Declare the photo in the preamble and put contact information in `contactinfo`:

```tex
\documentclass[margin,line]{resume}
\definecolor{sidebarcolor}{RGB}{0,49,83}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[english]{babel}
\usepackage{fontawesome}

\photo{../images/avatar.png}

\begin{document}
\resumeheading{Your Name --- Backend Developer}
\begin{resume}
  \begin{contactinfo}
    \section{\mysidestyle Personal\\Information}
    City, Country \\
    \href{mailto:you@example.com}{you@example.com}
  \end{contactinfo}

  \section{\mysidestyle Experience}
  Your experience.
\end{resume}
\end{document}
```

The photo's top aligns with the top of the contact block, below the heading
and horizontal rule. Its right edge aligns with the body's right margin.
The default width is 25.5 mm; the aspect ratio is preserved. To change the size,
use `\photo[35mm]{../images/avatar.png}`. Larger photos extend left and down
from the same corner without moving the text. Keep enough free space for the
chosen size; the class does not wrap text around the photo.

Paths are relative to the build directory (`tex/` here). PDF, PNG and JPEG are
supported. Omit `\photo` or use `\photo{}` for no photo. Calling it again replaces
the declaration. The photo is drawn only where `contactinfo` is used, so it does
not repeat on subsequent pages.

To migrate an existing document, replace the contact `minipage`, the photo's
`minipage`/`textblock`, and their trailing negative `\vspace` with `contactinfo`.
Replace the manually shifted heading with `\resumeheading{...}`. The template's
existing contact-to-body spacing is preserved; `\contactinfosep` controls that
spacing centrally. Its default preserves the body baseline after removing the
empty photo paragraph. For a more compact document, for example, declare
`\addtolength{\contactinfosep}{-1mm}` in the preamble.

### Yandex internship resume

[Short Russian resume focused on my Yandex internship](pdf/short-yandex.pdf) · [LaTeX source](tex/short-yandex.tex). Uses the short resume layout with a `#fc3e1c` accent stripe.

### Blog icon

Use `\faAlcehmmist` for the blog logo, sized to the current text and vertically
centered with lowercase text:

```tex
\faAlcehmmist\space
\href{https://alchemmist.xyz}{\texttt{alchemmist.xyz}}
```

### Sidebar logos

Declare a comma-separated list of image paths in the preamble, after
`\documentclass`, to stack logos in the colored sidebar:

```tex
\sidebarlogos{../images/yandex-mark.pdf, ../images/another-logo.png}
```

The first logo sits at the bottom; subsequent logos stack upward with a 3 mm
gap. Logos are centered within the visible stripe, start 6 mm above the page
edge, and fit within the stripe (2 mm horizontal padding) and a 14 mm height
while preserving their aspect ratios. The stack repeats on every page.
Omit the command or use `\sidebarlogos{}` for no logos; calling it again replaces
the list. Paths are relative to the LaTeX build directory (`tex/` here).
PDF, PNG, and JPEG work with the existing pdfLaTeX build.

The class adds no borders, shadows, backgrounds, or cropping. Decoration and
transparent padding already present in an image remain part of that image.
Use an asset with a transparent background for a bare logo. The included
`yandex-mark.pdf` contains only the white mark from the
[Wikimedia Yandex icon](https://commons.wikimedia.org/wiki/File:Yandex_icon.svg),
without its circular background; its vector source is `images/yandex-mark.svg`.

### Building

Build every `tex/*.tex` file into `pdf/` with:

```sh
make build
```

On macOS, install [TinyTeX](https://yihui.org/tinytex/) or MacTeX and make sure
`pdflatex` and `latexmk` are on `PATH`. For a minimal TinyTeX installation, add
the packages used by this template:

```sh
tlmgr install latexmk babel-english babel-russian hyphen-russian cyrillic lh cm-super fontawesome \
  tcolorbox listings tikzfill textpos enumitem wrapfig fancyhdr eso-pic
```

A user-local TinyTeX installation can live in `~/Library/TinyTeX`, with command
symlinks in `~/.local/bin`. The build runs natively on macOS; Docker is not
required. `babel-russian` and `hyphen-russian` are separate packages: the latter
provides Russian hyphenation patterns. `make build` fails if LaTeX reports
missing patterns.

### Layout checks

`make test` requires `latexmk`, the LaTeX packages used by `make build`, and
PyMuPDF (`python3 -m pip install pymupdf`). It compiles fixtures with portrait
and landscape images, different sizes and page geometry, replaced and omitted
photos, and a second page. It checks alignment, aspect ratios and unchanged
text positions. It also checks the right text margin in `pdf/short-yandex.pdf`;
run `make build` first to check the current sources.

To compare all resumes against PDFs built before a layout change, keep a copy
of that `pdf/` directory, run `make build`, then run:

```sh
make test BASELINE=/absolute/path/to/baseline-pdf
```

The baseline and current PDFs must be built with the same TeX distribution and
fonts. The comparison checks text coordinates, page breaks, and rendered pixels
at 144 dpi outside the old and new photo rectangles. Raster comparison allows
a difference of at most 2/255 per color channel for renderer rounding; text
positions are checked separately.

### Questions | Contribute

If you have questions about this repo or you want to contribute, [text me](https://t.me/alchemmist)!

### Demo

<img src="./images/demo.png" alt="Favicon Preview"  style="margin-bottom: 10px">

### License

Licensed under of The [MIT](./LICENSE) License.

### Thanks for review

- Anatoly Zinoviev
- Alexander Shakhov
- Natalia Kuznetsova
- Mikhail Doshevsky
- Yegor Bugayenko
- Nikita Sobolev
- Maxim Smirnov
- Grigory Petrov
- Pavel Sokolov
- Mikhail Flenov
- Julia Lukyanova
- Ruslan Masgutov
- Alexey Goloburdin
- Mark Melixetyan
- Kristina Lozbina
- Ksenia Vdovkina

If you find your name here and you **don't want** for put your name here, text me on email: [`anton.ingrish@gmail.com`](mailto:anton.ingrish@gmail.com). If you belive I make a typo in your name, sorry for that and report it in issue.
