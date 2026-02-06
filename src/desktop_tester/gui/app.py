"""QApplication setup and main entry point for the GUI."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication

from desktop_tester.constants import APP_NAME


def apply_dark_theme(app: QApplication) -> None:
    """Apply a dark theme to the application."""
    palette = QPalette()

    # Base colors
    dark = QColor(30, 30, 30)
    darker = QColor(20, 20, 20)
    mid = QColor(50, 50, 50)
    light = QColor(180, 180, 180)
    highlight = QColor(42, 130, 218)
    white = QColor(220, 220, 220)

    palette.setColor(QPalette.Window, dark)
    palette.setColor(QPalette.WindowText, white)
    palette.setColor(QPalette.Base, darker)
    palette.setColor(QPalette.AlternateBase, mid)
    palette.setColor(QPalette.ToolTipBase, mid)
    palette.setColor(QPalette.ToolTipText, white)
    palette.setColor(QPalette.Text, white)
    palette.setColor(QPalette.Button, mid)
    palette.setColor(QPalette.ButtonText, white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, highlight)
    palette.setColor(QPalette.Highlight, highlight)
    palette.setColor(QPalette.HighlightedText, Qt.black)
    palette.setColor(QPalette.PlaceholderText, light)

    # Disabled state
    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))

    app.setPalette(palette)

    # Stylesheet for additional polish
    app.setStyleSheet("""
        QToolTip {
            color: #ffffff;
            background-color: #2a2a2a;
            border: 1px solid #555;
            padding: 4px;
        }
        QMenuBar {
            background-color: #2a2a2a;
            border-bottom: 1px solid #444;
        }
        QMenuBar::item:selected {
            background-color: #3a3a3a;
        }
        QMenu {
            background-color: #2a2a2a;
            border: 1px solid #444;
        }
        QMenu::item:selected {
            background-color: #2a82da;
        }
        QToolBar {
            background-color: #2a2a2a;
            border-bottom: 1px solid #444;
            spacing: 6px;
            padding: 4px;
        }
        QStatusBar {
            background-color: #1e1e1e;
            border-top: 1px solid #444;
        }
        QSplitter::handle {
            background-color: #444;
        }
        QTreeView, QListView {
            background-color: #1a1a1a;
            border: 1px solid #333;
            outline: none;
        }
        QTreeView::item:selected, QListView::item:selected {
            background-color: #2a82da;
        }
        QTreeView::item:hover, QListView::item:hover {
            background-color: #333;
        }
        QTabWidget::pane {
            border: 1px solid #444;
            background-color: #1e1e1e;
        }
        QTabBar::tab {
            background-color: #2a2a2a;
            color: #ccc;
            padding: 8px 16px;
            border: 1px solid #444;
            border-bottom: none;
        }
        QTabBar::tab:selected {
            background-color: #1e1e1e;
            color: #fff;
        }
        QPushButton {
            background-color: #3a3a3a;
            border: 1px solid #555;
            padding: 6px 16px;
            border-radius: 3px;
            color: #ddd;
        }
        QPushButton:hover {
            background-color: #4a4a4a;
        }
        QPushButton:pressed {
            background-color: #2a82da;
        }
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: #2a2a2a;
            border: 1px solid #555;
            padding: 4px 8px;
            border-radius: 3px;
            color: #ddd;
        }
        QLineEdit:focus, QComboBox:focus {
            border-color: #2a82da;
        }
        QGroupBox {
            border: 1px solid #444;
            border-radius: 4px;
            margin-top: 12px;
            padding-top: 16px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
        }
        QScrollBar:vertical {
            background-color: #1a1a1a;
            width: 12px;
        }
        QScrollBar::handle:vertical {
            background-color: #555;
            border-radius: 4px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #777;
        }
    """)


def run_app() -> None:
    """Launch the DesktopTester GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("DesktopTester")

    apply_dark_theme(app)

    from desktop_tester.gui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())
