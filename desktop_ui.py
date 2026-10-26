"""Minimal offline-first Tk desktop UI for Code Checker Day 3.

No Tk root/window is initialized on import; headless tests use desktop_core.
This is an unverified developer GUI, not a customer-ready signed Windows EXE.
"""
from __future__ import annotations

import os
import queue
import sys
import threading
from datetime import datetime
from pathlib import Path

from desktop_core import ScanRequest, ScanResult, inspect_input, run_scan


def launch() -> int:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, scrolledtext, ttk
    except ImportError:
        print("GUI unavailable: tkinter was not installed.", file=sys.stderr)
        return 2

    class CodeCheckerWindow:
        def __init__(self, root: tk.Tk) -> None:
            self.root = root
            self.root.title("코드체커 — 오프라인 위험 진단 (개발용 MVP)")
            self.root.minsize(780, 680)
            self.root.geometry("930x790")
            self.root.protocol("WM_DELETE_WINDOW", self._on_close)

            self.kind = "path"
            self.source_var = tk.StringVar()
            self.language_var = tk.StringVar(value="자동")
            self.output_var = tk.StringVar(value=str(Path.home() / "CodeCheckerReports"))
            self.state_var = tk.StringVar(value="먼저 파일·폴더 또는 붙여넣기를 선택하세요.")
            self.queue: queue.Queue[tuple[str, ScanRequest, object]] = queue.Queue()
            self.busy = False
            self.preview_request: ScanRequest | None = None
            self.last_result: ScanResult | None = None
            self._build_widgets(ttk, tk, scrolledtext)
            self.root.after(100, self._poll)

        def _build_widgets(self, ttk, tk, scrolledtext) -> None:
            container = ttk.Frame(self.root, padding=18)
            container.pack(fill="both", expand=True)
            ttk.Label(
                container, text="오프라인 코드체커", font=("Malgun Gothic", 18, "bold")
            ).pack(anchor="w")
            ttk.Label(
                container, text="Python AST + 제한적 정적 규칙 · 고객 코드 실행/전송 없음 · AI 키 불필요"
            ).pack(anchor="w", pady=(2, 14))

            choose = ttk.LabelFrame(container, text="1. 입력 선택", padding=12)
            choose.pack(fill="x")
            bar = ttk.Frame(choose)
            bar.pack(fill="x")
            self.file_button = ttk.Button(bar, text="파일 / TXT / ZIP", command=self._choose_file)
            self.file_button.pack(side="left", padx=(0, 8))
            self.folder_button = ttk.Button(bar, text="프로젝트 폴더", command=self._choose_folder)
            self.folder_button.pack(side="left", padx=(0, 8))
            self.paste_button = ttk.Button(bar, text="코드 붙여넣기", command=self._select_paste)
            self.paste_button.pack(side="left", padx=(0, 8))
            self.clear_button = ttk.Button(bar, text="붙여넣기 지우기", command=self._clear_paste)
            self.clear_button.pack(side="left")

            self.source_entry = ttk.Entry(choose, textvariable=self.source_var, state="readonly")
            self.source_entry.pack(fill="x", pady=(10, 4))
            ttk.Label(
                choose, text="TXT / 붙여넣기는 언어를 선택하세요. 다중 파일 구분자 TXT는 반드시 자동 선택."
            ).pack(anchor="w", pady=(3, 4))
            self.language_select = ttk.Combobox(
                choose, textvariable=self.language_var, state="readonly", width=22,
                values=("자동", "Python", "JavaScript", "TypeScript"),
            )
            self.language_select.pack(anchor="w", pady=(0, 8))
            self.language_select.bind("<<ComboboxSelected>>", lambda _e: self._clear_preview())
            ttk.Label(choose, text="붙여넣기 영역 (파일 선택 중에는 무시됨)").pack(anchor="w")
            self.paste_text = scrolledtext.ScrolledText(
                choose, height=7, wrap="none", font=("Consolas", 10)
            )
            self.paste_text.pack(fill="x", pady=(4, 4))
            self.paste_text.bind("<<Modified>>", self._paste_modified)

            target = ttk.LabelFrame(container, text="2. 보고서 저장 위치", padding=10)
            target.pack(fill="x", pady=(12, 0))
            pathbar = ttk.Frame(target)
            pathbar.pack(fill="x")
            self.output_entry = ttk.Entry(pathbar, textvariable=self.output_var)
            self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
            self.output_button = ttk.Button(pathbar, text="위치 선택", command=self._choose_output)
            self.output_button.pack(side="left")

            actions = ttk.Frame(container)
            actions.pack(fill="x", pady=(12, 6))
            self.preview_button = ttk.Button(actions, text="① 입력 미리보기", command=self._preview)
            self.preview_button.pack(side="left", padx=(0, 10))
            self.scan_button = ttk.Button(actions, text="② 로컬 검사 및 보고서 생성", command=self._scan, state="disabled")
            self.scan_button.pack(side="left", padx=(0, 10))
            self.open_button = ttk.Button(actions, text="HTML 결과 열기", command=self._open, state="disabled")
            self.open_button.pack(side="left")

            ttk.Label(container, textvariable=self.state_var).pack(anchor="w", pady=(6, 5))
            self.result_text = scrolledtext.ScrolledText(
                container, height=13, state="disabled", wrap="word", font=("Malgun Gothic", 10)
            )
            self.result_text.pack(fill="both", expand=True)
            self._show(
                "미리보기를 먼저 실행한 다음 검사를 시작할 수 있습니다.\n"
                "결과는 선택한 로컬 폴더에 HTML + Markdown으로 저장됩니다.\n"
                "complete는 적용한 검사 절차 완료이며 보안성·무결점 판정이 아닙니다.\n"
                "지원 한도: 최대 200파일, 파일당 1MiB, 전체 8MiB (검증된 보장 최대치는 아님)."
            )

        def _show(self, text: str) -> None:
            self.result_text.configure(state="normal")
            self.result_text.delete("1.0", "end")
            self.result_text.insert("1.0", text)
            self.result_text.configure(state="disabled")

        def _clear_preview(self) -> None:
            self.preview_request = None
            if not self.busy:
                self.scan_button.configure(state="disabled")

        def _paste_modified(self, _event=None) -> None:
            if self.paste_text.edit_modified():
                self._clear_preview()
                self.paste_text.edit_modified(False)

        def _choose_file(self) -> None:
            source = filedialog.askopenfilename(
                title="오프라인 분석할 파일 선택",
                filetypes=[("ZIP/TXT/소스", "*.zip *.txt *.py *.pyi *.js *.ts"),
                           ("모든 파일", "*.*")],
            )
            if source:
                self.kind = "path"
                self.source_var.set(source)
                if Path(source).suffix.lower() != ".txt":
                    self.language_var.set("자동")
                self._clear_preview()
                self.state_var.set("파일 선택 완료. 미리보기를 실행하세요.")

        def _choose_folder(self) -> None:
            source = filedialog.askdirectory(title="프로젝트 폴더 선택")
            if source:
                self.kind = "path"
                self.source_var.set(source)
                self.language_var.set("자동")
                self._clear_preview()
                self.state_var.set("폴더 선택 완료. 미리보기를 실행하세요.")

        def _select_paste(self) -> None:
            self.kind = "paste"
            self.source_var.set("[메모리에서 코드 붙여넣기]")
            if self.language_var.get() == "자동":
                self.language_var.set("Python")
            self._clear_preview()
            self.paste_text.focus_set()
            self.state_var.set("붙여넣기 모드입니다. 코드를 입력한 뒤 미리보기를 실행하세요.")

        def _clear_paste(self) -> None:
            self.paste_text.delete("1.0", "end")
            self._clear_preview()

        def _choose_output(self) -> None:
            folder = filedialog.askdirectory(title="로컬 보고서 출력 폴더")
            if folder:
                self.output_var.set(folder)
                self._clear_preview()
                self.state_var.set("저장 폴더를 변경했습니다. 다시 미리보기를 실행하세요.")

        def _request(self) -> ScanRequest:
            language = {
                "자동": None, "Python": "python",
                "JavaScript": "javascript", "TypeScript": "typescript",
            }[self.language_var.get()]
            if self.kind == "paste":
                return ScanRequest("paste", text=self.paste_text.get("1.0", "end-1c"), language=language)
            return ScanRequest("path", source=self.source_var.get(), language=language)

        def _busy(self, enabled: bool) -> None:
            self.busy = enabled
            state = "disabled" if enabled else "normal"
            for button in (
                self.file_button, self.folder_button, self.paste_button,
                self.clear_button, self.preview_button, self.output_button,
            ):
                button.configure(state=state)
            self.language_select.configure(state="disabled" if enabled else "readonly")
            self.paste_text.configure(state=state)
            self.output_entry.configure(state=state)
            self.open_button.configure(state="disabled" if enabled or self.last_result is None else "normal")
            self.scan_button.configure(state="disabled" if enabled or self.preview_request is None else "normal")

        def _dispatch(self, operation: str, request: ScanRequest, output_dir: str = "", name: str = "") -> None:
            if self.busy:
                return
            self._busy(True)
            self.state_var.set("로컬 입력 처리 중... (완료될 때까지 종료를 제한합니다)")
            def task() -> None:
                try:
                    result = (
                        inspect_input(request) if operation == "preview"
                        else run_scan(request, output_dir, name)
                    )
                    self.queue.put((operation, request, result))
                except Exception as exc:
                    # Never print or log customer code or provider error payloads.
                    self.queue.put(("error", request, (type(exc).__name__, str(exc))))
            threading.Thread(target=task, daemon=True, name="offline-code-checker").start()

        def _preview(self) -> None:
            try:
                request = self._request()
            except (ValueError, KeyError):
                messagebox.showerror("입력 오류", "언어 설정을 확인하세요.")
                return
            self._clear_preview()
            self._dispatch("preview", request)

        def _scan(self) -> None:
            request = self._request()
            if request != self.preview_request:
                self._clear_preview()
                messagebox.showwarning("미리보기 필요", "입력이 변경되었습니다. 다시 미리보기를 실행하세요.")
                return
            folder = self.output_var.get().strip()
            if not folder:
                messagebox.showwarning("저장 위치 필요", "보고서 저장 폴더를 지정하세요.")
                return
            name = "code-checker-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            self._dispatch("scan", request, folder, name)

        def _poll(self) -> None:
            try:
                while True:
                    operation, request, payload = self.queue.get_nowait()
                    self._busy(False)
                    if operation == "error":
                        error_type, message = payload
                        self.preview_request = None
                        self.scan_button.configure(state="disabled")
                        self.state_var.set("실패/차단 — 검사 완료로 처리하지 않았습니다.")
                        self._show(f"처리 실패 ({error_type})\n{message}\n\n원본 자료는 변경하지 않았습니다.")
                    elif operation == "preview":
                        self.preview_request = request
                        self.state_var.set("미리보기 완료. 검사 버튼을 사용할 수 있습니다.")
                        self.scan_button.configure(state="normal")
                        self._show(payload.display())
                    else:
                        self.last_result = payload
                        self.state_var.set(
                            "검사 완료(범위 한정)" if payload.status == "complete"
                            else "부분 검사 — 보고서의 누락·제한 항목을 확인하세요."
                        )
                        self.open_button.configure(state="normal")
                        self._show(payload.display())
            except queue.Empty:
                pass
            self.root.after(100, self._poll)

        def _open(self) -> None:
            if self.busy or self.last_result is None:
                return
            try:
                path = self.last_result.html_path.resolve(strict=True)
                if sys.platform == "win32":
                    os.startfile(str(path))
                else:
                    import webbrowser
                    webbrowser.open_new_tab(path.as_uri())
            except (OSError, ValueError) as exc:
                messagebox.showerror("열기 실패", f"로컬 HTML을 열지 못했습니다 ({type(exc).__name__}).")

        def _on_close(self) -> None:
            if self.busy:
                messagebox.showwarning("검사 진행 중", "현재 작업이 완료될 때까지 종료를 제한합니다.")
                return
            self.root.destroy()

    try:
        root = tk.Tk()
    except tk.TclError:
        print("GUI unavailable: desktop display initialization failed.", file=sys.stderr)
        return 2
    CodeCheckerWindow(root)
    root.mainloop()
    return 0


def packaged_smoke_test() -> int:
    """Synthetic-only packaged EXE smoke test, not a GUI interaction test."""
    import tempfile
    from pathlib import Path

    try:
        with tempfile.TemporaryDirectory(prefix="code-checker-smoke-") as folder:
            result = run_scan(
                ScanRequest("paste", text="eval('1+1')\n", language="python"),
                Path(folder) / "reports", "synthetic-smoke",
            )
            if (
                result.status != "complete" or result.findings < 1
                or result.verified < 1
                or not result.html_path.is_file()
                or not result.markdown_path.is_file()
            ):
                return 1
    except Exception:
        return 1
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        raise SystemExit(packaged_smoke_test())
    if len(sys.argv) != 1:
        raise SystemExit(2)
    raise SystemExit(launch())
