"""Converte, em lote, PDFs textuais ou digitalizados em arquivos TXT."""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

LOGGER = logging.getLogger("ocr_batch")


class ConfigurationError(RuntimeError):
    """Erro de configuração ou dependência externa."""


@dataclass(frozen=True)
class Settings:
    input_dir: Path
    output_dir: Path
    dpi: int
    language: str
    min_text_chars: int
    overwrite: bool


@dataclass
class Summary:
    found: int = 0
    converted: int = 0
    skipped: int = 0
    failed: int = 0


def load_dependencies():
    """Importa dependências somente quando o processamento for iniciado."""
    try:
        import fitz
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise ConfigurationError(
            "Dependências Python ausentes. Execute: py -m pip install -r requirements.txt"
        ) from exc
    return fitz, pytesseract, Image


def validate_settings(settings: Settings, pytesseract) -> None:
    if settings.dpi < 72 or settings.dpi > 600:
        raise ConfigurationError("O DPI deve estar entre 72 e 600.")
    if settings.min_text_chars < 0:
        raise ConfigurationError("O mínimo de caracteres não pode ser negativo.")

    executable = shutil.which("tesseract")
    if not executable:
        candidates = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Tesseract-OCR" / "tesseract.exe",
            Path(os.environ.get("ProgramFiles", "")) / "Tesseract-OCR" / "tesseract.exe",
        ]
        executable = next((str(path) for path in candidates if path.is_file()), None)
    if executable:
        pytesseract.pytesseract.tesseract_cmd = executable

    try:
        version = pytesseract.get_tesseract_version()
    except Exception as exc:
        raise ConfigurationError(
            "Tesseract OCR não encontrado. Instale-o e adicione-o ao PATH do Windows."
        ) from exc

    try:
        languages = set(pytesseract.get_languages(config=""))
    except Exception as exc:
        raise ConfigurationError("Não foi possível consultar os idiomas do Tesseract.") from exc

    if settings.language not in languages:
        available = ", ".join(sorted(languages)) or "nenhum"
        raise ConfigurationError(
            f"Idioma '{settings.language}' não instalado no Tesseract. Disponíveis: {available}."
        )
    LOGGER.info("Tesseract %s; idioma: %s", version, settings.language)


def find_pdfs(folder: Path, output_dir: Path):
    output_resolved = output_dir.resolve()
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.suffix.lower() != ".pdf":
            continue
        try:
            path.resolve().relative_to(output_resolved)
        except ValueError:
            yield path


def output_path_for(pdf: Path, input_dir: Path, output_dir: Path) -> Path:
    relative = pdf.relative_to(input_dir).with_suffix(".txt")
    return output_dir / relative


def extract_page(page, dpi: int, language: str, min_text_chars: int, pytesseract, Image) -> str:
    direct_text = page.get_text("text").strip()
    if len(direct_text) >= min_text_chars:
        return direct_text

    pixmap = page.get_pixmap(dpi=dpi, alpha=False)
    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    try:
        return pytesseract.image_to_string(image, lang=language).strip()
    finally:
        image.close()


def extract_pdf(pdf: Path, settings: Settings, fitz, pytesseract, Image) -> str:
    page_texts: list[str] = []
    try:
        with fitz.open(pdf) as document:
            if document.needs_pass:
                raise ValueError("PDF protegido por senha")
            if document.page_count == 0:
                raise ValueError("PDF sem páginas")
            for page_number, page in enumerate(document, start=1):
                LOGGER.debug("%s: página %d/%d", pdf.name, page_number, document.page_count)
                page_texts.append(
                    extract_page(
                        page,
                        settings.dpi,
                        settings.language,
                        settings.min_text_chars,
                        pytesseract,
                        Image,
                    )
                )
    except Exception as exc:
        raise RuntimeError(f"não foi possível ler o PDF: {exc}") from exc
    return "\n\n".join(page_texts).strip()


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
        ) as temporary:
            temporary.write(text)
            if text and not text.endswith("\n"):
                temporary.write("\n")
            temporary_name = temporary.name
        Path(temporary_name).replace(path)
    finally:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)


def process_all(settings: Settings) -> Summary:
    fitz, pytesseract, Image = load_dependencies()
    validate_settings(settings, pytesseract)
    pdfs = list(find_pdfs(settings.input_dir, settings.output_dir))
    summary = Summary(found=len(pdfs))

    for index, pdf in enumerate(pdfs, start=1):
        destination = output_path_for(pdf, settings.input_dir, settings.output_dir)
        if destination.exists() and not settings.overwrite:
            LOGGER.info("[%d/%d] Ignorado (já existe): %s", index, len(pdfs), destination)
            summary.skipped += 1
            continue
        LOGGER.info("[%d/%d] Processando: %s", index, len(pdfs), pdf)
        try:
            text = extract_pdf(pdf, settings, fitz, pytesseract, Image)
            atomic_write(destination, text)
            LOGGER.info("Salvo: %s (%d caracteres)", destination, len(text))
            summary.converted += 1
        except Exception as exc:
            LOGGER.error("Falha em %s: %s", pdf, exc)
            summary.failed += 1
    return summary


def build_parser(script_dir: Path) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Converte PDFs textuais ou digitalizados em TXT.")
    parser.add_argument("input", nargs="?", type=Path, default=script_dir / "pdfs")
    parser.add_argument("--out", type=Path, default=script_dir / "textos")
    parser.add_argument("--dpi", type=int, default=300, help="DPI do OCR, entre 72 e 600")
    parser.add_argument("--lang", default="por", help="Idioma instalado no Tesseract")
    parser.add_argument(
        "--min-text-chars",
        type=int,
        default=20,
        help="Texto mínimo por página antes de aplicar OCR",
    )
    parser.add_argument("--overwrite", action="store_true", help="Sobrescreve TXT já existente")
    parser.add_argument("--verbose", action="store_true", help="Exibe detalhes por página")
    return parser


def main(argv: list[str] | None = None) -> int:
    script_dir = Path(__file__).resolve().parent
    args = build_parser(script_dir).parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    settings = Settings(
        input_dir=args.input.resolve(),
        output_dir=args.out.resolve(),
        dpi=args.dpi,
        language=args.lang,
        min_text_chars=args.min_text_chars,
        overwrite=args.overwrite,
    )
    settings.input_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)

    try:
        summary = process_all(settings)
    except ConfigurationError as exc:
        LOGGER.error("%s", exc)
        return 2

    if summary.found == 0:
        LOGGER.warning("Nenhum PDF encontrado em: %s", settings.input_dir)
    LOGGER.info(
        "Resumo: %d encontrado(s), %d convertido(s), %d ignorado(s), %d falha(s).",
        summary.found,
        summary.converted,
        summary.skipped,
        summary.failed,
    )
    return 1 if summary.failed else 0


if __name__ == "__main__":
    sys.exit(main())
