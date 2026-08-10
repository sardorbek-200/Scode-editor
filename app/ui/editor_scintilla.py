import os
from PyQt6.Qsci import (
    QsciScintilla,
    QsciLexerPython,
    QsciLexerJavaScript,
    QsciLexerHTML,
    QsciLexerCSS,
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
        self.setMarginWidth(0, "00000")
        self.setMarginLineNumbers(0, True)

        # Margin 1: Chegara chizig'ini yo'qotish
        self.setMarginWidth(1, 0)

        # Margin 2: Code Folding (Kodni yig'ish [-] / [+]) va oq kvadratlarni yo'qotish
        self.setFolding(QsciScintilla.FoldStyle.BoxedTreeFoldStyle)
        self.setFoldMarginColors(QColor("#1e1e1e"), QColor("#1e1e1e"))
        self.setMarginMarkerMask(2, QsciScintilla.SC_MARGIN_SYMBOL)
        self.setMarkerBackgroundColor(QColor("#2d2d2d"), -1)
        self.setMarkerForegroundColor(QColor("#cccccc"), -1)

        # 3. Karetka (Kursor va Joriy qator ranglari)
        self.setCaretForegroundColor(QColor("#ffffff"))
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#282828"))
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

    def set_lexer_for_file(self, file_path: str):
        """Fayl kengaytmasiga qarab mos QsciLexer va ranglarni biriktirish"""
        ext = os.path.splitext(file_path)[1].lower() if file_path else ""

        if ext == ".py":
            lexer = QsciLexerPython(self)
            self._apply_dark_base(lexer)
            self._style_python_lexer(lexer)
            self.setLexer(lexer)
        elif ext in [".js", ".jsx", ".ts", ".tsx", ".json"]:
            lexer = QsciLexerJavaScript(self)
            self._apply_dark_base(lexer)
            self._style_javascript_lexer(lexer)
            self.setLexer(lexer)
        elif ext in [".html", ".htm", ".xml"]:
            lexer = QsciLexerHTML(self)
            self._apply_dark_base(lexer)
            self._style_html_lexer(lexer)
            self.setLexer(lexer)
        elif ext in [".css", ".scss", ".less"]:
            lexer = QsciLexerCSS(self)
            self._apply_dark_base(lexer)
            self._style_css_lexer(lexer)
            self.setLexer(lexer)
        else:
            self.setLexer(None)
            self.setFont(self.default_font)
            self.setColor(QColor("#d4d4d4"))
            self.setPaper(QColor("#1e1e1e"))

    def _apply_dark_base(self, lexer):
        """Lexer uchun barcha fon va matn ranglarini #1e1e1e hamda #d4d4d4 ga sozlash"""
        lexer.setDefaultFont(self.default_font)
        lexer.setFont(self.default_font)
        lexer.setDefaultPaper(QColor("#1e1e1e"))
        lexer.setPaper(QColor("#1e1e1e"))
        lexer.setDefaultColor(QColor("#d4d4d4"))
        lexer.setColor(QColor("#d4d4d4"))

        bg = QColor("#1e1e1e")
        for style in range(128):
            lexer.setPaper(bg, style)

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
        lexer.setColor(QColor("#9CDCFE"), QsciLexerCSS.Property)
        lexer.setColor(QColor("#569CD6"), QsciLexerCSS.Value)
        lexer.setColor(QColor("#6A9955"), QsciLexerCSS.Comment)

        str_color = QColor("#CE9178")
        lexer.setColor(str_color, QsciLexerCSS.DoubleQuotedString)
        lexer.setColor(str_color, QsciLexerCSS.SingleQuotedString)
