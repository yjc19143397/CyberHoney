import sys
import logging
import traceback
import threading
import os
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QStatusBar,
    QSplitter, QGroupBox, QProgressBar, QGridLayout, QComboBox,
    QMenuBar, QMenu, QMessageBox, QLabel, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QTextBrowser,
    QFileDialog
)
from PyQt6.QtCore import Qt, QObject, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QActionGroup, QIcon
from .theme import DARK_STYLE, LIGHT_STYLE, DARK_LOG_COLORS, LIGHT_LOG_COLORS, detect_system_theme
from .auth import is_admin, run_as_admin, set_run_as_admin_permanently, check_run_as_admin_setting, remove_run_as_admin_setting


DEFAULT_CACHE_DIR = os.path.join(os.path.expanduser('~'), '.cyberhoney', 'cache')
DEFAULT_LOG_DIR = os.path.join(os.path.expanduser('~'), '.cyberhoney', 'logs')
CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.cyberhoney', 'config.json')


def load_settings():
    try:
        if os.path.exists(CONFIG_FILE):
            import json
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_settings(settings):
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        import json
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def get_cache_dir():
    settings = load_settings()
    cache_dir = settings.get('cache_dir', DEFAULT_CACHE_DIR)
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def get_log_dir():
    settings = load_settings()
    log_dir = settings.get('log_dir', DEFAULT_LOG_DIR)
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def clear_cache():
    try:
        cache_dir = get_cache_dir()
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            os.makedirs(cache_dir, exist_ok=True)
        return True
    except Exception:
        return False


THEME_CACHE = None


def get_system_theme():
    global THEME_CACHE
    if THEME_CACHE is None:
        THEME_CACHE = detect_system_theme()
    return THEME_CACHE


class LogSignalEmitter(QObject):
    log_received = pyqtSignal(str)


class QtLogHandler(logging.Handler):
    def __init__(self, emitter):
        super().__init__()
        self.emitter = emitter
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        msg = self.format(record)
        self.emitter.log_received.emit(msg)


