import os
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression


class CodeHighlighter(QSyntaxHighlighter):
    """
    Python, JavaScript, HTML va CSS fayllari uchun VS Code Dark Theme ranglarida
    sintaksis rang berish klassi.
    """

    def __init__(self, document=None, file_extension=""):
        super().__init__(document)
        self.rules = []
        self.comment_start_expression = None
        self.comment_end_expression = None
        self._setup_formats()
        self.set_language(file_extension)

    def _setup_formats(self):
        # 1. Kalit so'zlar (Keywords): Siyohrang / Moviy (#569CD6)
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#569CD6"))
        self.keyword_format.setFontWeight(QFont.Weight.Bold)

        # 2. Satrlar (Strings): Jigarrang / Zardob (#CE9178)
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#CE9178"))

        # 3. Izohlar (Comments): Yashil (#6A9955)
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#6A9955"))
        self.comment_format.setFontItalic(True)

        # 4. Raqamlar (Numbers): Och yashil (#B5CEA8)
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor("#B5CEA8"))

        # 5. Qo'shimcha formatlar (Funksiyalar, HTML atributlar va taglar)
        self.function_format = QTextCharFormat()
        self.function_format.setForeground(QColor("#DCDCAA"))

        self.html_tag_format = QTextCharFormat()
        self.html_tag_format.setForeground(QColor("#569CD6"))

        self.html_attr_format = QTextCharFormat()
        self.html_attr_format.setForeground(QColor("#9CDCFE"))

    def set_language(self, extension: str):
        """Fayl kengaytmasiga qarab ranglash qoidalarini o'rnatish"""
        ext = extension.lower().strip()
        if ext and not ext.startswith("."):
            ext = "." + ext

        self.rules = []
        self.comment_start_expression = None
        self.comment_end_expression = None

        if ext == ".py":
            self._set_python_rules()
        elif ext in [".js", ".jsx", ".ts", ".tsx", ".json"]:
            self._set_javascript_rules()
        elif ext in [".html", ".htm", ".xml"]:
            self._set_html_rules()
        elif ext in [".css", ".scss", ".less"]:
            self._set_css_rules()

        self.rehighlight()

    def _set_python_rules(self):
        # Python kalit so'zlari (#569CD6)
        python_keywords = [
            r"\band\b", r"\bas\b", r"\bassert\b", r"\basync\b", r"\bawait\b",
            r"\bbreak\b", r"\bclass\b", r"\bcontinue\b", r"\bdef\b", r"\bdel\b",
            r"\belif\b", r"\belse\b", r"\bexcept\b", r"\bFalse\b", r"\bfinally\b",
            r"\bfor\b", r"\bfrom\b", r"\bglobal\b", r"\bif\b", r"\bimport\b",
            r"\bin\b", r"\bis\b", r"\blambda\b", r"\bNone\b", r"\bnonlocal\b",
            r"\bnot\b", r"\bor\b", r"\bpass\b", r"\braise\b", r"\breturn\b",
            r"\bTrue\b", r"\btry\b", r"\bwhile\b", r"\bwith\b", r"\byield\b",
            r"\bself\b"
        ]
        for kw in python_keywords:
            self.rules.append((QRegularExpression(kw), self.keyword_format))

        # Raqamlar (#B5CEA8)
        self.rules.append((QRegularExpression(r"\b\d+(\.\d+)?\b"), self.number_format))

        # Funksiya nomlari
        self.rules.append((QRegularExpression(r"\bdef\s+([A-Za-z_][A-Za-z0-9_]*)"), self.function_format))

        # Satrlar (#CE9178)
        self.rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), self.string_format))
        self.rules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), self.string_format))
        self.rules.append((QRegularExpression(r'"""[\s\S]*?"""'), self.string_format))

        # Bir qatorlik izohlar (#6A9955)
        self.rules.append((QRegularExpression(r"#[^\n]*"), self.comment_format))

    def _set_javascript_rules(self):
        # JS kalit so'zlari (#569CD6)
        js_keywords = [
            r"\basync\b", r"\bawait\b", r"\bbreak\b", r"\bcase\b", r"\bcatch\b",
            r"\bclass\b", r"\bconst\b", r"\bcontinue\b", r"\bdebugger\b", r"\bdefault\b",
            r"\bdelete\b", r"\bdo\b", r"\belse\b", r"\bexport\b", r"\bextends\b",
            r"\bfalse\b", r"\bfinally\b", r"\bfor\b", r"\bfunction\b", r"\bif\b",
            r"\bimport\b", r"\bin\b", r"\binstanceof\b", r"\blet\b", r"\bnew\b",
            r"\bnull\b", r"\breturn\b", r"\bsuper\b", r"\bswitch\b", r"\bthis\b",
            r"\bthrow\b", r"\btrue\b", r"\btry\b", r"\btypeof\b", r"\bvar\b",
            r"\bvoid\b", r"\bwhile\b", r"\bwith\b", r"\byield\b", r"\bundefined\b"
        ]
        for kw in js_keywords:
            self.rules.append((QRegularExpression(kw), self.keyword_format))

        # Raqamlar (#B5CEA8)
        self.rules.append((QRegularExpression(r"\b\d+(\.\d+)?\b"), self.number_format))

        # Satrlar (#CE9178)
        self.rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), self.string_format))
        self.rules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), self.string_format))
        self.rules.append((QRegularExpression(r"`[^`\\]*(\\.[^`\\]*)*`"), self.string_format))

        # Bir qatorlik izohlar (#6A9955)
        self.rules.append((QRegularExpression(r"//[^\n]*"), self.comment_format))

        # Ko'p qatorlik izohlar (/* ... */)
        self.comment_start_expression = QRegularExpression(r"/\*")
        self.comment_end_expression = QRegularExpression(r"\*/")

    def _set_html_rules(self):
        # HTML Taglar (#569CD6)
        self.rules.append((QRegularExpression(r"</?[a-zA-Z0-9_-]+(?:\s*[^>]*>|>)?"), self.html_tag_format))

        # HTML atributlar (#9CDCFE)
        self.rules.append((QRegularExpression(r"\b[a-zA-Z0-9_-]+(?=\=)"), self.html_attr_format))

        # Satrlar (#CE9178)
        self.rules.append((QRegularExpression(r'"[^"]*"'), self.string_format))
        self.rules.append((QRegularExpression(r"'[^']*'"), self.string_format))

        # Raqamlar (#B5CEA8)
        self.rules.append((QRegularExpression(r"\b\d+(\.\d+)?\b"), self.number_format))

        # HTML izohlar (<!-- ... -->)
        self.comment_start_expression = QRegularExpression(r"<!--")
        self.comment_end_expression = QRegularExpression(r"-->")

    def _set_css_rules(self):
        # CSS kalit so'zlar / qiymatlar (#569CD6)
        css_keywords = [
            r"\bimportant\b", r"\bauto\b", r"\bnone\b", r"\binherit\b",
            r"\bblock\b", r"\bflex\b", r"\bgrid\b", r"\binline\b",
            r"\brelative\b", r"\babsolute\b", r"\bfixed\b", r"\bcenter\b",
            r"\bold\b", r"\bnormal\b", r"\bsolid\b", r"\bdashed\b"
        ]
        for kw in css_keywords:
            self.rules.append((QRegularExpression(kw), self.keyword_format))

        # CSS Xossalari (#9CDCFE)
        self.rules.append((QRegularExpression(r"\b[a-zA-Z-]+\s*(?=\:)"), self.html_attr_format))

        # Raqamlar va birliklar (#B5CEA8)
        self.rules.append((QRegularExpression(r"\b\d+(\.\d+)?(px|em|rem|%|vh|vw|pt|s|ms)?\b"), self.number_format))

        # Satrlar (#CE9178)
        self.rules.append((QRegularExpression(r'"[^"]*"'), self.string_format))
        self.rules.append((QRegularExpression(r"'[^']*'"), self.string_format))

        # CSS izohlar (/* ... */)
        self.comment_start_expression = QRegularExpression(r"/\*")
        self.comment_end_expression = QRegularExpression(r"\*/")

    def highlightBlock(self, text: str):
        # Bir qatorlik qoidalar bo'yicha ranglash
        for pattern, fmt in self.rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

        # Ko'p qatorlik izohlar nazorati (Block comments)
        if not self.comment_start_expression or not self.comment_end_expression:
            return

        self.setCurrentBlockState(0)
        start_index = 0
        if self.previousBlockState() != 1:
            match = self.comment_start_expression.match(text)
            start_index = match.capturedStart() if match.hasMatch() else -1

        while start_index >= 0:
            end_match = self.comment_end_expression.match(text, start_index)
            end_index = end_match.capturedStart() if end_match.hasMatch() else -1
            comment_length = 0

            if end_index == -1:
                self.setCurrentBlockState(1)
                comment_length = len(text) - start_index
            else:
                comment_length = end_index - start_index + end_match.capturedLength()

            self.setFormat(start_index, comment_length, self.comment_format)

            if end_index == -1:
                break

            start_match = self.comment_start_expression.match(text, start_index + comment_length)
            start_index = start_match.capturedStart() if start_match.hasMatch() else -1
