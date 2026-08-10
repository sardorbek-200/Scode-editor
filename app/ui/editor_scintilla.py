import os
from PyQt6.Qsci import (
    QsciScintilla,
    QsciLexerPython,
    QsciLexerJavaScript,
    QsciLexerHTML,
    QsciLexerCSS,
    QsciLexerCPP,
)
from PyQt6.QtGui import QColor, QFont


class ScodeScintillaEditor(QsciScintilla):
    """
    QScintilla asosidagi professional kod redaktori.
    Qator raqamlari, Dark Theme lexer ranglari, oq kvadratlarsiz Code Folding va Word Wrap.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._configure_editor()

    def _configure_editor(self):
        # 1. UTF-8 kodlashni yoqish va Word Wrap
        self.setUtf8(True)
        self.setWrapMode(QsciScintilla.WrapMode.WrapWord)

        # Defolt shrift (Consolas 11pt)
        self.default_font = QFont("Consolas", 11)
        self.default_font.setFixedPitch(True)
        self.setFont(self.default_font)

        # 2. Qator Raqamlari va Marginlar (#1e1e1e fon va #858585 matn)
        self.setMarginsBackgroundColor(QColor("#1e1e1e"))
        self.setMarginsForegroundColor(QColor("#858585"))

        # Margin 0: Qator raqamlari
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, " 000 ")
        self.setMarginLineNumbers(0, True)

        # Margin 1..4: Ortiqcha oq margin panellarini to'liq o'chirish (width = 0)
        for i in range(1, 5):
            self.setMarginWidth(i, 0)
            self.setMarginType(i, QsciScintilla.MarginType.SymbolMargin)
        self.setFoldMarginColors(QColor("#1e1e1e"), QColor("#1e1e1e"))

        # 3. Karetka (Kursor va Joriy qator ranglari)
        self.setCaretForegroundColor(QColor("#ffffff"))
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#2a2d2e"))
        self.setCaretWidth(2)

        # 4. Indentation & Tabs (Avto Tab tashlash)
        self.setAutoIndent(True)
        self.setIndentationWidth(4)
        self.setTabWidth(4)
        self.setIndentationsUseTabs(False)
        self.setBackspaceUnindents(True)

        # 5. Qavslarni moslash (Brace Matching)
        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.setMatchedBraceBackgroundColor(QColor("#3a3d41"))
        self.setMatchedBraceForegroundColor(QColor("#569CD6"))

        # 6. Matn tanlash ranglari
        self.setSelectionBackgroundColor(QColor("#264f78"))
        self.setSelectionForegroundColor(QColor("#ffffff"))

        # 7. Asosiy fon va matn ranglari (#1e1e1e va #d4d4d4)
        self.setPaper(QColor("#1e1e1e"))
        self.setColor(QColor("#d4d4d4"))

    def apply_settings(self, font_family: str = "Consolas", font_size: int = 11, tab_size: int = 4):
        """Sozlamalarga muvofiq shrift va tab o'lchamlarini yangilash"""
        self.default_font = QFont(font_family, font_size)
        self.default_font.setFixedPitch(True)
        self.setFont(self.default_font)

        self.setTabWidth(tab_size)
        self.setIndentationWidth(tab_size)

        lexer = self.lexer()
        if lexer:
            self._apply_dark_base(lexer)

    def set_lexer_for_file(self, file_path: str):
        """Fayl kengaytmasiga qarab mos QsciLexer va ranglarni biriktirish"""
        ext = os.path.splitext(file_path)[1].lower() if file_path else ""

        lexer = None
        if ext == ".py":
            lexer = QsciLexerPython(self)
            self._apply_dark_base(lexer)
            self._style_python_lexer(lexer)
        elif ext in [".js", ".jsx", ".ts", ".tsx", ".json"]:
            lexer = QsciLexerJavaScript(self)
            self._apply_dark_base(lexer)
            self._style_javascript_lexer(lexer)
        elif ext in [".html", ".htm", ".xml"]:
            lexer = QsciLexerHTML(self)
            self._apply_dark_base(lexer)
            self._style_html_lexer(lexer)
        elif ext in [".css", ".scss", ".less"]:
            lexer = QsciLexerCSS(self)
            self._apply_dark_base(lexer)
            self._style_css_lexer(lexer)
        elif ext in [".cpp", ".c", ".h", ".hpp", ".cs"]:
            lexer = QsciLexerCPP(self)
            self._apply_dark_base(lexer)

        if lexer:
            self.current_lexer = lexer
            self._current_lexer = lexer  # GC (Garbage Collector) xotiradan o'chirib yubormasligi uchun
            self.setLexer(lexer)
        else:
            self.current_lexer = None
            self._current_lexer = None
            self.setLexer(None)
            self.setFont(self.default_font)

        # setLexer() dan KEYIN margin ranglarini qorong'i (#1e1e1e) ga majburiy biriktirish
        self._enforce_dark_margins()

    def _enforce_dark_margins(self):
        """Margin va line number ranglarini dark (#1e1e1e va #858585) rejimida saqlash"""
        dark_bg = QColor("#1e1e1e")
        margin_fg = QColor("#858585")

        self.setMarginsBackgroundColor(dark_bg)
        self.setMarginsForegroundColor(margin_fg)
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, " 000 ")
        self.setMarginLineNumbers(0, True)

        for i in range(1, 5):
            self.setMarginWidth(i, 0)
            self.setMarginType(i, QsciScintilla.MarginType.SymbolMargin)

        self.setFoldMarginColors(dark_bg, dark_bg)
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#2a2d2e"))
        self.setCaretForegroundColor(QColor("#ffffff"))
        self.setPaper(dark_bg)
        self.setColor(QColor("#d4d4d4"))

        # Scintilla ichki style 33 (STYLE_LINENUMBER) fonini #1e1e1e ga bo'yash
        self.SendScintilla(QsciScintilla.SCI_STYLESETBACK, QsciScintilla.STYLE_LINENUMBER, dark_bg)
        self.SendScintilla(QsciScintilla.SCI_STYLESETFORE, QsciScintilla.STYLE_LINENUMBER, margin_fg)

    def _apply_dark_base(self, lexer):
        """Lexer uchun barcha fon va matn ranglarini #1e1e1e hamda #d4d4d4 ga sozlash"""
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