class AboutDialog(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('关于')
        self.setIcon(QMessageBox.Icon.Information)
        about_text = (
            '<h2>CyberHoney 蜜罐管理系统</h2>'
            '<p>版本: 1.0.3</p>'
            '<p>一款多服务蜜罐系统，用于网络安全监控和攻击检测。</p>'
            '<p></p>'
            '<p><strong>支持的服务:</strong></p>'
            '<ul>'
            '<li>SSH (端口 2222)</li>'
            '<li>FTP (端口 2121)</li>'
            '<li>HTTP (端口 8080)</li>'
            '<li>TCP (端口 1234)</li>'
            '<li>UDP (端口 5678)</li>'
            '<li>Telnet (端口 2323)</li>'
            '<li>API (端口 5000)</li>'
            '</ul>'
            '<p></p>'
            '<p><strong>功能特性:</strong></p>'
            '<ul>'
            '<li>实时日志监控</li>'
            '<li>攻击记录与分析</li>'
            '<li>连接状态追踪</li>'
            '<li>IP速率限制与封禁</li>'
            '<li>深色/浅色主题切换</li>'
            '<li>管理员权限管理</li>'
            '</ul>'
            '<p></p>'
            '<p>许可证: MIT License</p>'
        )
        self.setText(about_text)
        self.setStandardButtons(QMessageBox.StandardButton.Ok)


class ConfigDialog(QMessageBox):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle('配置信息')
        self.setIcon(QMessageBox.Icon.Information)
        
        config_text = '<h2>当前配置</h2>'
        config_text += '<p><strong>蜜罐名称:</strong> ' + str(config.get('honeypot.name', 'CyberHoney')) + '</p>'
        config_text += '<p><strong>监听地址:</strong> ' + str(config.get('honeypot.host', '0.0.0.0')) + '</p>'
        config_text += '<p><strong>日志级别:</strong> ' + str(config.get('honeypot.log_level', 'INFO')) + '</p>'
        config_text += '<p><strong>数据存储:</strong> ' + str(config.get('database.path', 'honeypot.db')) + '</p>'
        
        config_text += '<p></p><p><strong>服务配置:</strong></p>'
        services = ['ssh', 'ftp', 'http', 'tcp', 'udp', 'telnet', 'api']
        for service in services:
            enabled = config.get(f'services.{service}.enabled', True)
            port = config.get(f'services.{service}.port', 0)
            config_text += f'<p>{service.upper()}: {"启用" if enabled else "禁用"} (端口 {port})</p>'
        
        self.setText(config_text)
        self.setStandardButtons(QMessageBox.StandardButton.Ok)


class ErrorDialog(QMessageBox):
    def __init__(self, title, message, traceback_text=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setIcon(QMessageBox.Icon.Critical)
        self.setText(message)
        
        if traceback_text:
            self.setDetailedText(traceback_text)
        
        self.setStandardButtons(QMessageBox.StandardButton.Ok)


class SettingsDialog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('设置')
        self.setMinimumSize(500, 300)
        
        layout = QVBoxLayout(self)
        
        cache_group = QGroupBox('缓存路径')
        cache_layout = QHBoxLayout(cache_group)
        self.cache_path_edit = QLineEdit(get_cache_dir())
        self.cache_path_edit.setReadOnly(True)
        cache_browse_btn = QPushButton('浏览...')
        cache_browse_btn.clicked.connect(self._browse_cache_path)
        cache_layout.addWidget(self.cache_path_edit)
        cache_layout.addWidget(cache_browse_btn)
        layout.addWidget(cache_group)
        
        log_group = QGroupBox('日志保存路径')
        log_layout = QHBoxLayout(log_group)
        self.log_path_edit = QLineEdit(get_log_dir())
        self.log_path_edit.setReadOnly(True)
        log_browse_btn = QPushButton('浏览...')
        log_browse_btn.clicked.connect(self._browse_log_path)
        log_layout.addWidget(self.log_path_edit)
        log_layout.addWidget(log_browse_btn)
        layout.addWidget(log_group)
        
        button_layout = QHBoxLayout()
        save_btn = QPushButton('保存')
        save_btn.clicked.connect(self._save_settings)
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.close)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
    
    def _browse_cache_path(self):
        path = QFileDialog.getExistingDirectory(self, '选择缓存目录', self.cache_path_edit.text())
        if path:
            self.cache_path_edit.setText(path)
    
    def _browse_log_path(self):
        path = QFileDialog.getExistingDirectory(self, '选择日志目录', self.log_path_edit.text())
        if path:
            self.log_path_edit.setText(path)
    
    def _save_settings(self):
        settings = {
            'cache_dir': self.cache_path_edit.text(),
            'log_dir': self.log_path_edit.text()
        }
        if save_settings(settings):
            QMessageBox.information(self, '成功', '设置已保存')
            self.close()
        else:
            QMessageBox.warning(self, '失败', '保存设置失败')


class MainWindow(QMainWindow):
    def __init__(self, config_path='config.yaml'):
        super().__init__()
        self.config_path = config_path
        self.honeypot = None
        self.current_theme = 'system'
        self.log_colors = DARK_LOG_COLORS
        self.log_max_lines = 10000
        self._lazy_initialized = False
        self._data_timer = None
        self._service_lock = threading.Lock()
        self._log_cache = []
        self._log_cache_max_size = 50000
        self._init_fast_ui()

    def _init_fast_ui(self):
        self.setWindowTitle('CyberHoney - 蜜罐管理系统')
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        self._create_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(3)

        left_panel = self._create_left_panel()
        right_panel = self._create_right_panel_stub()

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_admin_status()

        self._apply_theme(self.current_theme)

        QTimer.singleShot(0, self._lazy_init)

    def _lazy_init(self):
        if self._lazy_initialized:
            return
        self._lazy_initialized = True

        self._init_log_handler()

        if hasattr(self, '_right_panel_stub'):
            self._replace_right_panel_stub()

        self._init_honeypot()
        self._init_data_timer()

    def _init_log_handler(self):
        self._log_emitter = LogSignalEmitter()
        self._log_emitter.log_received.connect(self.update_log)
        self._log_handler = QtLogHandler(self._log_emitter)
        logger = logging.getLogger('honeypot')
        logger.addHandler(self._log_handler)
        logger.setLevel(logging.DEBUG)

    def _init_honeypot(self):
        try:
            from honeypot.core.honeypot import Honeypot
            self.honeypot = Honeypot(self.config_path)
            self.log_text.append('蜜罐系统初始化完成')
            self.log_text.append(f'已加载服务: {list(self.honeypot.service_manager.services.keys())}')
            self.log_text.append(f'配置文件: {self.config_path}')
        except Exception as e:
            error_msg = f'蜜罐初始化失败: {type(e).__name__}: {e}'
            self.log_text.append(error_msg)
            self.log_text.append('详细错误信息:')
            self.log_text.append(traceback.format_exc())
            ErrorDialog('初始化失败', error_msg, traceback.format_exc(), self).exec()

    def _init_data_timer(self):
        self._data_timer = QTimer(self)
        self._data_timer.timeout.connect(self._refresh_data)
        self._data_timer.start(3000)

    def _refresh_data(self):
        if self.honeypot and self.honeypot.database:
            self._refresh_attacks()
            self._refresh_connections()
            self._refresh_stats()

    def _refresh_attacks(self):
        try:
            attacks = self.honeypot.database.get_attacks(limit=50)
            self.attacks_table.setRowCount(0)
            
            for i, attack in enumerate(attacks):
                self.attacks_table.insertRow(i)
                self.attacks_table.setItem(i, 0, QTableWidgetItem(str(attack.get('id', ''))))
                self.attacks_table.setItem(i, 1, QTableWidgetItem(attack.get('ip', '')))
                self.attacks_table.setItem(i, 2, QTableWidgetItem(attack.get('service', '')))
                self.attacks_table.setItem(i, 3, QTableWidgetItem(attack.get('username', '')))
                self.attacks_table.setItem(i, 4, QTableWidgetItem(attack.get('password', '')))
                self.attacks_table.setItem(i, 5, QTableWidgetItem(str(attack.get('timestamp', ''))))
        except Exception as e:
            self.log_text.append(f'刷新攻击记录失败: {e}')

    def _refresh_connections(self):
        try:
            connections = self.honeypot.database.get_connections(limit=50)
            self.connections_table.setRowCount(0)
            
            for i, conn in enumerate(connections):
                self.connections_table.insertRow(i)
                self.connections_table.setItem(i, 0, QTableWidgetItem(str(conn.get('id', ''))))
                self.connections_table.setItem(i, 1, QTableWidgetItem(conn.get('ip', '')))
                self.connections_table.setItem(i, 2, QTableWidgetItem(str(conn.get('port', ''))))
                self.connections_table.setItem(i, 3, QTableWidgetItem(conn.get('service', '')))
                self.connections_table.setItem(i, 4, QTableWidgetItem(conn.get('status', '')))
        except Exception as e:
            self.log_text.append(f'刷新连接状态失败: {e}')

    def _refresh_stats(self):
        try:
            stats = self.honeypot.database.get_stats()
            
            if 'total_attacks' in stats:
                self.stat_labels['攻击总数'].setText(str(stats['total_attacks']))
            if 'active_connections' in stats:
                self.stat_labels['活跃连接'].setText(str(stats['active_connections']))
            if 'blocked_ips' in stats:
                self.stat_labels['封禁IP'].setText(str(stats['blocked_ips']))
            if 'total_connections' in stats:
                self.stat_labels['连接总数'].setText(str(stats['total_connections']))
        except Exception as e:
            self.log_text.append(f'刷新统计信息失败: {e}')

    def _create_right_panel_stub(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        self._stub_label = QLabel('加载中...')
        self._stub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stub_label.setStyleSheet('font-size: 18px;')
        layout.addWidget(self._stub_label)
        self._right_panel_stub = panel
        return panel

    def _replace_right_panel_stub(self):
        if not hasattr(self, '_right_panel_stub'):
            return

        splitter = self.centralWidget().layout().itemAt(0).widget()
        if splitter is None:
            return

        index = splitter.indexOf(self._right_panel_stub)
        if index == -1:
            return

        self._right_panel_stub.setParent(None)

        right_panel = self._create_right_panel()
        splitter.insertWidget(index, right_panel)
        splitter.setStretchFactor(index, 3)

        self._right_panel_stub = None
        self._stub_label = None

    def _update_admin_status(self):
        if is_admin():
            self.status_bar.showMessage('已以管理员身份运行')
        else:
            self.status_bar.showMessage('未以管理员身份运行')

    def _create_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        service_group = QGroupBox('服务管理')
        service_layout = QGridLayout(service_group)
        service_layout.setSpacing(8)

        header_label = QLabel('<strong>服务</strong>')
        status_header = QLabel('<strong>状态</strong>')
        action_header = QLabel('<strong>操作</strong>')
        service_layout.addWidget(header_label, 0, 0)
        service_layout.addWidget(status_header, 0, 1)
        service_layout.addWidget(action_header, 0, 2)

        services = [
            ('SSH', '2222', False),
            ('FTP', '2121', False),
            ('HTTP', '8080', False),
            ('TCP', '1234', False),
            ('UDP', '5678', False),
            ('Telnet', '2323', False),
            ('API', '5000', False)
        ]

        self.service_buttons = {}

        for i, (name, port, status) in enumerate(services):
            row = i + 1
            label = QLabel(f'<strong>{name}</strong> ({port})')
            
            status_indicator = QProgressBar()
            status_indicator.setMaximum(1)
            status_indicator.setValue(0)
            status_indicator.setFixedWidth(60)
            status_indicator.setStyleSheet('QProgressBar::chunk { background-color: #dc3545; }')

            button = QPushButton('启动')
            button.setFixedWidth(80)
            button.clicked.connect(lambda checked, n=name: self._toggle_service(n))

            service_layout.addWidget(label, row, 0)
            service_layout.addWidget(status_indicator, row, 1)
            service_layout.addWidget(button, row, 2)

            self.service_buttons[name] = {
                'label': label,
                'indicator': status_indicator,
                'button': button,
                'status': False
            }

        layout.addWidget(service_group)

        button_layout = QHBoxLayout()
        
        start_all_btn = QPushButton('全部启动')
        start_all_btn.clicked.connect(self._start_all)
        button_layout.addWidget(start_all_btn)

        stop_all_btn = QPushButton('全部停止')
        stop_all_btn.clicked.connect(self._stop_all)
        button_layout.addWidget(stop_all_btn)

        layout.addLayout(button_layout)
        layout.addStretch()

        return panel

    def _create_right_panel(self):
        tab_widget = QTabWidget()

        logs_tab = self._create_logs_tab()
        attacks_tab = self._create_attacks_tab()
        connections_tab = self._create_connections_tab()
        stats_tab = self._create_stats_tab()
        config_tab = self._create_config_tab()

        tab_widget.addTab(logs_tab, '日志')
        tab_widget.addTab(attacks_tab, '攻击记录')
        tab_widget.addTab(connections_tab, '连接状态')
        tab_widget.addTab(stats_tab, '统计信息')
        tab_widget.addTab(config_tab, '配置')

        return tab_widget

    def _create_logs_tab(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        toolbar = QHBoxLayout()
        
        self.log_level_filter = QComboBox()
        self.log_level_filter.addItems(['全部', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
        self.log_level_filter.currentTextChanged.connect(self._filter_logs)
        
        toolbar.addWidget(QLabel('级别过滤:'))
        toolbar.addWidget(self.log_level_filter)
        toolbar.addStretch()

        clear_btn = QPushButton('清空日志')
        clear_btn.clicked.connect(self._clear_logs)
        toolbar.addWidget(clear_btn)

        save_btn = QPushButton('保存日志')
        save_btn.clicked.connect(self._save_logs)
        toolbar.addWidget(save_btn)

        self.auto_scroll_btn = QPushButton('自动滚动')
        self.auto_scroll_btn.setCheckable(True)
        self.auto_scroll_btn.setChecked(True)
        toolbar.addWidget(self.auto_scroll_btn)

        layout.addLayout(toolbar)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet('font-family: Consolas, monospace; font-size: 10pt;')
        layout.addWidget(self.log_text)

        return panel

    def _create_attacks_tab(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        toolbar = QHBoxLayout()
        refresh_btn = QPushButton('刷新')
        refresh_btn.clicked.connect(self._refresh_attacks)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.attacks_table = QTableWidget()
        self.attacks_table.setColumnCount(6)
        self.attacks_table.setHorizontalHeaderLabels([
            '编号', '攻击IP', '服务类型', '用户名', '密码', '时间戳'
        ])
        self.attacks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.attacks_table.setAlternatingRowColors(True)
        layout.addWidget(self.attacks_table)

        return panel

    def _create_connections_tab(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        toolbar = QHBoxLayout()
        refresh_btn = QPushButton('刷新')
        refresh_btn.clicked.connect(self._refresh_connections)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.connections_table = QTableWidget()
        self.connections_table.setColumnCount(5)
        self.connections_table.setHorizontalHeaderLabels([
            '编号', 'IP地址', '端口', '服务', '状态'
        ])
        self.connections_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.connections_table.setAlternatingRowColors(True)
        layout.addWidget(self.connections_table)

        return panel

    def _create_stats_tab(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        toolbar = QHBoxLayout()
        refresh_btn = QPushButton('刷新')
        refresh_btn.clicked.connect(self._refresh_stats)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(20)

        stats = [
            ('攻击总数', '0'),
            ('活跃连接', '0'),
            ('封禁IP', '0'),
            ('连接总数', '0')
        ]

        self.stat_labels = {}

        for i, (label, value) in enumerate(stats):
            group = QGroupBox(label)
            group_layout = QVBoxLayout(group)
            
            val = QLabel(value)
            val.setStyleSheet('font-weight: bold; font-size: 24px; text-align: center;')
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            group_layout.addWidget(val)
            stats_grid.addWidget(group, i // 2, i % 2)
            self.stat_labels[label] = val

        layout.addLayout(stats_grid)
        layout.addStretch()

        return panel

    def _create_config_tab(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        toolbar = QHBoxLayout()
        refresh_btn = QPushButton('查看配置')
        refresh_btn.clicked.connect(self._show_config)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        info_group = QGroupBox('服务端口配置')
        info_layout = QGridLayout(info_group)

        services = [
            ('SSH', '2222', 'TCP'),
            ('FTP', '2121', 'TCP'),
            ('HTTP', '8080', 'TCP'),
            ('TCP', '1234', 'TCP'),
            ('UDP', '5678', 'UDP'),
            ('Telnet', '2323', 'TCP'),
            ('API', '5000', 'TCP')
        ]

        header_row = 0
        info_layout.addWidget(QLabel('<strong>服务</strong>'), header_row, 0)
        info_layout.addWidget(QLabel('<strong>端口</strong>'), header_row, 1)
        info_layout.addWidget(QLabel('<strong>协议</strong>'), header_row, 2)
        info_layout.addWidget(QLabel('<strong>状态</strong>'), header_row, 3)

        for i, (name, port, protocol) in enumerate(services):
            row = i + 1
            info_layout.addWidget(QLabel(name), row, 0)
            info_layout.addWidget(QLabel(port), row, 1)
            info_layout.addWidget(QLabel(protocol), row, 2)
            
            status_label = QLabel('未运行')
            status_label.setStyleSheet('color: #dc3545;')
            info_layout.addWidget(status_label, row, 3)
            self.service_buttons[name]['config_status'] = status_label

        layout.addWidget(info_group)

        tips_group = QGroupBox('使用提示')
        tips_layout = QVBoxLayout(tips_group)
        
        tips_text = QLabel()
        tips_text.setWordWrap(True)
        tips_text.setText(
            '1. 点击左侧"启动"按钮启动对应服务\n'
            '2. 服务启动后会在对应端口监听连接\n'
            '3. 所有连接和攻击都会被记录到数据库\n'
            '4. 需要管理员权限才能监听低于1024的端口\n'
            '5. 建议以管理员身份运行以获得完整功能'
        )
        tips_layout.addWidget(tips_text)
        
        layout.addWidget(tips_group)
        layout.addStretch()

        return panel

    def _show_config(self):
        if self.honeypot and self.honeypot.config:
            ConfigDialog(self.honeypot.config, self).exec()
        else:
            QMessageBox.warning(self, '提示', '配置尚未加载')

    def _show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def _filter_logs(self, level):
        pass

    def _clear_logs(self):
        self.log_text.clear()

    def _get_current_style(self):
        if self.current_theme == 'system':
            detected = get_system_theme()
            return LIGHT_STYLE if detected == 'light' else DARK_STYLE
        elif self.current_theme == 'light':
            return LIGHT_STYLE
        else:
            return DARK_STYLE

    def _create_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu('文件')

        admin_menu = file_menu.addMenu('管理员权限')

        restart_admin_action = QAction('以管理员身份重启', self)
        restart_admin_action.triggered.connect(self._restart_as_admin)
        admin_menu.addAction(restart_admin_action)

        admin_menu.addSeparator()

        current_setting = check_run_as_admin_setting()
        self.run_as_admin_action = QAction('始终以管理员身份运行', self, checkable=True)
        self.run_as_admin_action.setChecked(current_setting)
        self.run_as_admin_action.triggered.connect(self._toggle_run_as_admin_setting)
        admin_menu.addAction(self.run_as_admin_action)

        file_menu.addSeparator()

        config_action = QAction('查看配置', self)
        config_action.triggered.connect(self._show_config)
        file_menu.addAction(config_action)

        save_logs_action = QAction('保存日志', self)
        save_logs_action.triggered.connect(self._save_logs)
        file_menu.addAction(save_logs_action)

        settings_action = QAction('设置', self)
        settings_action.triggered.connect(self._show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction('退出', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        theme_menu = menubar.addMenu('主题')

        self.theme_action_group = QActionGroup(self)
        self.theme_action_group.setExclusive(True)

        system_action = QAction('跟随系统', self, checkable=True)
        system_action.setChecked(True)
        system_action.triggered.connect(lambda: self._set_theme('system'))

        light_action = QAction('浅色模式', self, checkable=True)
        light_action.triggered.connect(lambda: self._set_theme('light'))

        dark_action = QAction('深色模式', self, checkable=True)
        dark_action.triggered.connect(lambda: self._set_theme('dark'))

        self.theme_action_group.addAction(system_action)
        self.theme_action_group.addAction(light_action)
        self.theme_action_group.addAction(dark_action)

        theme_menu.addAction(system_action)
        theme_menu.addAction(light_action)
        theme_menu.addAction(dark_action)

        help_menu = menubar.addMenu('帮助')

        about_action = QAction('关于', self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _show_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def _restart_as_admin(self):
        if is_admin():
            QMessageBox.information(self, '提示', '当前已以管理员身份运行')
            return

        reply = QMessageBox.question(
            self,
            '确认提权',
            '将以管理员身份重启程序，是否继续？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if not run_as_admin():
                QMessageBox.warning(self, '失败', '提权失败，请手动以管理员身份运行')

    def _toggle_run_as_admin_setting(self, checked):
        if checked:
            success = set_run_as_admin_permanently()
            if success:
                QMessageBox.information(self, '成功', '已设置始终以管理员身份运行，下次启动生效')
            else:
                self.run_as_admin_action.setChecked(False)
                QMessageBox.warning(self, '失败', '设置失败，请以管理员身份运行程序后再试')
        else:
            success = remove_run_as_admin_setting()
            if success:
                QMessageBox.information(self, '成功', '已取消始终以管理员身份运行')
            else:
                self.run_as_admin_action.setChecked(True)
                QMessageBox.warning(self, '失败', '取消设置失败')

    def _set_theme(self, theme):
        self.current_theme = theme
        self._apply_theme(theme)

        for action in self.theme_action_group.actions():
            action.setChecked(action.text() == {
                'system': '跟随系统',
                'light': '浅色模式',
                'dark': '深色模式'
            }[theme])

    def _apply_theme(self, theme):
        if theme == 'system':
            detected = get_system_theme()
            style = LIGHT_STYLE if detected == 'light' else DARK_STYLE
            self.log_colors = LIGHT_LOG_COLORS if detected == 'light' else DARK_LOG_COLORS
        elif theme == 'light':
            style = LIGHT_STYLE
            self.log_colors = LIGHT_LOG_COLORS
        else:
            style = DARK_STYLE
            self.log_colors = DARK_LOG_COLORS

        self.setStyleSheet(style)

        for service_name, service in self.service_buttons.items():
            if service['status']:
                service['indicator'].setStyleSheet('QProgressBar::chunk { background-color: #22c55e; }')
                if 'config_status' in service:
                    service['config_status'].setText('运行中')
                    service['config_status'].setStyleSheet('color: #22c55e;')
            else:
                service['indicator'].setStyleSheet('QProgressBar::chunk { background-color: #dc3545; }')
                if 'config_status' in service:
                    service['config_status'].setText('未运行')
                    service['config_status'].setStyleSheet('color: #dc3545;')

    def _toggle_service(self, service_name):
        service = self.service_buttons.get(service_name)
        if not service:
            return

        with self._service_lock:
            if service['status']:
                service['status'] = False
                service['button'].setText('启动')
                service['indicator'].setValue(0)
                service['indicator'].setStyleSheet('QProgressBar::chunk { background-color: #dc3545; }')
                self.status_bar.showMessage(f'{service_name} 服务已停止')
                if 'config_status' in service:
                    service['config_status'].setText('未运行')
                    service['config_status'].setStyleSheet('color: #dc3545;')
                
                if self.honeypot:
                    try:
                        success = self.honeypot.service_manager.stop_service(service_name)
                        if not success:
                            self.log_text.append(f'停止 {service_name} 服务失败')
                    except Exception as e:
                        error_msg = f'停止 {service_name} 服务异常: {type(e).__name__}: {e}'
                        self.log_text.append(error_msg)
                        self.log_text.append(traceback.format_exc())
                        ErrorDialog('操作失败', error_msg, traceback.format_exc(), self).exec()
            else:
                service['status'] = True
                service['button'].setText('停止')
                service['indicator'].setValue(1)
                service['indicator'].setStyleSheet('QProgressBar::chunk { background-color: #22c55e; }')
                self.status_bar.showMessage(f'{service_name} 服务已启动')
                if 'config_status' in service:
                    service['config_status'].setText('运行中')
                    service['config_status'].setStyleSheet('color: #22c55e;')
                
                if self.honeypot:
                    try:
                        success = self.honeypot.service_manager.start_service(service_name)
                        if not success:
                            service['status'] = False
                            service['button'].setText('启动')
                            service['indicator'].setValue(0)
                            if 'config_status' in service:
                                service['config_status'].setText('未运行')
                                service['config_status'].setStyleSheet('color: #dc3545;')
                            self.log_text.append(f'启动 {service_name} 服务失败')
                    except Exception as e:
                        service['status'] = False
                        service['button'].setText('启动')
                        service['indicator'].setValue(0)
                        if 'config_status' in service:
                            service['config_status'].setText('未运行')
                            service['config_status'].setStyleSheet('color: #dc3545;')
                        error_msg = f'启动 {service_name} 服务异常: {type(e).__name__}: {e}'
                        self.log_text.append(error_msg)
                        self.log_text.append(traceback.format_exc())
                        ErrorDialog('操作失败', error_msg, traceback.format_exc(), self).exec()

    def _start_all(self):
        with self._service_lock:
            if self.honeypot:
                try:
                    self.honeypot.start()
                    for name in self.service_buttons:
                        self.service_buttons[name]['status'] = True
                        self.service_buttons[name]['button'].setText('停止')
                        self.service_buttons[name]['indicator'].setValue(1)
                        self.service_buttons[name]['indicator'].setStyleSheet('QProgressBar::chunk { background-color: #22c55e; }')
                        if 'config_status' in self.service_buttons[name]:
                            self.service_buttons[name]['config_status'].setText('运行中')
                            self.service_buttons[name]['config_status'].setStyleSheet('color: #22c55e;')
                    self.status_bar.showMessage('所有服务已启动')
                except Exception as e:
                    error_msg = f'启动所有服务失败: {type(e).__name__}: {e}'
                    self.log_text.append(error_msg)
                    self.log_text.append(traceback.format_exc())
                    ErrorDialog('操作失败', error_msg, traceback.format_exc(), self).exec()
            else:
                self.log_text.append('蜜罐系统未初始化')

    def _stop_all(self):
        with self._service_lock:
            if self.honeypot:
                try:
                    self.honeypot.stop()
                    for name in self.service_buttons:
                        self.service_buttons[name]['status'] = False
                        self.service_buttons[name]['button'].setText('启动')
                        self.service_buttons[name]['indicator'].setValue(0)
                        self.service_buttons[name]['indicator'].setStyleSheet('QProgressBar::chunk { background-color: #dc3545; }')
                        if 'config_status' in self.service_buttons[name]:
                            self.service_buttons[name]['config_status'].setText('未运行')
                            self.service_buttons[name]['config_status'].setStyleSheet('color: #dc3545;')
                    self.status_bar.showMessage('所有服务已停止')
                except Exception as e:
                    error_msg = f'停止所有服务失败: {type(e).__name__}: {e}'
                    self.log_text.append(error_msg)
                    self.log_text.append(traceback.format_exc())
                    ErrorDialog('操作失败', error_msg, traceback.format_exc(), self).exec()
            else:
                self.log_text.append('蜜罐系统未初始化')

    def update_log(self, log_line):
        original_line = log_line
        
        with threading.Lock():
            self._log_cache.append(original_line)
            if len(self._log_cache) > self._log_cache_max_size:
                self._log_cache = self._log_cache[-self._log_cache_max_size:]

        for level, color in self.log_colors.items():
            if f' - {level} - ' in log_line:
                log_line = log_line.replace(f' - {level} - ', f' - <span style="color:{color}">{level}</span> - ')
                break

        self.log_text.append(log_line)

        self._trim_log_lines()

        if self.auto_scroll_btn.isChecked():
            self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def _trim_log_lines(self):
        doc = self.log_text.document()
        if doc.blockCount() > self.log_max_lines:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.NextBlock, cursor.MoveMode.KeepAnchor, doc.blockCount() - self.log_max_lines)
            cursor.removeSelectedText()
            cursor.deleteChar()

    def _save_logs(self):
        if not self._log_cache:
            QMessageBox.information(self, '提示', '没有可保存的日志')
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            '保存日志',
            os.path.join(get_log_dir(), f'cyberhoney_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            '日志文件 (*.log);;所有文件 (*.*)'
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(self._log_cache))
                QMessageBox.information(self, '成功', f'日志已保存到:\n{file_path}')
                self.status_bar.showMessage(f'日志已保存: {file_path}')
            except Exception as e:
                error_msg = f'保存日志失败: {type(e).__name__}: {e}'
                self.log_text.append(error_msg)
                QMessageBox.warning(self, '失败', error_msg)

    def _clear_log_cache(self):
        with threading.Lock():
            self._log_cache.clear()
        self.log_text.clear()
        self.status_bar.showMessage('日志缓存已清空')

    def closeEvent(self, event):
        if self._data_timer:
            self._data_timer.stop()

        if self.honeypot:
            try:
                self.honeypot.stop()
            except Exception as e:
                self.log_text.append(f'关闭蜜罐异常: {e}')

        if hasattr(self, '_log_handler'):
            logger = logging.getLogger('honeypot')
            logger.removeHandler(self._log_handler)
            self._log_handler.close()

        self._clear_log_cache()

        clear_cache()

        event.accept()


def main(config_path='config.yaml'):
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)

    initial_theme = get_system_theme()
    if initial_theme == 'dark':
        app.setStyleSheet(DARK_STYLE)
    else:
        app.setStyleSheet(LIGHT_STYLE)

    window = MainWindow(config_path)
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()