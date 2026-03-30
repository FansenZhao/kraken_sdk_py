from setuptools import setup, find_packages

setup(
    name="krakensdr",
    version="1.0.0",
    packages=find_packages(),
    # 核心依赖列表
    install_requires=[
        "",
    ],
    author="Xudong Zhao",
    description="KrakenSDR Python Client SDK",
    python_requires=">=3.10", # 限制 Python 版本
)
