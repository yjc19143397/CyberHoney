from setuptools import setup, find_packages

setup(
    name='CyberHoney',
    version='1.0.3',
    description='A multi-service honeypot for cybersecurity monitoring',
    author='Yjc',
    author_email='yjc19143397@163.com',
    packages=find_packages(),
    install_requires=[
        'paramiko>=2.12.0',
        'flask>=2.3.0',
        'pyyaml>=6.0',
        'sqlalchemy>=2.0.0',
        'click>=8.0',
        'scapy>=2.5.0',
        'PyQt6>=6.0.0',
    ],
    entry_points={
        'console_scripts': [
            'cyberhoney=honeypot.cli.main:cli',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.14',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.14',
)