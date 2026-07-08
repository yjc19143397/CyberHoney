import subprocess
import sys
import os
import re
from datetime import datetime

def run_command(cmd, cwd=None):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, 
                               capture_output=True, text=True, encoding='utf-8')
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), -1

def get_current_version(changelog_path):
    """从CHANGELOG.md获取当前版本号"""
    if os.path.exists(changelog_path):
        with open(changelog_path, 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.search(r'## \[v([\d.]+)\]', content)
        if match:
            return match.group(1)
    return "1.0.0"

def increment_version(version):
    """递增版本号"""
    parts = version.split('.')
    if len(parts) == 3:
        major, minor, patch = map(int, parts)
        patch += 1
        return f"{major}.{minor}.{patch}"
    return f"{version}.1"

def update_changelog(changelog_path, changes):
    """更新CHANGELOG.md"""
    current_version = get_current_version(changelog_path)
    new_version = increment_version(current_version)
    today = datetime.now().strftime('%Y-%m-%d')
    
    header = f"## [v{new_version}] - {today}\n\n### Changed\n\n"
    
    if isinstance(changes, list):
        change_items = "\n".join([f"- {change}" for change in changes])
    else:
        change_items = f"- {changes}"
    
    if os.path.exists(changelog_path):
        with open(changelog_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content.startswith('# Changelog'):
            # 在第一个版本之前插入新版本
            lines = content.split('\n')
            insert_idx = lines.index('') if '' in lines else 4
            lines.insert(insert_idx, header + change_items + '\n')
            content = '\n'.join(lines)
        else:
            content = header + change_items + '\n\n' + content
    else:
        content = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n{header}{change_items}\n"
    
    with open(changelog_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return new_version

def sync_to_github(changes):
    """同步更改到GitHub"""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    changelog_path = os.path.join(project_dir, 'CHANGELOG.md')
    
    print("=" * 60)
    print("CyberHoney - 同步到GitHub")
    print("=" * 60)
    
    print(f"\n1. 更新 CHANGELOG.md...")
    new_version = update_changelog(changelog_path, changes)
    print(f"   版本更新: v{get_current_version(changelog_path)} -> v{new_version}")
    
    print(f"\n2. 检查git状态...")
    stdout, stderr, code = run_command("git status", cwd=project_dir)
    if code != 0:
        print(f"   错误: {stderr}")
        return False
    
    print(f"\n3. 添加文件...")
    stdout, stderr, code = run_command("git add .", cwd=project_dir)
    if code != 0:
        print(f"   错误: {stderr}")
        return False
    print("   完成")
    
    print(f"\n4. 提交更改...")
    commit_msg = f"v{new_version}: {changes[0] if isinstance(changes, list) else changes}"
    if len(commit_msg) > 50:
        commit_msg = commit_msg[:47] + "..."
    stdout, stderr, code = run_command(f'git commit -m "{commit_msg}"', cwd=project_dir)
    if code != 0:
        print(f"   错误: {stderr}")
        return False
    print(f"   提交成功: {commit_msg}")
    
    print(f"\n5. 推送到GitHub...")
    stdout, stderr, code = run_command("git push origin main", cwd=project_dir)
    if code != 0:
        print(f"   错误: {stderr}")
        return False
    print("   推送成功!")
    
    print("\n" + "=" * 60)
    print(f"同步完成! 版本: v{new_version}")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python sync.py \"更改描述\"")
        print("示例: python sync.py \"添加新功能\"")
        print("或: python sync.py \"修复Bug\" \"优化性能\"")
        sys.exit(1)
    
    changes = sys.argv[1:]
    success = sync_to_github(changes)
    sys.exit(0 if success else 1)