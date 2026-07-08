import ctypes
import sys
import os
import winreg


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    if is_admin():
        return True
    
    script_path = sys.argv[0]
    params = ' '.join(sys.argv[1:])
    
    if script_path.endswith('.py'):
        exe_path = sys.executable
        params = f'"{script_path}" {params}'
    else:
        exe_path = script_path
    
    try:
        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            exe_path,
            params,
            None,
            1
        )
        
        if result > 32:
            sys.exit(0)
        else:
            return False
    except Exception as e:
        return False


def set_run_as_admin_permanently(exe_path=None):
    if exe_path is None:
        exe_path = sys.argv[0]
    
    if exe_path.endswith('.py'):
        exe_path = sys.executable
    
    try:
        key_path = r'Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
            winreg.SetValueEx(key, exe_path, 0, winreg.REG_SZ, '~ RUNASADMIN')
        return True
    except Exception:
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, exe_path, 0, winreg.REG_SZ, '~ RUNASADMIN')
            return True
        except Exception:
            return False


def check_run_as_admin_setting(exe_path=None):
    if exe_path is None:
        exe_path = sys.argv[0]
    
    if exe_path.endswith('.py'):
        exe_path = sys.executable
    
    try:
        key_path = r'Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, exe_path)
            return 'RUNASADMIN' in value
    except Exception:
        return False


def remove_run_as_admin_setting(exe_path=None):
    if exe_path is None:
        exe_path = sys.argv[0]
    
    if exe_path.endswith('.py'):
        exe_path = sys.executable
    
    try:
        key_path = r'Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
            winreg.DeleteValue(key, exe_path)
        return True
    except Exception:
        return False