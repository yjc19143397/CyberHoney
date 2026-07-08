import winreg

DARK_STYLE = """
    QWidget {
        background-color: #1e1e2e;
        color: #cdd6f4;
        selection-background-color: #45475a;
        selection-color: #cdd6f4;
    }
    QGroupBox {
        border: 1px solid #313244;
        border-radius: 8px;
        padding: 10px;
        font-weight: bold;
        background-color: #181825;
    }
    QPushButton {
        background-color: #45475a;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        color: #cdd6f4;
        min-width: 80px;
    }
    QPushButton:hover {
        background-color: #585b70;
    }
    QPushButton:pressed {
        background-color: #313244;
    }
    QPushButton:checked {
        background-color: #6c7086;
    }
    QPushButton:disabled {
        background-color: #313244;
        color: #6c7086;
    }
    QTextEdit {
        background-color: #181825;
        border: 1px solid #313244;
        border-radius: 4px;
        color: #cdd6f4;
        selection-background-color: #45475a;
    }
    QTableWidget {
        background-color: #181825;
        border: 1px solid #313244;
        border-radius: 4px;
        color: #cdd6f4;
        gridline-color: #313244;
    }
    QTableWidget::item {
        padding: 4px;
        color: #cdd6f4;
        border-bottom: 1px solid #313244;
    }
    QTableWidget::item:alternate {
        background-color: #1e1e2e;
    }
    QTableWidget::item:selected {
        background-color: #45475a;
        color: #cdd6f4;
    }
    QHeaderView::section {
        background-color: #313244;
        padding: 6px;
        color: #cdd6f4;
        border: none;
        border-right: 1px solid #45475a;
    }
    QHeaderView::section:last-child {
        border-right: none;
    }
    QProgressBar {
        width: 20px;
        height: 20px;
        border-radius: 10px;
        background-color: #313244;
        border: none;
    }
    QProgressBar::chunk {
        border-radius: 10px;
    }
    QLabel {
        color: #cdd6f4;
    }
    QComboBox {
        background-color: #45475a;
        border: 1px solid #313244;
        border-radius: 4px;
        padding: 4px;
        color: #cdd6f4;
        min-width: 120px;
    }
    QComboBox::drop-down {
        border-left: 1px solid #313244;
        width: 20px;
    }
    QComboBox::down-arrow {
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 4px solid #cdd6f4;
        margin-bottom: 2px;
    }
    QComboBox QAbstractItemView {
        background-color: #1e1e2e;
        border: 1px solid #313244;
        color: #cdd6f4;
        selection-background-color: #45475a;
    }
    QMenuBar {
        background-color: #313244;
        color: #cdd6f4;
        padding: 4px 0;
    }
    QMenuBar::item {
        padding: 4px 12px;
        border-radius: 4px;
    }
    QMenuBar::item:selected {
        background-color: #45475a;
    }
    QMenu {
        background-color: #313244;
        border: 1px solid #45475a;
        color: #cdd6f4;
        border-radius: 6px;
        padding: 4px;
    }
    QMenu::item {
        padding: 6px 24px;
        border-radius: 4px;
    }
    QMenu::item:selected {
        background-color: #45475a;
    }
    QMenu::separator {
        background-color: #45475a;
        height: 1px;
        margin: 4px 0;
    }
    QStatusBar {
        background-color: #313244;
        color: #cdd6f4;
        border-top: 1px solid #45475a;
    }
    QStatusBar::item {
        border: none;
    }
    QSplitter {
        background-color: #1e1e2e;
    }
    QSplitter::handle {
        background-color: #313244;
        width: 8px;
        height: 8px;
    }
    QSplitter::handle:hover {
        background-color: #45475a;
    }
    QTabWidget {
        background-color: #1e1e2e;
    }
    QTabWidget::pane {
        background-color: #181825;
        border: 1px solid #313244;
        border-radius: 0 0 4px 4px;
    }
    QTabBar {
        background-color: #1e1e2e;
    }
    QTabBar::tab {
        background-color: #313244;
        color: #a6adc8;
        padding: 8px 16px;
        border-radius: 4px 4px 0 0;
        margin-right: 2px;
        min-width: 80px;
    }
    QTabBar::tab:selected {
        background-color: #181825;
        color: #cdd6f4;
        border-bottom: 2px solid #89b4fa;
    }
    QTabBar::tab:hover {
        background-color: #45475a;
    }
    QLineEdit {
        background-color: #181825;
        border: 1px solid #313244;
        border-radius: 4px;
        padding: 6px 10px;
        color: #cdd6f4;
        selection-background-color: #45475a;
    }
    QLineEdit:focus {
        border-color: #89b4fa;
        outline: none;
    }
    QLineEdit::placeholder {
        color: #6c7086;
    }
    QCheckBox {
        color: #cdd6f4;
        spacing: 6px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 4px;
        background-color: #313244;
        border: 1px solid #45475a;
    }
    QCheckBox::indicator:checked {
        background-color: #89b4fa;
        border-color: #89b4fa;
    }
    QCheckBox::indicator:checked::unchecked {
        background-color: #313244;
    }
    QMessageBox {
        background-color: #1e1e2e;
        color: #cdd6f4;
    }
    QMessageBox QLabel {
        color: #cdd6f4;
    }
    QDialog {
        background-color: #1e1e2e;
    }
"""

