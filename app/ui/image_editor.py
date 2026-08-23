import os
import math
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QTransform, QKeySequence, QShortcut, QIcon
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QDialog,
    QFormLayout,
    QSpinBox,
    QCheckBox,
    QMessageBox,
    QToolBar,
    QFrame,
    QSizePolicy,
)
from PyQt6.QtSvg import QSvgRenderer

from app.utils.icon_manager import IconManager


class ImageResizeDialog(QDialog):
    """Rasm o'lchamini (Width x Height) o'zgartirish muloqot oynasi."""

    def __init__(self, current_width: int, current_height: int, parent=None):
        super().__init__(parent)
        self.orig_w = current_width
        self.orig_h = current_height
        self.aspect_ratio = current_width / max(1, current_height)

        self.setWindowTitle("Rasm hajmini o'zgartirish (Resize)")
        self.setFixedSize(340, 190)

        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #252526;
                color: #ffffff;
            }
            QLabel {
                color: #cccccc;
                font-size: 12px;
            }
            QSpinBox {
                background-color: #1c1c1c;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QSpinBox:focus {
                border: 1px solid #007acc;
            }
            QCheckBox {
                color: #cccccc;
                font-size: 12px;
            }
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton#cancelBtn {
                background-color: #3c3c3c;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        form = QFormLayout()
        form.setSpacing(10)

        self.spin_width = QSpinBox()
        self.spin_width.setRange(1, 10000)
        self.spin_width.setValue(self.orig_w)

        self.spin_height = QSpinBox()
        self.spin_height.setRange(1, 10000)
        self.spin_height.setValue(self.orig_h)

        self.check_ratio = QCheckBox("Proportsiyani saqlash (Aspect Ratio)")
        self.check_ratio.setChecked(True)

        self.spin_width.valueChanged.connect(self._on_width_changed)
        self.spin_height.valueChanged.connect(self._on_height_changed)

        form.addRow("Kenglik (Width px):", self.spin_width)
        form.addRow("Balandlik (Height px):", self.spin_height)
        form.addRow("", self.check_ratio)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Bekor qilish")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Qo'llash")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _on_width_changed(self, val: int):
        if self.check_ratio.isChecked() and self.spin_width.hasFocus():
            new_h = max(1, int(val / self.aspect_ratio))
            self.spin_height.blockSignals(True)
            self.spin_height.setValue(new_h)
            self.spin_height.blockSignals(False)

    def _on_height_changed(self, val: int):
        if self.check_ratio.isChecked() and self.spin_height.hasFocus():
            new_w = max(1, int(val * self.aspect_ratio))
            self.spin_width.blockSignals(True)
            self.spin_width.setValue(new_w)
            self.spin_width.blockSignals(False)

    def get_size(self) -> tuple[int, int]:
        return self.spin_width.value(), self.spin_height.value()


