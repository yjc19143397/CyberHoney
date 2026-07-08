import sys
import os

if sys.version_info < (3, 14):
    print(f"错误：需要Python 3.14或更高版本，当前版本是{sys.version}")
    sys.exit(1)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from honeypot.cli.main import cli

if __name__ == '__main__':
    cli()