LIGHT_STYLE = """
    QWidget {
        background-color: #eff1f5;
        color: #4c4f69;
        selection-background-color: #bcc0cc;
        selection-color: #4c4f69;
    }
    QGroupBox {
        border: 1px solid #dce0e8;
        border-radius: 8px;
        padding: 10px;
        font-weight: bold;
        background-color: #ffffff;
    }
    QPushButton {
        background-color: #bcc0cc;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        color: #4c4f69;
        min-width: 80px;
    }
    QPushButton:hover {
        background-color: #ccd0da;
    }
    QPushButton:pressed {
        background-color: #acb0be;
    }
    QPushButton:checked {
        background-color: #9ca0b0;
    }
    QPushButton:disabled {
        background-color: #dce0e8;
        color: #8c8fa3;
    }
    QTextEdit {
        background-color: #ffffff;
        border: 1px solid #dce0e8;
        border-radius: 4px;
        color: #4c4f69;
        selection-background-color: #bcc0cc;
    }
    QTableWidget {
        background-color: #ffffff;
        border: 1px solid #dce0e8;
        border-radius: 4px;
        color: #4c4f69;
        gridline-color: #dce0e8;
    }
    QTableWidget::item {
        padding: 4px;
        color: #4c4f69;
        border-bottom: 1px solid #e6e9ef;
    }
    QTableWidget::item:alternate {
        background-color: #e6e9ef;
    }
    QTableWidget::item:selected {
        background-color: #bcc0cc;
        color: #4c4f69;
    }
    QHeaderView::section {
        background-color: #bcc0cc;
        padding: 6px;
        color: #4c4f69;
        border: none;
        border-right: 1px solid #dce0e8;
    }
    QHeaderView::section:last-child {
        border-right: none;
    }
    QProgressBar {
        width: 20px;
        height: 20px;
        border-radius: 10px;
        background-color: #dce0e8;
        border: none;
    }
    QProgressBar::chunk {
        border-radius: 10px;
    }
    QLabel {
        color: #4c4f69;
    }
    QComboBox {
        background-color: #bcc0cc;
        border: 1px solid #dce0e8;
        border-radius: 4px;
        padding: 4px;
        color: #4c4f69;
        min-width: 120px;
    }
    QComboBox::drop-down {
        border-left: 1px solid #dce0e8;
        width: 20px;
    }
    QComboBox::down-arrow {
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 4px solid #4c4f69;
        margin-bottom: 2px;
    }
    QComboBox QAbstractItemView {
        background-color: #eff1f5;
        border: 1px solid #dce0e8;
        color: #4c4f69;
        selection-background-color: #bcc0cc;
    }
    QMenuBar {
        background-color: #bcc0cc;
        color: #4c4f69;
        padding: 4px 0;
    }
    QMenuBar::item {
        padding: 4px 12px;
        border-radius: 4px;
    }
    QMenuBar::item:selected {
        background-color: #ccd0da;
    }
    QMenu {
        background-color: #bcc0cc;
        border: 1px solid #dce0e8;
        color: #4c4f69;
        border-radius: 6px;
        padding: 4px;
    }
    QMenu::item {
        padding: 6px 24px;
        border-radius: 4px;
    }
    QMenu::item:selected {
        background-color: #ccd0da;
    }
    QMenu::separator {
        background-color: #dce0e8;
        height: 1px;
        margin: 4px 0;
    }
    QStatusBar {
        background-color: #bcc0cc;
        color: #4c4f69;
        border-top: 1px solid #dce0e8;
    }
    QStatusBar::item {
        border: none;
    }
    QSplitter {
        background-color: #eff1f5;
    }
    QSplitter::handle {
        background-color: #dce0e8;
        width: 8px;
        height: 8px;
    }
    QSplitter::handle:hover {
        background-color: #bcc0cc;
    }
    QTabWidget {
        background-color: #eff1f5;
    }
    QTabWidget::pane {
        background-color: #ffffff;
        border: 1px solid #dce0e8;
        border-radius: 0 0 4px 4px;
    }
    QTabBar {
        background-color: #eff1f5;
    }
    QTabBar::tab {
        background-color: #bcc0cc;
        color: #6c6f85;
        padding: 8px 16px;
        border-radius: 4px 4px 0 0;
        margin-right: 2px;
        min-width: 80px;
    }
    QTabBar::tab:selected {
        background-color: #ffffff;
        color: #4c4f69;
        border-bottom: 2px solid #1e66f5;
    }
    QTabBar::tab:hover {
        background-color: #ccd0da;
    }
    QLineEdit {
        background-color: #ffffff;
        border: 1px solid #dce0e8;
        border-radius: 4px;
        padding: 6px 10px;
        color: #4c4f69;
        selection-background-color: #bcc0cc;
    }
    QLineEdit:focus {
        border-color: #1e66f5;
        outline: none;
    }
    QLineEdit::placeholder {
        color: #8c8fa3;
    }
    QCheckBox {
        color: #4c4f69;
        spacing: 6px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 4px;
        background-color: #ffffff;
        border: 1px solid #dce0e8;
    }
    QCheckBox::indicator:checked {
        background-color: #1e66f5;
        border-color: #1e66f5;
    }
    QCheckBox::indicator:checked::unchecked {
        background-color: #ffffff;
    }
    QMessageBox {
        background-color: #eff1f5;
        color: #4c4f69;
    }
    QMessageBox QLabel {
        color: #4c4f69;
    }
    QDialog {
        background-color: #eff1f5;
    }
"""

DARK_LOG_COLORS = {
    'DEBUG': '#6c7086',
    'INFO': '#89b4fa',
    'WARNING': '#f9e2af',
    'ERROR': '#f38ba8',
    'CRITICAL': '#eba0ac'
}

LIGHT_LOG_COLORS = {
    'DEBUG': '#8c8fa3',
    'INFO': '#1e66f5',
    'WARNING': '#df8e1d',
    'ERROR': '#d20f39',
    'CRITICAL': '#e64553'
}

def detect_system_theme():
    try:
        reg_path = r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
            value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
            return 'light' if value == 1 else 'dark'
    except Exception:
        return 'dark'