class ImageEditorWidget(QWidget):
    """
    O'rnatilgan Rasm Ko'rish va Mini-Tahrirlovchi (Built-in Image Viewer & Mini-Editor).
    Zoom In/Out, Rotate Left/Right, Resize va Ctrl+S orqali saqlash funksiyalari bilan.
    """

    image_saved = pyqtSignal(str)

    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = os.path.normpath(file_path) if file_path else ""
        self.is_modified = False

        self.original_pixmap = QPixmap()
        self.current_pixmap = QPixmap()
        self.scale_factor = 1.0
        self.rotation_angle = 0

        self._build_ui()
        if self.file_path and os.path.exists(self.file_path):
            self.load_image(self.file_path)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Yuqori ToolBar (Zoom, Rotate, Resize, Save)
        toolbar = QWidget()
        toolbar.setStyleSheet("""
            QWidget {
                background-color: #212121;
                border-bottom: 1px solid #2d2d2d;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #04395e;
                color: #ffffff;
                border-color: #007acc;
            }
            QLabel {
                color: #aaaaaa;
                font-size: 12px;
            }
        """)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(8, 4, 8, 4)
        tb_layout.setSpacing(6)

        # Zoom Out (-)
        btn_zoom_out = QPushButton(" 🔍- Zoom Out ")
        btn_zoom_out.setToolTip("Kichiklashtirish (Ctrl + Scroll Down)")
        btn_zoom_out.clicked.connect(self.zoom_out)
        tb_layout.addWidget(btn_zoom_out)

        # Zoom In (+)
        btn_zoom_in = QPushButton(" 🔍+ Zoom In ")
        btn_zoom_in.setToolTip("Kattalashtirish (Ctrl + Scroll Up)")
        btn_zoom_in.clicked.connect(self.zoom_in)
        tb_layout.addWidget(btn_zoom_in)

        # Reset Zoom (100%)
        btn_zoom_reset = QPushButton(" 100% ")
        btn_zoom_reset.setToolTip("Asl o'lchamga qaytarish")
        btn_zoom_reset.clicked.connect(self.reset_zoom)
        tb_layout.addWidget(btn_zoom_reset)

        tb_layout.addWidget(self._create_separator())

        # Rotate Left (↺)
        btn_rot_left = QPushButton(" ↺ Burish Chapga ")
        btn_rot_left.setToolTip("Rasmni 90° chapga burish")
        btn_rot_left.clicked.connect(lambda: self.rotate_image(-90))
        tb_layout.addWidget(btn_rot_left)

        # Rotate Right (↻)
        btn_rot_right = QPushButton(" ↻ Burish O'ngga ")
        btn_rot_right.setToolTip("Rasmni 90° o'ngga burish")
        btn_rot_right.clicked.connect(lambda: self.rotate_image(90))
        tb_layout.addWidget(btn_rot_right)

        tb_layout.addWidget(self._create_separator())

        # Resize (📐)
        btn_resize = QPushButton(" 📐 Resize (O'lcham) ")
        btn_resize.setToolTip("Rasm piksel o'lchamlarini o'zgartirish")
        btn_resize.clicked.connect(self.open_resize_dialog)
        tb_layout.addWidget(btn_resize)

        tb_layout.addStretch()

        # Save Button (💾)
        self.btn_save = QPushButton(" 💾 Saqlash (Ctrl+S) ")
        self.btn_save.setToolTip("O'zgarishlarni saqlash (Ctrl + S)")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)
        self.btn_save.clicked.connect(self.save_image)
        tb_layout.addWidget(self.btn_save)

        layout.addWidget(toolbar)

        # 2. Markaziy Scroll Area (Rasm ko'rsatgichi)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
        """)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: transparent;")
        self.scroll_area.setWidget(self.image_label)

        layout.addWidget(self.scroll_area, 1)

        # 3. Pastki Status Bar (Dimension, File Size, Zoom, Status)
        status_bar = QWidget()
        status_bar.setFixedHeight(26)
        status_bar.setStyleSheet("""
            QWidget {
                background-color: #007acc;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 11px;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        sb_layout = QHBoxLayout(status_bar)
        sb_layout.setContentsMargins(10, 2, 10, 2)
        sb_layout.setSpacing(14)

        self.lbl_dimensions = QLabel("O'lcham: 0 x 0 px")
        sb_layout.addWidget(self.lbl_dimensions)

        self.lbl_filesize = QLabel("Hajmi: 0 KB")
        sb_layout.addWidget(self.lbl_filesize)

        self.lbl_zoom = QLabel("Zoom: 100%")
        sb_layout.addWidget(self.lbl_zoom)

        sb_layout.addStretch()

        self.lbl_status = QLabel("Tayyor")
        sb_layout.addWidget(self.lbl_status)

        layout.addWidget(status_bar)

        # Ctrl + S saqlash shortcut
        shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut_save.activated.connect(self.save_image)

    def _create_separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #3c3c3c;")
        return line

    def load_image(self, file_path: str):
        """Faylni diskdan yuklash (PNG, JPG, SVG, ICO, BMP, WebP va hokazo)"""
        self.file_path = os.path.normpath(file_path)
        ext = os.path.splitext(self.file_path)[1].lower()

        if ext == ".svg":
            renderer = QSvgRenderer(self.file_path)
            size = renderer.defaultSize()
            w = max(100, size.width() if size.width() > 0 else 512)
            h = max(100, size.height() if size.height() > 0 else 512)
            img = QImage(w, h, QImage.Format.Format_ARGB32)
            img.fill(Qt.GlobalColor.transparent)
            from PyQt6.QtGui import QPainter
            painter = QPainter(img)
            renderer.render(painter)
            painter.end()
            self.original_pixmap = QPixmap.fromImage(img)
        else:
            self.original_pixmap = QPixmap(self.file_path)

        if self.original_pixmap.isNull():
            self.lbl_status.setText("Rasmni yuklashda xatolik yuz berdi!")
            return

        self.current_pixmap = QPixmap(self.original_pixmap)
        self.scale_factor = 1.0
        self.rotation_angle = 0
        self.is_modified = False

        self._update_display()
        self._update_status_info()

    def _update_display(self):
        """Rasmni joriy masshtab va burilish burchagi bo'yicha ekranga chiqarish"""
        if self.current_pixmap.isNull():
            return

        w = max(1, int(self.current_pixmap.width() * self.scale_factor))
        h = max(1, int(self.current_pixmap.height() * self.scale_factor))

        scaled_pixmap = self.current_pixmap.scaled(
            w, h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)
        self.lbl_zoom.setText(f"Zoom: {int(self.scale_factor * 100)}%")

    def _update_status_info(self):
        """Piksel o'lchamlari va fayl hajmini yangilash"""
        if not self.current_pixmap.isNull():
            w = self.current_pixmap.width()
            h = self.current_pixmap.height()
            self.lbl_dimensions.setText(f"O'lcham: {w} x {h} px")

        if self.file_path and os.path.exists(self.file_path):
            size_bytes = os.path.getsize(self.file_path)
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
            self.lbl_filesize.setText(f"Hajmi: {size_str}")

    def zoom_in(self):
        self.scale_factor = min(10.0, self.scale_factor * 1.25)
        self._update_display()

    def zoom_out(self):
        self.scale_factor = max(0.1, self.scale_factor / 1.25)
        self._update_display()

    def reset_zoom(self):
        self.scale_factor = 1.0
        self._update_display()

    def wheelEvent(self, event):
        """Ctrl + Wheel orqali rasm masshtabini o'zgartirish"""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            angle = event.angleDelta().y()
            if angle > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    def rotate_image(self, degrees: int):
        """Rasmni chapga yoki o'ngga 90 darajaga burish"""
        if self.current_pixmap.isNull():
            return

        transform = QTransform().rotate(degrees)
        self.current_pixmap = self.current_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        self.rotation_angle = (self.rotation_angle + degrees) % 360
        self.is_modified = True
        self.lbl_status.setText(f"Burildi ({degrees}°)")

        self._update_display()
        self._update_status_info()

    def open_resize_dialog(self):
        """Rasm pixel o'lchamlarini o'zgartirish muloqoti"""
        if self.current_pixmap.isNull():
            return

        dlg = ImageResizeDialog(self.current_pixmap.width(), self.current_pixmap.height(), self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_w, new_h = dlg.get_size()
            self.current_pixmap = self.current_pixmap.scaled(
                new_w, new_h,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.is_modified = True
            self.lbl_status.setText(f"O'lcham o'zgartirildi: {new_w}x{new_h} px")
            self._update_display()
            self._update_status_info()

    def save_image(self):
        """Tahrirlangan rasmni diskka saqlash (Ctrl + S)"""
        if not self.file_path or self.current_pixmap.isNull():
            return

        try:
            ext = os.path.splitext(self.file_path)[1].lower().lstrip('.')
            fmt = ext.upper()
            if fmt == "JPG":
                fmt = "JPEG"
            elif fmt in ("SVG", "ICO"):
                fmt = "PNG"

            saved = self.current_pixmap.save(self.file_path, fmt)
            if saved:
                self.is_modified = False
                self.lbl_status.setText("Saqlandi!")
                self._update_status_info()
                self.image_saved.emit(self.file_path)
            else:
                QMessageBox.warning(self, "Xatolik", f"Rasmni saqlashda xatolik yuz berdi: {self.file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Xatolik", f"Rasmni saqlashda xatolik: {e}")

    def isModified(self) -> bool:
        return self.is_modified

    def text(self) -> str:
        return ""
