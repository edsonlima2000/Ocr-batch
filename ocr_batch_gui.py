"""Interface gráfica do OCR Batch usando Tkinter."""

from __future__ import annotations

import logging
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import ocr_batch


class QueueHandler(logging.Handler):
    def __init__(self, messages: queue.Queue):
        super().__init__()
        self.messages = messages

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.put(("log", self.format(record)))


class OcrBatchApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("OCR Batch — PDF para texto")
        self.geometry("780x570")
        self.minsize(680, 480)

        base = Path(__file__).resolve().parent
        self.input_var = tk.StringVar(value=str(base / "pdfs"))
        self.output_var = tk.StringVar(value=str(base / "textos"))
        self.language_var = tk.StringVar(value="por")
        self.dpi_var = tk.StringVar(value="300")
        self.overwrite_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Pronto para processar.")
        self.messages: queue.Queue = queue.Queue()
        self.worker: threading.Thread | None = None

        self._build_ui()
        self.after(100, self._read_messages)

    def _build_ui(self) -> None:
        container = ttk.Frame(self, padding=18)
        container.pack(fill="both", expand=True)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(7, weight=1)

        ttk.Label(container, text="OCR Batch", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 14)
        )
        self._folder_row(container, 1, "Pasta dos PDFs", self.input_var, self._choose_input)
        self._folder_row(container, 2, "Pasta dos textos", self.output_var, self._choose_output)

        options = ttk.Frame(container)
        options.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(12, 6))
        ttk.Label(options, text="Idioma:").pack(side="left")
        ttk.Entry(options, textvariable=self.language_var, width=8).pack(side="left", padx=(6, 20))
        ttk.Label(options, text="DPI:").pack(side="left")
        ttk.Combobox(
            options, textvariable=self.dpi_var, values=("150", "200", "300", "400", "600"),
            state="readonly", width=7,
        ).pack(side="left", padx=(6, 20))
        ttk.Checkbutton(
            options, text="Sobrescrever textos existentes", variable=self.overwrite_var
        ).pack(side="left")

        actions = ttk.Frame(container)
        actions.grid(row=4, column=0, columnspan=3, sticky="ew", pady=10)
        self.start_button = ttk.Button(actions, text="Converter PDFs", command=self._start)
        self.start_button.pack(side="left")
        ttk.Button(actions, text="Abrir pasta dos textos", command=self._open_output).pack(
            side="left", padx=8
        )
        ttk.Button(actions, text="Limpar mensagens", command=self._clear_log).pack(side="left")

        self.progress = ttk.Progressbar(container, mode="indeterminate")
        self.progress.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(2, 8))
        ttk.Label(container, textvariable=self.status_var).grid(
            row=6, column=0, columnspan=3, sticky="w", pady=(0, 6)
        )

        log_frame = ttk.Frame(container)
        log_frame.grid(row=7, column=0, columnspan=3, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = tk.Text(log_frame, wrap="word", state="disabled", font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def _folder_row(self, parent, row: int, label: str, variable, command) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(parent, textvariable=variable).grid(
            row=row, column=1, sticky="ew", padx=10, pady=5
        )
        ttk.Button(parent, text="Escolher…", command=command).grid(row=row, column=2, pady=5)

    def _choose_input(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.input_var.get())
        if selected:
            self.input_var.set(selected)

    def _choose_output(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.output_var.get())
        if selected:
            self.output_var.set(selected)

    def _open_output(self) -> None:
        path = Path(self.output_var.get()).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        try:
            import os
            os.startfile(path)  # type: ignore[attr-defined]
        except OSError as exc:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{exc}")

    def _clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _start(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        try:
            dpi = int(self.dpi_var.get())
            input_dir = Path(self.input_var.get()).expanduser().resolve()
            output_dir = Path(self.output_var.get()).expanduser().resolve()
            if input_dir == output_dir:
                raise ValueError("As pastas de entrada e saída devem ser diferentes.")
            settings = ocr_batch.Settings(
                input_dir=input_dir,
                output_dir=output_dir,
                dpi=dpi,
                language=self.language_var.get().strip() or "por",
                min_text_chars=20,
                overwrite=self.overwrite_var.get(),
            )
        except (OSError, ValueError) as exc:
            messagebox.showerror("Configuração inválida", str(exc))
            return

        settings.input_dir.mkdir(parents=True, exist_ok=True)
        settings.output_dir.mkdir(parents=True, exist_ok=True)
        self.start_button.configure(state="disabled")
        self.progress.start(12)
        self.status_var.set("Processando…")
        self._append_log("Iniciando conversão…")
        self.worker = threading.Thread(target=self._run, args=(settings,), daemon=True)
        self.worker.start()

    def _run(self, settings: ocr_batch.Settings) -> None:
        handler = QueueHandler(self.messages)
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        ocr_batch.LOGGER.addHandler(handler)
        ocr_batch.LOGGER.setLevel(logging.INFO)
        try:
            summary = ocr_batch.process_all(settings)
            self.messages.put(("done", summary))
        except ocr_batch.ConfigurationError as exc:
            self.messages.put(("error", str(exc)))
        except Exception as exc:
            self.messages.put(("error", f"Erro inesperado: {exc}"))
        finally:
            ocr_batch.LOGGER.removeHandler(handler)

    def _read_messages(self) -> None:
        try:
            while True:
                kind, payload = self.messages.get_nowait()
                if kind == "log":
                    self._append_log(payload)
                elif kind == "done":
                    self._finish(payload)
                elif kind == "error":
                    self._fail(payload)
        except queue.Empty:
            pass
        self.after(100, self._read_messages)

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _finish(self, summary: ocr_batch.Summary) -> None:
        self.progress.stop()
        self.start_button.configure(state="normal")
        text = (
            f"Concluído: {summary.converted} convertido(s), "
            f"{summary.skipped} ignorado(s), {summary.failed} falha(s)."
        )
        self.status_var.set(text)
        self._append_log(text)
        if summary.found == 0:
            messagebox.showinfo("Nenhum PDF", "Coloque arquivos PDF na pasta de entrada.")
        elif summary.failed:
            messagebox.showwarning("Conversão concluída", text)
        else:
            messagebox.showinfo("Conversão concluída", text)

    def _fail(self, message: str) -> None:
        self.progress.stop()
        self.start_button.configure(state="normal")
        self.status_var.set("Não foi possível iniciar a conversão.")
        self._append_log("ERRO: " + message)
        messagebox.showerror("Erro", message)


if __name__ == "__main__":
    OcrBatchApp().mainloop()
