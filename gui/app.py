"""
app.py
The RiskRadder desktop window (CustomTkinter) - polished design.
"""

import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from modules.file_reader import FileReadError, read_file
from modules.recommender import add_guidance
from modules.report_generator import REPORTS_DIR, generate_report
from modules.risk_engine import CATEGORY_SEVERITY, analyze_text
from modules.text_output import build_text_report

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

DARK = "#0D1B1A"
PANEL = "#142826"
PANEL_LINE = "#1F3A34"
MINT = "#2DD4A7"
GREEN = "#0E9F78"
GREEN_HOVER = "#0B8564"
BG = "#F1F6F4"
WHITE = "#FFFFFF"
LINE = "#E1EAE7"
TEXT = "#10201E"
MUTED = "#5B6B68"
SOFT_TEXT = "#9FB4AF"
FONT = "Segoe UI"

SEVERITY_COLORS = {
    "High": {"strong": "#D64545", "soft": "#FBE9E9", "text": "#A32D2D"},
    "Medium": {"strong": "#E8A317", "soft": "#FDF3DC", "text": "#7A4F00"},
    "Low": {"strong": "#2E9E6B", "soft": "#E3F4EC", "text": "#1F6E4A"},
}
SEVERITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}

DOC_TYPES = [("Documents", "*.pdf *.docx *.txt"), ("All files", "*.*")]
IMAGE_TYPES = [("Images", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp")]


def font(size, weight="normal", slant="roman"):
    return ctk.CTkFont(family=FONT, size=size, weight=weight, slant=slant)


class RiskRadderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("RiskRadder - Terms and Conditions Risk Analyzer")
        self.geometry("1180x740")
        self.minsize(980, 640)
        self.configure(fg_color=BG)

        self.file_path = None
        self.photo_path = None
        self.result = None
        self.source_name = "Pasted text"
        self.messages = queue.Queue()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()
        self._on_mode_change("File")
        self._show_welcome()
        self.after(100, self._poll_messages)

    # ---------------------------------------------------------------- drawing
    @staticmethod
    def _draw_radar(canvas, size, ring, width=2, dots=()):
        c = size / 2
        for fraction in (0.46, 0.31, 0.16):
            r = size * fraction
            canvas.create_oval(c - r, c - r, c + r, c + r, outline=ring, width=width)
        canvas.create_line(c, size * 0.04, c, size * 0.96, fill=ring)
        canvas.create_line(size * 0.04, c, size * 0.96, c, fill=ring)
        canvas.create_oval(c - 3, c - 3, c + 3, c + 3, fill=MINT, outline=MINT)
        for dx, dy, color in dots:
            x, y = c + dx * size, c + dy * size
            canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill=color, outline=color)

    @staticmethod
    def _draw_gauge(canvas, score, color, size=150):
        pad = 14
        box = (pad, pad, size - pad, size - pad)
        canvas.create_arc(*box, start=90, extent=359.9, style="arc",
                          outline="#E3ECE9", width=14)
        if score > 0:
            extent = -max(4.0, score / 100 * 359.9)
            canvas.create_arc(*box, start=90, extent=extent, style="arc",
                              outline=color, width=14)
        canvas.create_text(size / 2, size / 2 - 6, text=str(score),
                           font=(FONT, 34, "bold"), fill=TEXT)
        canvas.create_text(size / 2, size / 2 + 26, text="out of 100",
                           font=(FONT, 10), fill=MUTED)

    def _wrap(self, offset, minimum=380):
        return max(minimum, self.winfo_width() - offset)

    # ---------------------------------------------------------------- sidebar
    def _build_sidebar(self):
        side = ctk.CTkFrame(self, width=330, corner_radius=0, fg_color=DARK)
        side.grid(row=0, column=0, sticky="nsew")
        side.pack_propagate(False)

        head = ctk.CTkFrame(side, fg_color="transparent")
        head.pack(fill="x", padx=22, pady=(26, 0))
        logo = tk.Canvas(head, width=46, height=46, bg=DARK, highlightthickness=0)
        logo.pack(side="left")
        self._draw_radar(logo, 46, MINT, width=2)
        names = ctk.CTkFrame(head, fg_color="transparent")
        names.pack(side="left", padx=(12, 0))
        ctk.CTkLabel(names, text="RiskRadder", font=font(24, "bold"),
                     text_color="white").pack(anchor="w")
        ctk.CTkLabel(names, text="Terms and Conditions Risk Analyzer",
                     font=font(11), text_color=SOFT_TEXT).pack(anchor="w")

        ctk.CTkLabel(side, text="Choose input", font=font(12),
                     text_color=SOFT_TEXT).pack(anchor="w", padx=22, pady=(26, 0))
        self.mode_button = ctk.CTkSegmentedButton(
            side, values=["File", "Paste text", "Photo"],
            command=self._on_mode_change,
            fg_color=PANEL, selected_color=GREEN, selected_hover_color=GREEN,
            unselected_color=PANEL, unselected_hover_color=PANEL_LINE,
            text_color="white", font=font(13, "bold"), height=36,
        )
        self.mode_button.pack(fill="x", padx=22, pady=(6, 14))

        self.input_card = ctk.CTkFrame(side, fg_color=PANEL, corner_radius=14)
        self.input_card.pack(fill="both", expand=True, padx=22)

        self.file_frame = ctk.CTkFrame(self.input_card, fg_color="transparent")
        ctk.CTkButton(
            self.file_frame, text="Choose PDF, DOCX or TXT file", height=40,
            fg_color=GREEN, hover_color=GREEN_HOVER, font=font(13, "bold"),
            corner_radius=10, command=self._choose_file,
        ).pack(fill="x")
        self.file_label = ctk.CTkLabel(
            self.file_frame, text="No file chosen", text_color=SOFT_TEXT,
            font=font(12), wraplength=250, justify="left",
        )
        self.file_label.pack(anchor="w", pady=(10, 0))

        self.text_frame = ctk.CTkFrame(self.input_card, fg_color="transparent")
        self.paste_box = ctk.CTkTextbox(
            self.text_frame, wrap="word", fg_color="#0F1F1D", text_color="white",
            border_width=1, border_color=PANEL_LINE, font=font(13),
        )
        self.paste_box.pack(fill="both", expand=True)

        self.photo_frame = ctk.CTkFrame(self.input_card, fg_color="transparent")
        ctk.CTkButton(
            self.photo_frame, text="Choose photo or screenshot", height=40,
            fg_color=GREEN, hover_color=GREEN_HOVER, font=font(13, "bold"),
            corner_radius=10, command=self._choose_photo,
        ).pack(fill="x")
        self.photo_label = ctk.CTkLabel(
            self.photo_frame, text="No photo chosen", text_color=SOFT_TEXT,
            font=font(12), wraplength=250, justify="left",
        )
        self.photo_label.pack(anchor="w", pady=(10, 0))
        ctk.CTkLabel(
            self.photo_frame,
            text="Photos are read with Tesseract OCR. Clear, straight and "
                 "well-lit pictures work best.",
            text_color=SOFT_TEXT, font=font(12), wraplength=250, justify="left",
        ).pack(anchor="w", pady=(12, 0))

        self.analyze_button = ctk.CTkButton(
            side, text="Analyze document", height=48, corner_radius=12,
            fg_color=MINT, hover_color="#25B88F", text_color=DARK,
            font=font(15, "bold"), command=self._start_analysis,
        )
        self.analyze_button.pack(fill="x", padx=22, pady=(16, 10))

        ctk.CTkLabel(
            side, text="Not legal advice. Results show possible risks only.",
            font=font(11), text_color=SOFT_TEXT, wraplength=280, justify="left",
        ).pack(anchor="w", padx=22, pady=(0, 22))

    def _on_mode_change(self, mode):
        self.mode_button.set(mode)
        for frame in (self.file_frame, self.text_frame, self.photo_frame):
            frame.pack_forget()
        if mode == "File":
            self.file_frame.pack(fill="x", padx=14, pady=14)
        elif mode == "Paste text":
            self.text_frame.pack(fill="both", expand=True, padx=14, pady=14)
        else:
            self.photo_frame.pack(fill="x", padx=14, pady=14)

    def _choose_file(self):
        path = filedialog.askopenfilename(title="Choose a document", filetypes=DOC_TYPES)
        if path:
            self.file_path = path
            self.file_label.configure(text=os.path.basename(path), text_color="white")

    def _choose_photo(self):
        path = filedialog.askopenfilename(title="Choose a photo", filetypes=IMAGE_TYPES)
        if path:
            self.photo_path = path
            self.photo_label.configure(text=os.path.basename(path), text_color="white")

    # ------------------------------------------------------------------- main
    def _build_main(self):
        main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 8))
        ctk.CTkLabel(header, text="Analysis results", font=font(24, "bold"),
                     text_color=TEXT).pack(side="left")
        self.subtitle = ctk.CTkLabel(header, text="", font=font(13),
                                     text_color=MUTED)
        self.subtitle.pack(side="left", padx=(14, 0), pady=(6, 0))

        self.results = ctk.CTkScrollableFrame(
            main, fg_color=BG, corner_radius=0,
            scrollbar_button_color="#C9D6D3", scrollbar_button_hover_color="#AFC2BD",
        )
        self.results.grid(row=1, column=0, sticky="nsew", padx=(24, 12))

        bar = ctk.CTkFrame(main, fg_color="transparent")
        bar.grid(row=2, column=0, sticky="ew", padx=24, pady=(8, 18))
        self.status_label = ctk.CTkLabel(bar, text="", font=font(12), text_color=MUTED)
        self.status_label.pack(side="left")
        ctk.CTkButton(
            bar, text="Save as PDF", width=140, height=38, corner_radius=10,
            fg_color=GREEN, hover_color=GREEN_HOVER, font=font(13, "bold"),
            command=self._save_pdf,
        ).pack(side="right")
        ctk.CTkButton(
            bar, text="Copy text", width=120, height=38, corner_radius=10,
            fg_color=WHITE, hover_color="#E8F0ED", text_color=TEXT,
            border_width=1, border_color="#C9D6D3", font=font(13, "bold"),
            command=self._copy_text,
        ).pack(side="right", padx=(0, 8))

    def _clear_results(self):
        for widget in self.results.winfo_children():
            widget.destroy()

    def _card(self, parent=None, pady=(0, 12)):
        card = ctk.CTkFrame(parent or self.results, fg_color=WHITE, corner_radius=16,
                            border_width=1, border_color=LINE)
        card.pack(fill="x", pady=pady, padx=2)
        return card

    def _show_welcome(self):
        self._clear_results()
        self.subtitle.configure(text="")
        card = self._card(pady=(8, 0))

        canvas = tk.Canvas(card, width=170, height=170, bg=WHITE, highlightthickness=0)
        canvas.pack(pady=(26, 6))
        self._draw_radar(
            canvas, 170, "#CFE3DD", width=2,
            dots=((0.22, -0.2, "#D64545"), (-0.24, 0.12, "#E8A317"), (0.16, 0.26, "#2E9E6B")),
        )
        ctk.CTkLabel(card, text="Ready when you are", font=font(22, "bold"),
                     text_color=TEXT).pack()
        ctk.CTkLabel(
            card,
            text="RiskRadder reads Terms and Conditions and Privacy Policies, "
                 "then flags the clauses worth a second look.",
            font=font(14), text_color=MUTED, wraplength=520, justify="center",
        ).pack(pady=(6, 14))

        steps = (
            "Choose a file, paste text or add a photo",
            "Click Analyze document",
            "Review the risks, then copy the text or save a PDF",
        )
        for number, text in enumerate(steps, start=1):
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(pady=3)
            ctk.CTkLabel(row, text=str(number), width=26, height=26, corner_radius=13,
                         fg_color=GREEN, text_color="white",
                         font=font(12, "bold")).pack(side="left")
            ctk.CTkLabel(row, text=text, font=font(14), text_color=TEXT).pack(
                side="left", padx=(10, 0))
        ctk.CTkFrame(card, height=24, fg_color="transparent").pack()

    def _show_message(self, text):
        self._clear_results()
        card = self._card(pady=(8, 0))
        ctk.CTkLabel(card, text=text, font=font(15), text_color=MUTED,
                     wraplength=520, justify="center").pack(padx=30, pady=40)

    # ---------------------------------------------------------------- results
    def _render_result(self, result):
        self._clear_results()
        self.update_idletasks()
        tone = SEVERITY_COLORS[result["level"]]

        top = self._card()
        gauge = tk.Canvas(top, width=150, height=150, bg=WHITE, highlightthickness=0)
        gauge.pack(side="left", padx=(20, 10), pady=18)
        self._draw_gauge(gauge, result["score"], tone["strong"])

        info = ctk.CTkFrame(top, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=(8, 20), pady=18)
        ctk.CTkLabel(info, text=f"{result['level']} risk", font=font(22, "bold"),
                     text_color=tone["text"]).pack(anchor="w")
        wrap = self._wrap(640)
        ctk.CTkLabel(info, text=result["summary"], font=font(14), text_color=TEXT,
                     wraplength=wrap, justify="left").pack(anchor="w", pady=(4, 0))
        if result["overall_advice"]:
            ctk.CTkLabel(info, text=result["overall_advice"], font=font(14, "bold"),
                         text_color=TEXT, wraplength=wrap, justify="left").pack(
                anchor="w", pady=(6, 0))
        pills = ctk.CTkFrame(info, fg_color="transparent")
        pills.pack(anchor="w", pady=(12, 0))
        for level in ("High", "Medium", "Low"):
            pill_tone = SEVERITY_COLORS[level]
            ctk.CTkLabel(
                pills, text=f"  {result['severity_counts'][level]} {level}  ",
                fg_color=pill_tone["soft"], text_color=pill_tone["text"],
                corner_radius=8, height=26, font=font(12, "bold"),
            ).pack(side="left", padx=(0, 8))

        if result["category_counts"]:
            self._add_breakdown(result["category_counts"])

        if not result["flagged"]:
            card = self._card()
            ctk.CTkLabel(card, text="No risky clauses were detected.", font=font(14),
                         text_color=MUTED).pack(padx=20, pady=24)
            return

        ctk.CTkLabel(self.results, text="Flagged clauses", font=font(17, "bold"),
                     text_color=TEXT).pack(anchor="w", padx=4, pady=(8, 2))
        ordered = sorted(
            result["flagged"],
            key=lambda item: (SEVERITY_ORDER[item["severity"]], item["id"]),
        )
        for item in ordered:
            self._add_clause_card(item)

    def _add_breakdown(self, category_counts):
        card = self._card()
        ctk.CTkLabel(card, text="Risk breakdown", font=font(15, "bold"),
                     text_color=TEXT).pack(anchor="w", padx=20, pady=(14, 6))
        ordered = sorted(category_counts.items(), key=lambda kv: -kv[1])
        biggest = ordered[0][1]
        for name, count in ordered:
            level = CATEGORY_SEVERITY.get(name, "Medium")
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=3)
            ctk.CTkLabel(row, text=name, width=210, anchor="w", font=font(13),
                         text_color=TEXT).pack(side="left")
            bar = ctk.CTkProgressBar(
                row, height=10, corner_radius=5, fg_color="#E3ECE9",
                progress_color=SEVERITY_COLORS[level]["strong"],
            )
            bar.set(count / biggest)
            bar.pack(side="left", fill="x", expand=True, padx=12)
            ctk.CTkLabel(row, text=str(count), width=26, anchor="e",
                         font=font(13, "bold"), text_color=TEXT).pack(side="left")
        ctk.CTkFrame(card, height=10, fg_color="transparent").pack()

    def _add_clause_card(self, item):
        tone = SEVERITY_COLORS[item["severity"]]
        card = self._card(pady=5)

        stripe = ctk.CTkFrame(card, width=5, corner_radius=3, fg_color=tone["strong"])
        stripe.pack(side="left", fill="y", padx=(12, 0), pady=14)
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=16, pady=14)

        header = ctk.CTkFrame(body, fg_color="transparent")
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text=f"  {item['severity']}  ", fg_color=tone["soft"],
            text_color=tone["text"], corner_radius=8, height=24,
            font=font(12, "bold"),
        ).pack(side="left")
        ctk.CTkLabel(header, text=item["category"], font=font(15, "bold"),
                     text_color=TEXT).pack(side="left", padx=(10, 0))
        ctk.CTkLabel(header, text=f"clause {item['id']}", font=font(12),
                     text_color=MUTED).pack(side="right")

        wrap = self._wrap(640)
        quote = ctk.CTkFrame(body, fg_color=BG, corner_radius=8)
        quote.pack(fill="x", pady=(10, 8))
        ctk.CTkLabel(
            quote, text="\u201c" + item["original"] + "\u201d",
            font=font(13, slant="italic"), text_color=TEXT,
            wraplength=wrap - 20, justify="left", anchor="w",
        ).pack(fill="x", padx=12, pady=8)

        for label, text, label_color in (
            ("Why it matters", item["explanation"], MUTED),
            ("What to do", item["recommendation"], GREEN),
        ):
            ctk.CTkLabel(body, text=label, font=font(12, "bold"),
                         text_color=label_color).pack(anchor="w", pady=(4, 0))
            ctk.CTkLabel(body, text=text, font=font(13), text_color=TEXT,
                         wraplength=wrap, justify="left", anchor="w").pack(anchor="w")

    # --------------------------------------------------------------- analysis
    def _start_analysis(self):
        mode = self.mode_button.get()
        text, path, source = None, None, "Pasted text"

        if mode == "Paste text":
            text = self.paste_box.get("1.0", "end").strip()
            if not text:
                messagebox.showinfo("Nothing to analyze", "Paste some text first.")
                return
        elif mode == "File":
            path = self.file_path
            if not path:
                messagebox.showinfo("Nothing to analyze", "Choose a file first.")
                return
            source = os.path.basename(path)
        else:
            path = self.photo_path
            if not path:
                messagebox.showinfo("Nothing to analyze", "Choose a photo first.")
                return
            source = os.path.basename(path)

        self.analyze_button.configure(state="disabled", text="Analyzing...")
        self.status_label.configure(text="")
        self._show_message("Reading and analyzing the document...")
        threading.Thread(
            target=self._worker, args=(text, path, source), daemon=True
        ).start()

    def _worker(self, text, path, source):
        try:
            if path:
                text = read_file(path)
            result = add_guidance(analyze_text(text))
            self.messages.put(("result", result, source))
        except (FileReadError, ValueError) as error:
            self.messages.put(("error", str(error), source))
        except Exception as error:
            self.messages.put(("error", f"Something went wrong: {error}", source))

    def _poll_messages(self):
        try:
            while True:
                kind, payload, source = self.messages.get_nowait()
                self.analyze_button.configure(state="normal", text="Analyze document")
                if kind == "result":
                    self.result = payload
                    self.source_name = source
                    self.subtitle.configure(text=source)
                    self._render_result(payload)
                    self.status_label.configure(text=f"Analysis of {source} is ready.")
                else:
                    self._show_welcome()
                    messagebox.showerror("RiskRadder", payload)
        except queue.Empty:
            pass
        self.after(100, self._poll_messages)

    # ---------------------------------------------------------------- outputs
    def _copy_text(self):
        if not self.result:
            messagebox.showinfo("Nothing to copy", "Analyze a document first.")
            return
        self.clipboard_clear()
        self.clipboard_append(build_text_report(self.result, self.source_name))
        self.status_label.configure(text="Report text copied to the clipboard.")

    def _save_pdf(self):
        if not self.result:
            messagebox.showinfo("Nothing to save", "Analyze a document first.")
            return
        REPORTS_DIR.mkdir(exist_ok=True)
        path = filedialog.asksaveasfilename(
            title="Save PDF report",
            initialdir=str(REPORTS_DIR),
            initialfile="RiskRadder_Report.pdf",
            defaultextension=".pdf",
            filetypes=[("PDF file", "*.pdf")],
        )
        if not path:
            return
        try:
            generate_report(self.result, self.source_name, path)
        except Exception as error:
            messagebox.showerror("RiskRadder", f"Could not save the PDF: {error}")
            return
        self.status_label.configure(text=f"PDF saved: {os.path.basename(path)}")
        try:
            os.startfile(path)
        except Exception:
            pass