import os
import re
from PyQt6.Qsci import (
    QsciScintilla,
    QsciLexerPython,
    QsciLexerJavaScript,
    QsciLexerHTML,
    QsciLexerCSS,
    QsciLexerCPP,
    QsciLexerJSON,
    QsciLexerXML,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QToolTip, QColorDialog
from app.ui.smart_editor_mixin import SmartEditorMixin
from app.ui.code_folding_mixin import CodeFoldingMixin
from app.core.linter import LiveLinter, LintIssue


# Soft, vibrant Rainbow colors for Rainbow Indent Guides
RAINBOW_COLORS = [
    QColor(239, 68, 68, 140),   # Red
    QColor(249, 115, 22, 140),  # Orange
    QColor(234, 179, 8, 140),   # Yellow
    QColor(34, 197, 94, 140),   # Green
    QColor(59, 130, 246, 140),  # Blue
    QColor(168, 85, 247, 140),  # Purple
]


class JSXCustomLexer(QsciLexerJavaScript):
    """JSX/TSX teglarini ko'rinadigan tarzda ranglaydigan maxsus lexer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDefaultPaper(QColor("#1e1e1e"))
        self.setDefaultColor(QColor("#d4d4d4"))

        style_map = {
            "keyword": getattr(QsciLexerJavaScript, "Keyword", None),
            "keyword_set_2": getattr(QsciLexerJavaScript, "KeywordSet2", None),
            "double_quoted": getattr(QsciLexerJavaScript, "DoubleQuotedString", None),
            "single_quoted": getattr(QsciLexerJavaScript, "SingleQuotedString", None),
            "raw_string": getattr(QsciLexerJavaScript, "RawString", None),
            "global_class": getattr(QsciLexerJavaScript, "GlobalClass", None),
            "identifier": getattr(QsciLexerJavaScript, "Identifier", None),
            "number": getattr(QsciLexerJavaScript, "Number", None),
            "comment": getattr(QsciLexerJavaScript, "Comment", None),
            "comment_line": getattr(QsciLexerJavaScript, "CommentLine", None),
            "comment_doc": getattr(QsciLexerJavaScript, "CommentDoc", None),
        }

        for style_name, style_id in style_map.items():
            if style_id is None:
                continue

            if style_name == "keyword":
                self.setColor(QColor("#569CD6"), style_id)
            elif style_name == "keyword_set_2":
                self.setColor(QColor("#569CD6"), style_id)
            elif style_name in {"double_quoted", "single_quoted", "raw_string"}:
                self.setColor(QColor("#CE9178"), style_id)
            elif style_name in {"global_class", "identifier"}:
                self.setColor(QColor("#4EC9B0"), style_id)
            elif style_name == "number":
                self.setColor(QColor("#B5CEA8"), style_id)
            elif style_name in {"comment", "comment_line", "comment_doc"}:
                self.setColor(QColor("#6A9955"), style_id)


class ScodeScintillaEditor(CodeFoldingMixin, SmartEditorMixin, QsciScintilla):
    """
    QScintilla asosidagi professional kod redaktori (SmartEditorMixin va CodeFoldingMixin bilan).
    Rainbow Indent Guides, Dynamic Color Picker, AppData Theme Customizing, Qator raqamlari,
    Code Folding, Dark Theme lexer ranglari, Auto-bracket va Live Linting.
    """

    ERROR_INDICATOR_ID = 8
    WARNING_INDICATOR_ID = 9

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lint_issues = []
        self.lint_timer = QTimer(self)
        self.lint_timer.setSingleShot(True)
        self.lint_timer.setInterval(500)
        self.lint_timer.timeout.connect(self._run_live_lint)
        self.live_linter = LiveLinter(self)
        self.live_linter.issuesChanged.connect(self._apply_lint_issues)

        self.rainbow_indent_enabled = True
        self.file_path = ""

        self._configure_editor()
        self._setup_lint_indicators()

    def _configure_editor(self):
        # 1. UTF-8 kodlashni yoqish va uzun chiziqlar uchun gorizontal scroll
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setReadOnly(False)
        self.setFocus()
        self.setUtf8(True)
        self.setWrapMode(QsciScintilla.WrapMode.WrapNone)
        self._configure_scroll_bars()

        # Defolt shrift (Consolas 11pt)
        self.default_font = QFont("Consolas", 11)
        self.default_font.setFixedPitch(True)
        self.setFont(self.default_font)

        # 2. Qator Raqamlari va Marginlar (#1e1e1e fon va #656e7b matn)
        self.setMarginsBackgroundColor(QColor("#1e1e1e"))
        self.setMarginsForegroundColor(QColor("#656e7b"))
        self._set_margin_color(0, QColor("#1e1e1e"), QColor("#656e7b"))

        # Margin 0: Qator raqamlari
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, " 000 ")
        self.setMarginLineNumbers(0, True)

        # Margin 2: Code Folding paneli (VS Code minimalist stili)
        self._setup_vscode_folding_style()

        # Qolgan marginlar kengligini 0 qilish
        for i in (1, 3, 4):
            self.setMarginWidth(i, 0)
            self.setMarginType(i, QsciScintilla.MarginType.SymbolMargin)

        # 3. Redaktor oraliqlari va satr intervallari
        self.setExtraAscent(2)
        self.setExtraDescent(2)
        self.setIndentationGuides(False)  # Biz maxsus Rainbow Indent Guides chazamiz
        self._apply_scrollbar_minimap_style()

        # 3. Karetka (Kursor va Joriy qator ranglari)
        self.setCaretForegroundColor(QColor("#ffffff"))
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#2a2d2e"))
        self.setCaretWidth(2)

        # 4. Indentation & Tabs (Avto Tab tashlash)
        self.setAutoIndent(True)
        self.setTabWidth(4)
        self.setIndentationsUseTabs(False)
        self.setBackspaceUnindents(True)

        self._clear_scintilla_conflicting_keys()
        self._apply_brace_highlight_styles()

        # Multi-Cursor / Multiple Selection (Alt + Click multi cursor typing)
        try:
            self.SendScintilla(2563, 1)  # SCI_SETMULTIPLESELECTION
            self.SendScintilla(2565, 1)  # SCI_SETADDITIONALSELECTIONTYPING
            self.SendScintilla(2614, 1)  # SCI_SETMULTIPASTE
            self.SendScintilla(2567, 1)  # SCI_SETADDITIONALCARETSBLINK
        except Exception:
            pass

        self._setup_lint_indicators()

    # =========================================================================
    # 1. Rainbow Indent Guides Painting
    # =========================================================================
    def paintEvent(self, event):
        super().paintEvent(event)
        if getattr(self, 'rainbow_indent_enabled', True):
            try:
                self._draw_rainbow_indent_guides()
            except Exception:
                pass

    def _draw_rainbow_indent_guides(self):
        """Redaktorda kod indentatsiyasiga mos nozik va chiroyli kamalak chiziqlarini chizish."""
        viewport = self.viewport()
        if not viewport or not viewport.isVisible():
            return

        painter = QPainter(viewport)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

            first_line = self.firstVisibleLine()
            lines_on_screen = self.linesOnScreen()
            total_lines = self.lines()

            tab_width = max(1, self.tabWidth())

            margin_left = 0
            for m_idx in range(5):
                margin_left += max(0, self.marginWidth(m_idx))

            left_pad = self.SendScintilla(2145)  # SCI_GETMARGINLEFT
            if left_pad < 0 or left_pad > 50:
                left_pad = 8
            margin_left += left_pad

            font_metrics = self.fontMetrics()
            char_width = max(1, font_metrics.horizontalAdvance(' '))

            line_height = self.SendScintilla(2276, 0)  # SCI_TEXTHEIGHT
            if line_height <= 0:
                line_height = font_metrics.height() + 4

            hbar = self.horizontalScrollBar()
            h_scroll = hbar.value() if hbar is not None else 0

            rainbow_count = len(RAINBOW_COLORS)

            for i in range(lines_on_screen + 2):
                line_idx = first_line + i
                if line_idx >= total_lines:
                    break

                line_text = self.text(line_idx)
                num_guides = 0

                if line_text.strip():
                    indent_spaces = 0
                    for char in line_text:
                        if char == ' ':
                            indent_spaces += 1
                        elif char == '\t':
                            indent_spaces += tab_width
                        else:
                            break
                    num_guides = indent_spaces // tab_width
                else:
                    # Bo'sh qator bo'lsa, oldingi no-bo'sh qatordan indent darajasini aniqlash
                    prev_idx = line_idx - 1
                    while prev_idx >= 0 and not self.text(prev_idx).strip():
                        prev_idx -= 1
                    if prev_idx >= 0:
                        prev_text = self.text(prev_idx)
                        sp = 0
                        for char in prev_text:
                            if char == ' ':
                                sp += 1
                            elif char == '\t':
                                sp += tab_width
                            else:
                                break
                        num_guides = sp // tab_width

                if num_guides <= 0:
                    continue

                y_top = i * line_height
                y_bottom = y_top + line_height

                line_start_pos = self.SendScintilla(2168, line_idx, 0)  # SCI_POSITIONFROMLINE

                for lvl in range(1, num_guides + 1):
                    col_index = lvl * tab_width
                    target_pos = line_start_pos + col_index

                    # SCI_POINTXFROMPOSITION yordamida aniq X nuqtasini olish
                    sc_x = self.SendScintilla(2164, 0, target_pos)
                    if sc_x > 0:
                        x_pos = sc_x
                    else:
                        x_pos = margin_left + (col_index * char_width) - h_scroll

                    if x_pos < margin_left or x_pos > viewport.width():
                        continue

                    color = RAINBOW_COLORS[(lvl - 1) % rainbow_count]
                    painter.setPen(QPen(color, 1, Qt.PenStyle.SolidLine))
                    painter.drawLine(int(x_pos), int(y_top), int(x_pos), int(y_bottom))
        finally:
            painter.end()

    # =========================================================================
    # 2. Color Picker Integration (Hex & RGB/RGBA detection)
    # =========================================================================
    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        try:
            self._try_open_color_picker()
        except Exception:
            pass

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        if not menu:
            menu = QMenu(self)
        menu.addSeparator()
        action_picker = menu.addAction("🎨 Rangni tanlash (Color Picker)...")
        action_picker.triggered.connect(self._try_open_color_picker)
        menu.exec(event.globalPos())

    def _try_open_color_picker(self):
        """Kursor Hex (#1e1e1e) yoki RGB (rgb(255, 0, 0)) rang ustida bo'lganda Color Picker dialogini ochadi."""
        line, col = self.getCursorPosition()
        line_text = self.text(line)
        sel_text = self.selectedText().strip()

        hex_matches = list(re.finditer(r'#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b', line_text))
        rgb_matches = list(re.finditer(r'rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*(?:,\s*[\d\.]+\s*)?\)', line_text, re.IGNORECASE))

        target_start = -1
        target_end = -1
        target_str = ""
        is_hex = True

        for m in hex_matches:
            if (m.start() <= col <= m.end()) or (m.start() <= col + 1 <= m.end()) or (m.start() - 1 <= col <= m.end()):
                target_start = m.start()
                target_end = m.end()
                target_str = m.group(0)
                is_hex = True
                break

        if target_start == -1:
            for m in rgb_matches:
                if (m.start() <= col <= m.end()) or (m.start() <= col + 1 <= m.end()) or (m.start() - 1 <= col <= m.end()):
                    target_start = m.start()
                    target_end = m.end()
                    target_str = m.group(0)
                    is_hex = False
                    break

        if target_start == -1 and sel_text:
            test_str = sel_text if sel_text.startswith('#') else f"#{sel_text}"
            if QColor(test_str).isValid():
                idx = line_text.find(sel_text)
                if idx != -1:
                    target_start = idx
                    target_end = idx + len(sel_text)
                    target_str = test_str
                    is_hex = True

        if target_start == -1:
            return

        initial_color = QColor(target_str if target_str.startswith('#') else (f"#{target_str}" if is_hex else target_str))
        if not initial_color.isValid():
            initial_color = QColor("#007acc")

        chosen_color = QColorDialog.getColor(initial_color, self, "Scode Color Picker — Rangni Tanlang")
        if chosen_color.isValid():
            if is_hex:
                new_color_str = chosen_color.name()
            else:
                if "rgba" in target_str.lower():
                    new_color_str = f"rgba({chosen_color.red()}, {chosen_color.green()}, {chosen_color.blue()}, {chosen_color.alphaF():.2f})"
                else:
                    new_color_str = f"rgb({chosen_color.red()}, {chosen_color.green()}, {chosen_color.blue()})"

            self.setSelection(line, target_start, line, target_end)
            self.replaceSelectedText(new_color_str)

    # =========================================================================
    # 3. Dynamic Custom Theme Application
    # =========================================================================
    def apply_custom_theme_colors(self, colors: dict):
        """Custom Theme Customizer sozlamalarini redaktor va lexerga darhol tatbiq etish."""
        if not colors:
            return

        bg_ed = colors.get("bg_editor", "#1e1e1e")
        fg_ed = colors.get("fg_text", "#d4d4d4")
        bg_margin = colors.get("bg_margin", "#1e1e1e")
        fg_margin = colors.get("fg_margin", "#656e7b")

        self.setPaper(QColor(bg_ed))
        self.setColor(QColor(fg_ed))

        self.setMarginsBackgroundColor(QColor(bg_margin))
        self.setMarginsForegroundColor(QColor(fg_margin))
        self._set_margin_color(0, QColor(bg_margin), QColor(fg_margin))

        lexer = self.lexer()
        if lexer:
            lexer.setDefaultPaper(QColor(bg_ed))
            lexer.setDefaultColor(QColor(fg_ed))

            if hasattr(lexer, "setColor"):
                if "color_keyword" in colors:
                    kw_col = QColor(colors["color_keyword"])
                    for style_id in (getattr(QsciLexerPython, "Keyword", 5), getattr(QsciLexerJavaScript, "Keyword", 5)):
                        try:
                            lexer.setColor(kw_col, style_id)
                        except Exception:
                            pass

                if "color_string" in colors:
                    str_col = QColor(colors["color_string"])
                    for style_id in (getattr(QsciLexerPython, "DoubleQuotedString", 6), getattr(QsciLexerJavaScript, "DoubleQuotedString", 6)):
                        try:
                            lexer.setColor(str_col, style_id)
                        except Exception:
                            pass

                if "color_comment" in colors:
                    cm_col = QColor(colors["color_comment"])
                    for style_id in (getattr(QsciLexerPython, "Comment", 1), getattr(QsciLexerJavaScript, "Comment", 1)):
                        try:
                            lexer.setColor(cm_col, style_id)
                        except Exception:
                            pass

                if "color_number" in colors:
                    num_col = QColor(colors["color_number"])
                    for style_id in (getattr(QsciLexerPython, "Number", 4), getattr(QsciLexerJavaScript, "Number", 4)):
                        try:
                            lexer.setColor(num_col, style_id)
                        except Exception:
                            pass

        self._apply_brace_highlight_styles()

    def _setup_lint_indicators(self):
        try:
            self.SendScintilla(QsciScintilla.SCI_INDICSETSTYLE, self.ERROR_INDICATOR_ID, QsciScintilla.INDIC_SQUIGGLE)
            self.SendScintilla(QsciScintilla.SCI_INDICSETFORE, self.ERROR_INDICATOR_ID, 0xEF4444)
            self.SendScintilla(QsciScintilla.SCI_INDICSETUNDER, self.ERROR_INDICATOR_ID, True)

            self.SendScintilla(QsciScintilla.SCI_INDICSETSTYLE, self.WARNING_INDICATOR_ID, QsciScintilla.INDIC_SQUIGGLE)
            self.SendScintilla(QsciScintilla.SCI_INDICSETFORE, self.WARNING_INDICATOR_ID, 0xF59E0B)
            self.SendScintilla(QsciScintilla.SCI_INDICSETUNDER, self.WARNING_INDICATOR_ID, True)
        except Exception:
            pass

    def _schedule_lint(self):
        self.lint_timer.start()

    def _run_live_lint(self):
        code = self.text()
        file_path = getattr(self, "file_path", "")
        if not file_path and not code.strip():
            self._apply_lint_issues([])
            return
        self.live_linter.schedule(file_path, code)

    def _apply_lint_issues(self, issues):
        self.lint_issues = issues or []
        self.clearIndicatorRange(0, 0, self.lines(), 0, self.ERROR_INDICATOR_ID)
        self.clearIndicatorRange(0, 0, self.lines(), 0, self.WARNING_INDICATOR_ID)

        for issue in self.lint_issues:
            line = max(0, int(issue.line) - 1)
            if line < 0 or line >= self.lines():
                continue
            start_col = max(0, int(issue.start_column))
            end_col = max(start_col + 1, min(self.lineLength(line), start_col + 8))
            indicator_id = self.ERROR_INDICATOR_ID if str(issue.severity).lower() in {"error", "fatal"} else self.WARNING_INDICATOR_ID
            self.fillIndicatorRange(line, start_col, line, end_col, indicator_id)

    def _clear_lint_issues(self):
        self.clearIndicatorRange(0, 0, self.lines(), 0, self.ERROR_INDICATOR_ID)
        self.clearIndicatorRange(0, 0, self.lines(), 0, self.WARNING_INDICATOR_ID)
        self.lint_issues = []

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if not self.lint_issues:
            return

        pos = event.pos()
        try:
            sc_pos = self.SendScintilla(QsciScintilla.SCI_POSITIONFROMPOINTCLOSE, pos.x(), pos.y())
            line = self.SendScintilla(QsciScintilla.SCI_LINEFROMPOSITION, sc_pos)
            col = self.SendScintilla(QsciScintilla.SCI_GETCOLUMN, sc_pos)
            line_idx = int(line) + 1
            match = None
            for issue in self.lint_issues:
                start = int(issue.line)
                end = int(issue.line) + 1
                if start <= line_idx <= end:
                    start_col = max(0, int(issue.start_column))
                    end_col = max(start_col + 1, int(issue.start_column) + 12)
                    if start_col <= col <= end_col:
                        match = issue
                        break
            if match:
                QToolTip.showText(self.mapToGlobal(pos), f"[{match.code}] {match.message}", self)
            else:
                QToolTip.hideText()
        except Exception:
            QToolTip.hideText()

    def _clear_scintilla_conflicting_keys(self):
        try:
            _ = self.standardCommands()
        except Exception as e:
            print(f"Scintilla keymap check exception: {e}")
        self.setIndentationWidth(4)
        self.setTabWidth(4)
        self.setIndentationsUseTabs(False)
        self.setBackspaceUnindents(True)

        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.setMatchedBraceBackgroundColor(QColor("#2d3748"))
        self.setMatchedBraceForegroundColor(QColor("#38bdf8"))
        self.setUnmatchedBraceBackgroundColor(QColor("#7f1d1d"))
        self.setUnmatchedBraceForegroundColor(QColor("#f87171"))

        self.setSelectionBackgroundColor(QColor("#264f78"))
        self.setSelectionForegroundColor(QColor("#ffffff"))

        self.setPaper(QColor("#1e1e1e"))
        self.setColor(QColor("#d4d4d4"))

    def _apply_brace_highlight_styles(self):
        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.setMatchedBraceBackgroundColor(QColor("#1e293b"))
        self.setMatchedBraceForegroundColor(QColor("#38bdf8"))
        self.setUnmatchedBraceBackgroundColor(QColor("#450a0a"))
        self.setUnmatchedBraceForegroundColor(QColor("#f87171"))
        self.setCaretForegroundColor(QColor("#ffffff"))
        self.setCaretWidth(2)

    def apply_settings(self, font_family: str = "Consolas", font_size: int = 11, tab_size: int = 4):
        self.default_font = QFont(font_family, font_size)
        self.default_font.setFixedPitch(True)
        self.setFont(self.default_font)

        self.setTabWidth(tab_size)
        self.setIndentationWidth(tab_size)
        self.tab_size = tab_size

        lexer = self.lexer()
        if lexer:
            self._apply_dark_base(lexer)
        self._apply_brace_highlight_styles()

    def set_lexer_for_file(self, file_path: str):
        self.file_path = file_path or ""
        ext = os.path.splitext(file_path)[1].lower().lstrip('.') if file_path else ""

        lexer = None
        if ext in ["py", "pyw"]:
            self.set_language("python")
            lexer = QsciLexerPython(self)
            self._apply_dark_base(lexer)
            self._style_python_lexer(lexer)
        elif ext in ["js", "jsx", "ts", "tsx"]:
            self.set_language("javascript")
            if ext in ["jsx", "tsx"]:
                lexer = JSXCustomLexer(self)
            else:
                lexer = QsciLexerJavaScript(self)
            self._apply_dark_base(lexer)
            self._style_javascript_lexer(lexer)
        elif ext == "json":
            self.set_language("json")
            lexer = QsciLexerJSON(self)
            self._apply_dark_base(lexer)
        elif ext in ["html", "htm"]:
            self.set_language("html")
            lexer = QsciLexerHTML(self)
            self._apply_dark_base(lexer)
            self._style_html_lexer(lexer)
        elif ext in ["css", "scss", "less"]:
            self.set_language("css")
            lexer = QsciLexerCSS(self)
            self._apply_dark_base(lexer)
            self._style_css_lexer(lexer)
        elif ext in ["xml", "svg"]:
            self.set_language("xml")
            lexer = QsciLexerXML(self)
            self._apply_dark_base(lexer)
        elif ext in ["cpp", "c", "h", "hpp", "cs"]:
            self.set_language("cpp")
            lexer = QsciLexerCPP(self)
            self._apply_dark_base(lexer)
        else:
            self.set_language("python")
            lexer = None

        if lexer:
            lexer.setDefaultPaper(QColor("#1e1e1e"))
            lexer.setDefaultColor(QColor("#d4d4d4"))
            self.current_lexer = lexer
            self._current_lexer = lexer
            self.setLexer(lexer)
        else:
            self.current_lexer = None
            self._current_lexer = None
            self.setLexer(None)
            self.setFont(self.default_font)

        self._apply_brace_highlight_styles()
        self._enforce_dark_margins()
        self._apply_brace_highlight_styles()

    def _set_margin_color(self, margin: int, bg: QColor, fg: QColor):
        if hasattr(self, "setMarginBackgroundColor"):
            try:
                self.setMarginBackgroundColor(margin, bg)
            except Exception:
                pass
        else:
            try:
                self.SendScintilla(QsciScintilla.SCI_SETMARGINBACK, margin, bg.rgb())
            except Exception:
                pass

        if hasattr(self, "setMarginForegroundColor"):
            try:
                self.setMarginForegroundColor(margin, fg)
            except Exception:
                pass
        else:
            try:
                self.SendScintilla(QsciScintilla.SCI_SETMARGINFORE, margin, fg.rgb())
            except Exception:
                pass

    def _configure_scroll_bars(self):
        for method_name, enabled in (
            ("setVScrollBarEnabled", True),
            ("setVerticalScrollBar", True),
            ("setHScrollBarEnabled", True),
            ("setHorizontalScrollBar", True),
        ):
            method = getattr(self, method_name, None)
            if callable(method):
                try:
                    method(enabled)
                except TypeError:
                    try:
                        method()
                    except Exception:
                        pass

        if hasattr(self, "setScrollWidthTracking"):
            try:
                self.setScrollWidthTracking(True)
            except Exception:
                pass

        if hasattr(self, "horizontalScrollBar"):
            hbar = self.horizontalScrollBar()
            if hbar is not None:
                hbar.setStyleSheet(
                    """
                    QScrollBar:horizontal {
                        background: transparent;
                        height: 6px;
                        margin: 0px;
                        border: none;
                    }
                    QScrollBar::handle:horizontal {
                        background: rgba(255, 255, 255, 0.12);
                        border: 1px solid rgba(255, 255, 255, 0.15);
                        border-radius: 3px;
                        min-width: 30px;
                    }
                    QScrollBar::add-line:horizontal,
                    QScrollBar::sub-line:horizontal,
                    QScrollBar::add-page:horizontal,
                    QScrollBar::sub-page:horizontal {
                        background: transparent;
                        border: none;
                        width: 0px;
                    }
                    """
                )

        vbar = self.verticalScrollBar()
        if vbar is not None:
            vbar.setStyleSheet(
                """
                QScrollBar:vertical {
                    background: transparent;
                    width: 6px;
                    margin: 0px;
                    border: none;
                }
                QScrollBar::handle:vertical {
                    background: rgba(255, 255, 255, 0.10);
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 3px;
                    min-height: 24px;
                }
                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {
                    background: none;
                    border: none;
                    height: 0px;
                }
                QScrollBar::add-page:vertical,
                QScrollBar::sub-page:vertical {
                    background: transparent;
                }
                """
            )

    def _apply_scrollbar_minimap_style(self):
        scrollbar = self.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setStyleSheet(
                """
                QScrollBar:vertical {
                    background: transparent;
                    width: 6px;
                    margin: 0px;
                    border: none;
                }
                QScrollBar::handle:vertical {
                    background: rgba(255, 255, 255, 0.10);
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 3px;
                    min-height: 24px;
                }
                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {
                    background: none;
                    border: none;
                    height: 0px;
                }
                QScrollBar::add-page:vertical,
                QScrollBar::sub-page:vertical {
                    background: transparent;
                }
                """
            )

    def _enforce_dark_margins(self):
        dark_bg = QColor("#1e1e1e")
        margin_fg = QColor("#656e7b")

        self.setMarginsBackgroundColor(dark_bg)
        self.setMarginsForegroundColor(margin_fg)
        self._set_margin_color(0, dark_bg, margin_fg)
        self._set_margin_color(0, QColor("#1e1e1e"), QColor("#656e7b"))
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, " 000 ")
        self.setMarginLineNumbers(0, True)
        self.SendScintilla(QsciScintilla.SCI_SETMARGINLEFT, 0, 8)
        self.SendScintilla(QsciScintilla.SCI_SETMARGINRIGHT, 0, 8)

        self._setup_vscode_folding_style()

        for i in (1, 3, 4):
            self.setMarginWidth(i, 0)
            self.setMarginType(i, QsciScintilla.MarginType.SymbolMargin)

        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#2a2d2e"))
        self.setCaretForegroundColor(QColor("#ffffff"))
        self.setPaper(dark_bg)
        self.setColor(QColor("#d4d4d4"))
        self.setExtraAscent(2)
        self.setExtraDescent(2)
        self._apply_scrollbar_minimap_style()

        self.SendScintilla(QsciScintilla.SCI_STYLESETBACK, QsciScintilla.STYLE_LINENUMBER, dark_bg)
        self.SendScintilla(QsciScintilla.SCI_STYLESETFORE, QsciScintilla.STYLE_LINENUMBER, margin_fg)

    def _setup_vscode_folding_style(self):
        dark_bg = QColor("#1e1e1e")
        arrow_fg = QColor("#c5c5c5")

        self.setFolding(QsciScintilla.FoldStyle.PlainFoldStyle)
        self.setMarginType(2, QsciScintilla.MarginType.SymbolMargin)
        self.setMarginWidth(2, 14)
        self.setMarginSensitivity(2, True)
        self._set_margin_color(2, QColor("#1e1e1e"), QColor("#656e7b"))
        self.setFoldMarginColors(QColor("#1e1e1e"), QColor("#1e1e1e"))

        self.SendScintilla(QsciScintilla.SCI_MARKERDEFINE, QsciScintilla.SC_MARKNUM_FOLDER, QsciScintilla.SC_MARK_ARROW)
        self.SendScintilla(QsciScintilla.SCI_MARKERDEFINE, QsciScintilla.SC_MARKNUM_FOLDEROPEN, QsciScintilla.SC_MARK_ARROWDOWN)
        self.SendScintilla(QsciScintilla.SCI_MARKERDEFINE, QsciScintilla.SC_MARKNUM_FOLDERSUB, QsciScintilla.SC_MARK_EMPTY)
        self.SendScintilla(QsciScintilla.SCI_MARKERDEFINE, QsciScintilla.SC_MARKNUM_FOLDERTAIL, QsciScintilla.SC_MARK_EMPTY)
        self.SendScintilla(QsciScintilla.SCI_MARKERDEFINE, QsciScintilla.SC_MARKNUM_FOLDEREND, QsciScintilla.SC_MARK_EMPTY)
        self.SendScintilla(QsciScintilla.SCI_MARKERDEFINE, QsciScintilla.SC_MARKNUM_FOLDEROPENMID, QsciScintilla.SC_MARK_EMPTY)
        self.SendScintilla(QsciScintilla.SCI_MARKERDEFINE, QsciScintilla.SC_MARKNUM_FOLDERMIDTAIL, QsciScintilla.SC_MARK_EMPTY)

        for m in (
            QsciScintilla.SC_MARKNUM_FOLDER,
            QsciScintilla.SC_MARKNUM_FOLDEROPEN,
            QsciScintilla.SC_MARKNUM_FOLDERSUB,
            QsciScintilla.SC_MARKNUM_FOLDERTAIL,
            QsciScintilla.SC_MARKNUM_FOLDEREND,
            QsciScintilla.SC_MARKNUM_FOLDEROPENMID,
            QsciScintilla.SC_MARKNUM_FOLDERMIDTAIL,
        ):
            self.SendScintilla(QsciScintilla.SCI_MARKERSETFORE, m, arrow_fg)
            self.SendScintilla(QsciScintilla.SCI_MARKERSETBACK, m, dark_bg)

    def _apply_dark_base(self, lexer):
        dark_bg = QColor("#1e1e1e")
        default_fg = QColor("#d4d4d4")
        margin_fg = QColor("#858585")

        lexer.setDefaultFont(self.default_font)
        lexer.setFont(self.default_font)
        lexer.setDefaultPaper(dark_bg)
        lexer.setPaper(dark_bg)
        lexer.setDefaultColor(default_fg)
        lexer.setColor(default_fg)

        for style in range(128):
            lexer.setPaper(dark_bg, style)

        lexer.setPaper(dark_bg, QsciScintilla.STYLE_LINENUMBER)
        lexer.setColor(margin_fg, QsciScintilla.STYLE_LINENUMBER)
        lexer.setPaper(dark_bg, QsciScintilla.STYLE_DEFAULT)
        lexer.setColor(default_fg, QsciScintilla.STYLE_DEFAULT)

    def _style_python_lexer(self, lexer):
        lexer.setColor(QColor("#569CD6"), QsciLexerPython.Keyword)

        str_color = QColor("#CE9178")
        lexer.setColor(str_color, QsciLexerPython.DoubleQuotedString)
        lexer.setColor(str_color, QsciLexerPython.SingleQuotedString)
        lexer.setColor(str_color, QsciLexerPython.TripleSingleQuotedString)
        lexer.setColor(str_color, QsciLexerPython.TripleDoubleQuotedString)

        comment_color = QColor("#6A9955")
        lexer.setColor(comment_color, QsciLexerPython.Comment)
        lexer.setColor(comment_color, QsciLexerPython.CommentBlock)

        lexer.setColor(QColor("#B5CEA8"), QsciLexerPython.Number)
        lexer.setColor(QColor("#DCDCAA"), QsciLexerPython.FunctionMethodName)
        lexer.setColor(QColor("#4EC9B0"), QsciLexerPython.ClassName)
        lexer.setColor(QColor("#9CDCFE"), QsciLexerPython.Identifier)

    def _style_javascript_lexer(self, lexer):
        lexer.setColor(QColor("#569CD6"), QsciLexerJavaScript.Keyword)

        str_color = QColor("#CE9178")
        lexer.setColor(str_color, QsciLexerJavaScript.DoubleQuotedString)
        lexer.setColor(str_color, QsciLexerJavaScript.SingleQuotedString)
        lexer.setColor(str_color, QsciLexerJavaScript.RawString)

        comment_color = QColor("#6A9955")
        lexer.setColor(comment_color, QsciLexerJavaScript.Comment)
        lexer.setColor(comment_color, QsciLexerJavaScript.CommentLine)
        lexer.setColor(comment_color, QsciLexerJavaScript.CommentDoc)

        lexer.setColor(QColor("#B5CEA8"), QsciLexerJavaScript.Number)

    def _style_html_lexer(self, lexer):
        lexer.setColor(QColor("#569CD6"), QsciLexerHTML.Tag)
        lexer.setColor(QColor("#9CDCFE"), QsciLexerHTML.Attribute)

        str_color = QColor("#CE9178")
        lexer.setColor(str_color, QsciLexerHTML.HTMLDoubleQuotedString)
        lexer.setColor(str_color, QsciLexerHTML.HTMLSingleQuotedString)

        lexer.setColor(QColor("#6A9955"), QsciLexerHTML.HTMLComment)

    def _style_css_lexer(self, lexer):
        lexer.setColor(QColor("#D7BA7D"), QsciLexerCSS.Tag)
        lexer.setColor(QColor("#9CDCFE"), QsciLexerCSS.CSS1Property)
        lexer.setColor(QColor("#9CDCFE"), QsciLexerCSS.CSS2Property)
        lexer.setColor(QColor("#9CDCFE"), QsciLexerCSS.CSS3Property)
        lexer.setColor(QColor("#569CD6"), QsciLexerCSS.Value)
        lexer.setColor(QColor("#6A9955"), QsciLexerCSS.Comment)

        str_color = QColor("#CE9178")
        lexer.setColor(str_color, QsciLexerCSS.DoubleQuotedString)
        lexer.setColor(str_color, QsciLexerCSS.SingleQuotedString)
