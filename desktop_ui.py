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

from report_cleanup import (
    ReportCleanupError, delete_report_pair, validate_current_report_receipt,
)
from report_history import list_historical_reports, validate_historical_report
from output_safety import validate_output_location
from code_input import InputError
from desktop_core import (
    ProgressUpdate, ScanCancelled, ScanControl, ScanRequest, ScanResult,
    inspect_input, run_scan,
)


def launch(on_ready=None) -> int:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, scrolledtext, ttk
    except ImportError:
        print("GUI unavailable: tkinter was not installed.", file=sys.stderr)
        return 2

    class CodeCheckerWindow:
        def __init__(self, root: tk.Tk) -> None:
            self.root = root
            self.root.title("코드체커 — 로컬 코드 위험 점검")
            self.root.minsize(780, 680)
            self.root.geometry("930x790")
            self.root.protocol("WM_DELETE_WINDOW", self._on_close)

            self.kind = "path"
            self.source_var = tk.StringVar()
            self.language_var = tk.StringVar(value="자동")
            self.paste_filename_var = tk.StringVar(value="pasted.txt")
            self.output_var = tk.StringVar(value=str(Path.home() / "CodeCheckerReports"))
            self.state_var = tk.StringVar(value="먼저 파일·폴더 또는 붙여넣기를 선택하세요.")
            self.queue: queue.Queue[tuple[str, ScanRequest, object]] = queue.Queue()
            self.busy = False
            self.active_control: ScanControl | None = None
            self.preview_request: ScanRequest | None = None
            self.preview_fingerprint: str | None = None
            self.last_result: ScanResult | None = None
            self._build_widgets(ttk, tk, scrolledtext)
            self.paste_filename_var.trace_add("write", lambda *_: self._clear_preview())
            self.root.after(100, self._poll)

        def _build_widgets(self, ttk, tk, scrolledtext) -> None:
            container = ttk.Frame(self.root, padding=18)
            container.pack(fill="both", expand=True)
            ttk.Label(
                container, text="오프라인 코드체커", font=("Malgun Gothic", 18, "bold")
            ).pack(anchor="w")
            ttk.Label(
                container, text="Python AST + 제한적 정적 규칙 · 기본 로컬 분석 · AI 키 불필요"
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
            ttk.Label(
                choose,
                text="로컬 파일·폴더만 검사 · 연결 네트워크 드라이브 입력 차단 (파일 선택창은 별도 동작)",
            ).pack(anchor="w", pady=(6, 2))

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
            ttk.Label(choose, text="붙여넣기 가상 파일명 (.py/.pyi/.js/.ts/.txt, 경로 입력 불가)").pack(anchor="w")
            self.paste_filename_entry = ttk.Entry(choose, textvariable=self.paste_filename_var, width=35)
            self.paste_filename_entry.pack(anchor="w", pady=(3, 7))
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
            self.output_button.pack(side="left", padx=(0, 8))
            self.history_button = ttk.Button(
                pathbar, text="기존 보고서 열기", command=self._open_historical_report
            )
            self.history_button.pack(side="left", padx=(0, 8))
            self.recent_button = ttk.Button(
                pathbar, text="최근 목록", command=self._browse_recent_reports
            )
            self.recent_button.pack(side="left")
            ttk.Label(
                target,
                text="네트워크 드라이브·알려진 동기화 폴더 저장 차단 · 비동기화 로컬 폴더를 선택하세요.",
            ).pack(anchor="w", pady=(6, 0))

            actions = ttk.Frame(container)
            actions.pack(fill="x", pady=(12, 6))
            self.preview_button = ttk.Button(actions, text="① 입력 미리보기", command=self._preview)
            self.preview_button.pack(side="left", padx=(0, 10))
            self.scan_button = ttk.Button(actions, text="② 로컬 검사 및 보고서 생성", command=self._scan, state="disabled")
            self.scan_button.pack(side="left", padx=(0, 10))
            self.open_button = ttk.Button(actions, text="HTML 결과 열기", command=self._open, state="disabled")
            self.open_button.pack(side="left", padx=(0, 10))
            self.delete_button = ttk.Button(
                actions, text="현재 보고서 삭제", command=self._delete_current_report, state="disabled"
            )
            self.delete_button.pack(side="left", padx=(0, 10))
            self.cancel_button = ttk.Button(
                actions, text="진행 중 취소", command=self._cancel, state="disabled"
            )
            self.cancel_button.pack(side="left")

            self.progress_bar = ttk.Progressbar(container, orient="horizontal", mode="determinate", maximum=1)
            self.progress_bar.pack(fill="x", pady=(4, 2))
            ttk.Label(container, textvariable=self.state_var).pack(anchor="w", pady=(6, 5))
            self.result_text = scrolledtext.ScrolledText(
                container, height=13, state="disabled", wrap="word", font=("Malgun Gothic", 10)
            )
            self.result_text.pack(fill="both", expand=True)
            self._show(
                "미리보기를 먼저 실행한 다음 검사를 시작할 수 있습니다.\n"
                "미리보기 이후 파일·범위가 달라지면 검사를 차단하고 다시 미리보기를 요구합니다.\n"
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
            self.preview_fingerprint = None
            # A new source or changed input invalidates the previous result.
            # Keep stale HTML from being mistaken for this source's scan.
            self.last_result = None
            if not self.busy:
                self.scan_button.configure(state="disabled")
                self.open_button.configure(state="disabled")
                self.delete_button.configure(state="disabled")

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
                return ScanRequest("paste", text=self.paste_text.get("1.0", "end-1c"),
                                   language=language, filename=self.paste_filename_var.get())
            return ScanRequest("path", source=self.source_var.get(), language=language)

        def _busy(self, enabled: bool) -> None:
            self.busy = enabled
            state = "disabled" if enabled else "normal"
            for button in (
                self.file_button, self.folder_button, self.paste_button,
                self.clear_button, self.preview_button, self.output_button,
                self.history_button,
            ):
                button.configure(state=state)
            self.language_select.configure(state="disabled" if enabled else "readonly")
            self.paste_filename_entry.configure(state=state)
            self.paste_text.configure(state=state)
            self.output_entry.configure(state=state)
            self.open_button.configure(state="disabled" if enabled or self.last_result is None else "normal")
            self.delete_button.configure(
                state="normal"
                if not enabled and self.last_result is not None
                and self.last_result.report_receipt is not None else "disabled"
            )
            self.scan_button.configure(state="disabled" if enabled or self.preview_request is None else "normal")
            self.cancel_button.configure(state="normal" if enabled else "disabled")

        def _cancel(self) -> None:
            if not self.busy or self.active_control is None:
                return
            accepted = self.active_control.cancel()
            self.cancel_button.configure(state="disabled")
            if accepted:
                self.state_var.set("취소 요청됨 — 현재 읽기/검사 단계 종료 시 중단합니다.")
            else:
                self.state_var.set("보고서 저장이 이미 시작되어 취소할 수 없습니다.")

        def _update_progress(self, update: ProgressUpdate) -> None:
            if self.active_control is not None and self.active_control.cancel_requested.is_set():
                return
            labels = {
                "reading": "입력 읽기/정규화 중 — 파일 수 집계 전",
                "scan": "정적 규칙 검사 중",
                "report": "보고서 근거 대조 중",
                "publishing": "HTML/Markdown 파일 저장 중 — 취소 불가 구간",
                "done": "보고서 저장 완료",
                "preview": "입력 미리보기 작성 완료",
            }
            if update.phase == "scan" and update.total > 0:
                self.progress_bar.configure(maximum=update.total, value=update.completed)
                self.state_var.set(
                    f"{labels[update.phase]}: {update.completed}/{update.total}개 파일"
                )
            else:
                if update.phase == "reading":
                    self.progress_bar.configure(maximum=1, value=0)
                self.state_var.set(labels[update.phase])
            if update.phase in {"publishing", "done"}:
                # Publishing has an atomic no-overwrite boundary and cannot be interrupted.
                self.cancel_button.configure(state="disabled")

        def _dispatch(self, operation: str, request: ScanRequest, output_dir: str = "", name: str = "") -> None:
            if self.busy:
                return
            control = ScanControl(
                on_update=lambda update: self.queue.put(("progress", request, update))
            )
            self.active_control = control
            preview_fingerprint = self.preview_fingerprint if operation == "scan" else None
            self.progress_bar.configure(maximum=1, value=0)
            self._busy(True)
            self.state_var.set("로컬 입력 처리 중... (취소 요청 가능)")
            def task() -> None:
                try:
                    result = (
                        inspect_input(request, control=control) if operation == "preview"
                        else run_scan(
                            request, output_dir, name, control=control,
                            expected_preview_fingerprint=preview_fingerprint,
                        )
                    )
                    self.queue.put((operation, request, result))
                except ScanCancelled:
                    self.queue.put(("cancelled", request, None))
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
            if request != self.preview_request or not self.preview_fingerprint:
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
                    if operation == "progress":
                        self._update_progress(payload)
                        continue
                    self._busy(False)
                    self.active_control = None
                    if operation == "cancelled":
                        self.preview_fingerprint = None
                        self.preview_request = None
                        self.last_result = None
                        self.scan_button.configure(state="disabled")
                        self.open_button.configure(state="disabled")
                        self.delete_button.configure(state="disabled")
                        self.state_var.set("작업 취소됨 — 새 보고서를 생성하지 않았습니다.")
                        self._show("취소 완료. 원본 파일은 변경하지 않았습니다. 다시 진행하려면 미리보기를 실행하세요.")
                    elif operation == "error":
                        error_type, message = payload
                        self.preview_fingerprint = None
                        self.preview_request = None
                        self.last_result = None
                        self.scan_button.configure(state="disabled")
                        self.open_button.configure(state="disabled")
                        self.delete_button.configure(state="disabled")
                        self.state_var.set("실패/차단 — 검사 완료로 처리하지 않았습니다.")
                        self._show(f"처리 실패 ({error_type})\n{message}\n\n원본 자료는 변경하지 않았습니다.")
                    elif operation == "preview":
                        self.preview_fingerprint = payload.fingerprint
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
                        self.delete_button.configure(
                            state="normal" if payload.report_receipt is not None else "disabled"
                        )
                        self._show(payload.display())
            except queue.Empty:
                pass
            self.root.after(100, self._poll)

        def _delete_current_report(self) -> None:
            """Only the current session's unchanged generated pair may be removed."""
            if self.busy or self.last_result is None:
                return
            receipt = self.last_result.report_receipt
            if receipt is None:
                messagebox.showwarning(
                    "삭제 불가", "현재 실행에서 검증된 보고서 두 파일이 없어 삭제할 수 없습니다."
                )
                return
            if not messagebox.askyesno(
                "현재 보고서 삭제 확인",
                "이번 검사에서 생성한 아래 두 파일만 삭제합니다. 이 작업은 되돌릴 수 없습니다.\n\n"
                + str(receipt.html.path) + "\n" + str(receipt.markdown.path)
                + "\n\n원본 코드와 다른 보고서는 유지됩니다. 삭제하시겠습니까?",
                default="no",
            ):
                return
            try:
                delete_report_pair(receipt)
            except (ReportCleanupError, OSError) as exc:
                self.delete_button.configure(state="disabled")
                self.state_var.set("삭제 거부/실패 — 보고서 파일 상태를 확인하세요.")
                messagebox.showerror(
                    "보고서 삭제 거부/실패",
                    "검증 불일치 또는 I/O 오류로 안전 삭제를 완료하지 못했습니다.\n"
                    + str(exc),
                )
                return
            self.last_result = None
            self.open_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")
            self.state_var.set("현재 실행 보고서 HTML·Markdown 2개 삭제 완료.")
            self._show("선택한 현재 보고서 두 파일만 삭제했습니다. 원본 코드와 다른 보고서는 유지됩니다.")

        def _open(self) -> None:
            if self.busy or self.last_result is None:
                return
            try:
                # A current report may have been replaced or edited since the
                # scan. Never open it as a trusted current-session result
                # unless the HTML AND Markdown still match the captured pair.
                path = validate_current_report_receipt(self.last_result.report_receipt)
                path = path.resolve(strict=True)
                if sys.platform == "win32":
                    os.startfile(str(path))
                else:
                    import webbrowser
                    webbrowser.open_new_tab(path.as_uri())
            except (ReportCleanupError, OSError, ValueError):
                messagebox.showerror(
                    "현재 보고서 열기 거부",
                    "보고서가 생성된 후 수정·교체되었거나 두 파일의 상태를 검증할 수 없습니다. "
                    "기존 파일은 Windows 파일 관리자로 확인하고, 새 분석 결과는 다시 검사해 생성하세요.",
                )

        def _browse_recent_reports(self) -> None:
            """Show bounded local history sorted by file modification time."""
            if self.busy:
                return
            try:
                reports = list_historical_reports(self.output_var.get().strip())
            except (InputError, OSError) as exc:
                messagebox.showerror("최근 보고서 목록", str(exc))
                return
            if not reports:
                messagebox.showinfo("최근 보고서 목록", "검증 가능한 기존 HTML·Markdown 보고서 쌍이 없습니다.")
                return

            dialog = tk.Toplevel(self.root)
            dialog.title("최근 보고서 — 수정시간순 (읽기 전용)")
            dialog.transient(self.root)
            dialog.geometry("600x340")
            frame = ttk.Frame(dialog, padding=12)
            frame.pack(fill="both", expand=True)
            ttk.Label(
                frame, text="로컬 보고서 형식만 확인합니다. 출처 인증이나 안전성 검증은 아닙니다."
            ).pack(anchor="w", pady=(0, 8))
            listing = tk.Listbox(frame, height=min(len(reports), 12), exportselection=False)
            listing.pack(fill="both", expand=True)
            for path in reports:
                listing.insert(tk.END, path.name)
            listing.selection_set(0)

            def open_selected(_event=None) -> None:
                selection = listing.curselection()
                if not selection:
                    return
                selected_path = reports[selection[0]]
                dialog.destroy()
                # The file could change while the list is displayed.
                self._open_historical_report(selected_path)

            buttons = ttk.Frame(frame)
            buttons.pack(fill="x", pady=(8, 0))
            ttk.Button(buttons, text="선택한 보고서 열기", command=open_selected).pack(
                side="left", padx=(0, 8)
            )
            ttk.Button(buttons, text="취소", command=dialog.destroy).pack(side="left")
            listing.bind("<Double-Button-1>", open_selected)
            listing.bind("<Return>", open_selected)
            dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
            dialog.grab_set()
            listing.focus_set()

        def _open_historical_report(self, selected: Path | None = None) -> None:
            """Read-only previous report selection; never authorizes deletion."""
            if self.busy:
                return
            try:
                folder = validate_output_location(self.output_var.get().strip())
                if not folder.is_dir():
                    raise InputError("보고서 저장 폴더가 존재하지 않습니다.")
            except (InputError, OSError) as exc:
                messagebox.showerror("기존 보고서 열기 차단", str(exc))
                return
            chosen = str(selected) if selected is not None else filedialog.askopenfilename(
                title="기존 코드체커 HTML 보고서 선택 (읽기 전용)",
                initialdir=str(folder),
                filetypes=(("HTML 보고서", "*.html"),),
            )
            if not chosen:
                return
            try:
                validated = validate_historical_report(folder, chosen)
                if sys.platform == "win32":
                    os.startfile(str(validated))
                else:
                    import webbrowser
                    webbrowser.open_new_tab(validated.as_uri())
            except (InputError, OSError, ValueError) as exc:
                messagebox.showerror("기존 보고서 열기 차단", str(exc))
                return
            self.state_var.set("선택한 기존 로컬 보고서를 읽기 전용으로 열었습니다.")
            # Deliberately do not set last_result/receipt or enable deletion.
            self._show(
                "기존 HTML 보고서를 열었습니다. 이 파일은 현재 실행의 보고서가 아니므로 "
                "프로그램에서 삭제할 수 없습니다. 보고서 형식 확인은 출처 인증이 아닙니다."
            )

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
    window = CodeCheckerWindow(root)
    if on_ready is not None:
        # Explicit opt-in injection for synthetic Windows Tk integration tests.
        # Production launch never calls it.
        root.after(0, lambda: on_ready(window))
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



def packaged_scenario_smoke_test() -> int:
    """Drive actual frozen Tk widgets with synthetic code and local reports.

    This is intentionally not a retail Windows, OS-packet, Defender or human
    PDF visual acceptance check. No customer files, internet or browser.
    """
    import tempfile
    import time
    from pathlib import Path

    success = [False]
    failures: list[str] = []
    try:
        with tempfile.TemporaryDirectory(prefix="code-checker-frozen-gui-") as temp:
            output = Path(temp) / "synthetic-local-reports"

            def on_ready(window) -> None:
                deadline = time.monotonic() + 35

                def fail(reason: str) -> None:
                    failures.append(reason)
                    window.root.destroy()

                def await_phase(expected: str) -> None:
                    if time.monotonic() > deadline:
                        fail("timeout-" + expected)
                        return
                    if not window.root.winfo_exists():
                        return
                    try:
                        if expected == "preview":
                            if not window.busy and window.preview_request is not None:
                                if window.scan_button.instate(["disabled"]):
                                    fail("scan-button-disabled")
                                    return
                                window.scan_button.invoke()
                                window.root.after(40, lambda: await_phase("report"))
                                return
                        elif expected == "report":
                            if not window.busy and window.last_result is not None:
                                result = window.last_result
                                if (
                                    result.status != "complete" or result.findings < 1
                                    or result.verified < 1
                                    or not result.html_path.is_file()
                                    or not result.markdown_path.is_file()
                                    or result.html_path.parent != output
                                    or window.open_button.instate(["disabled"])
                                    or window.delete_button.instate(["disabled"])
                                    or result.report_receipt is None
                                ):
                                    fail("frozen-scan-or-controls-invalid")
                                    return
                                report_html = result.html_path.read_text(encoding="utf-8")
                                report_markdown = result.markdown_path.read_text(encoding="utf-8")
                                if (
                                    "코드체커 오프라인 진단 보고서" not in report_html
                                    or "코드체커 오프라인 진단 보고서" not in report_markdown
                                    or "eval" not in report_html
                                    or "<!doctype html>" not in report_html.lower()
                                ):
                                    fail("frozen-report-content-invalid")
                                    return
                                success[0] = True
                                window.root.destroy()
                                return
                        if not window.busy and "실패" in window.state_var.get():
                            fail("gui-reported-error-" + expected)
                            return
                        window.root.after(40, lambda: await_phase(expected))
                    except Exception as error:
                        fail("phase-" + expected + "-" + type(error).__name__)

                try:
                    window.paste_button.invoke()
                    window.language_var.set("Python")
                    window.paste_text.delete("1.0", "end")
                    window.paste_text.insert("1.0", "eval('1+1')\n")
                    window.output_var.set(str(output))
                    window.root.update_idletasks()
                    window.preview_button.invoke()
                    await_phase("preview")
                except Exception as error:
                    fail("setup-" + type(error).__name__)

            result_code = launch(on_ready=on_ready)
            if result_code != 0 or not success[0] or failures:
                print("FROZEN_GUI_SCENARIO_FAILURE=" + ",".join(failures), file=sys.stderr)
                return 1
        print("FROZEN_GUI_PREVIEW_SCAN_REPORT_PASS")
        print("FROZEN_GUI_REAL_CUSTOMER_DEVICE=UNVERIFIED")
        print("OS_PACKET_CAPTURE=UNVERIFIED")
        return 0
    except Exception as error:
        print("FROZEN_GUI_SCENARIO_FAILURE=" + type(error).__name__, file=sys.stderr)
        return 1


def packaged_gui_smoke_test() -> int:
    """Check real Tk initialization in the packaged process, no project data."""
    try:
        import tkinter as tk
        from tkinter import ttk

        root = tk.Tk()
        try:
            root.title("CodeCheckerOffline synthetic Tk smoke")
            button = ttk.Button(root, text="synthetic")
            button.pack()
            root.update_idletasks()
            root.update()
            if not button.winfo_exists() or not root.winfo_exists():
                return 1
        finally:
            root.destroy()
    except Exception:
        return 1
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--scenario-smoke":
        raise SystemExit(packaged_scenario_smoke_test())
    if len(sys.argv) == 2 and sys.argv[1] == "--gui-smoke":
        raise SystemExit(packaged_gui_smoke_test())
    if len(sys.argv) == 3 and sys.argv[1] == "--runtime-version-receipt":
        from scripts.runtime_version_receipt import main as runtime_version_main
        raise SystemExit(runtime_version_main(["--write-frozen", sys.argv[2]]))
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        raise SystemExit(packaged_smoke_test())
    if len(sys.argv) != 1:
        raise SystemExit(2)
    raise SystemExit(launch())
