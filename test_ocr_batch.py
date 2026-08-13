import tempfile
import unittest
from pathlib import Path

import ocr_batch


class OcrBatchTests(unittest.TestCase):
    def test_default_folders_are_next_to_script(self):
        base = Path("C:/app")
        args = ocr_batch.build_parser(base).parse_args([])
        self.assertEqual(args.input, base / "pdfs")
        self.assertEqual(args.out, base / "textos")

    def test_find_pdfs_is_case_insensitive_and_recursive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sub").mkdir()
            (root / "sub" / "a.PDF").touch()
            (root / "b.pdf").touch()
            (root / "ignore.txt").touch()
            found = list(ocr_batch.find_pdfs(root, root / "textos"))
            self.assertEqual({path.name for path in found}, {"a.PDF", "b.pdf"})

    def test_output_preserves_relative_subfolders(self):
        source = Path("C:/entrada/setor/documento.pdf")
        result = ocr_batch.output_path_for(source, Path("C:/entrada"), Path("C:/saida"))
        self.assertEqual(result, Path("C:/saida/setor/documento.txt"))

    def test_atomic_write_replaces_complete_file(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "sub" / "result.txt"
            ocr_batch.atomic_write(destination, "conteúdo")
            self.assertEqual(destination.read_text(encoding="utf-8"), "conteúdo\n")


if __name__ == "__main__":
    unittest.main()
