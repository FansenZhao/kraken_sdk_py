from setuptools import setup, find_packages

setup(
    name="krakensdr",
    version="1.0.0",
    packages=find_packages(),
    # 核心依赖列表
    install_requires=[
        "numpy",
        "scipy==1.9.3",
        "numba==0.56.4",
        "configparser",
        "pyzmq",
        "scikit-rf",
    ],
    author="Xudong Zhao",
    description="KrakenSDR Python Client SDK",
    python_requires=">=3.10", # 限制 Python 版本
)