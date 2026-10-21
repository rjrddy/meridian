from pybind11.setup_helpers import Pybind11Extension
from setuptools import setup

setup(
    ext_modules=[
        Pybind11Extension(
            "meridian._fusion",
            ["core/fusion.cpp"],
            cxx_std=20,
            extra_compile_args=["-Wall", "-Wextra", "-Werror", "-ffp-contract=off"],
        )
    ]
)
