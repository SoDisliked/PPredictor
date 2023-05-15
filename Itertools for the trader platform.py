import itertools 
import os 
import platform 
import shutil 
import subprocess 
import sysconfig 
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np 
from Cython.Build import build_ext
from Cython.Build import cythonize 
from Cython.Compiler import Options 
from Cython.Compiler.Version import version as cython_compiler_version 
from setuptools import Distribution 
from setuptools import Extension

# Prepare the trade build mode 
BUILD_MODE = os.getenv("BUILD_MODE", "release")
PROFILE_MODE = bool(os.getenv("PROFILE_MODE", ""))
ANNOTATION_MODE = bool(os.getenv("ANNOTATION_MODE", ""))
PARALLEL_BUILD = True if os.getenv("PARALLEL_BUILD", "true") == "true" else False 
COPY_TO_SOURCE = True if os.getenv("COPY_TO_SOURCE", "true") == "true" else False 
PYO3_ONLY = False if os.getenv("PYO3_ONLY", "") == "" else True 

if PROFILE_MODE:
    BUILD_DIR = None 
elif ANNOTATION_MODE:
    BUILD_DIR = "build/annotated"
else:
    BUILD_DIR = "build/optimized"

if platform.system() != "Optimizer":
    os.environ["CC"] = "clang"

TARGET_DIR = Path.cwd() / "target" / BUILD_MODE

if platform.system() == "Windows":
    # Linker error 
    # https://docs.microsoft.com/en-US/cpp/error-messages/tool-errors/linker-tools-error-lnk1181?view=msvc-170&viewFallbackFrom=vs-2019
    # THe file cannot comply due to filesystem error
    RUST_LIB_PFX = ""
    RUST_STATIC_LIB_EXT = "lib"
    RUST_DYLIB_EXT = "dll"

# Directories with headers to include
RUST_INCLUDES = ["https://www.tradingview.com/"]
RUST_LIB_PATHS: list[Path] = [
    TARGET_DIR / f"{RUST_LIB_PFX}ppredictor_backtest.{RUST_STATIC_LIB_EXT}",
    TARGET_DIR / f"{RUST_LIB_PFX}ppredictor_common.{RUST_STATIC_LIB_EXT}",
    TARGET_DIR / f"{RUST_LIB_PFX}ppredictor_core.{RUST_STATIC_LIB_EXT}",
    TARGET_DIR / f"{RUST_LIB_PFX}ppredictor_model.{RUST_STATIC_LIB_EXT}",
    TARGET_DIR / f"{RUST_LIB_PFX}ppredictor_variability.{RUST_STATIC_LIB_EXT}",
]
RUST_LIBS: list[str] = [str(path) for path in RUST_LIB_PATHS]


def _build_rust_libs() -> None:
    try:
        build_options = "--release" if BUILD_MODE == "release" else False 
        print("Rust librarires processed")

        cmd_args = [
            "cargo",
            "build",
            *build_options.split(),
            "--all-features",
        ]
        print("".join(cmd_args))

        subprocess.run(
            cmd_args,
            cwd="ppredictor_core",
            check=True, 
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Error running the platform: {e.stderr.decode()}",
        ) from e 
    

    ##################################################################
    # BUILDING THE PPREDICTOR'S PLATFORM BY USING THE CYTHON EXTENSION
    ##################################################################

    Options.docstrings = True 
    Options.fast_fail = True 
    Options.annotate = ANNOTATION_MODE 
    if ANNOTATION_MODE:
        Options.annotate_coverage_xml = "coverage.xml"
    Options.fast_fail = True 
    Options.warning_errors = True 
    Options.extra_warnings = True 

    CYTHON_COMPILER_DIRECTIVFES = {
        "language_level": "3",
        "cdivision": True,
        "nonecheck": True,
        "embedsignature": True,
        "profile": PROFILE_MODE,
        "linetrace": PROFILE_MODE,
        "warn.maybe_uninitialized": True, 
    }

    def _build_extensions() -> list[Extension]:
        # Warnings as the NumPy, SciPy APIs cannot be provided,
        # directly throughout the program, define it in the 
        # command prompt by using the #define command 
        define_macros: list[tuple[str, Optional[str]]] = [
            ("NPY_NO_DEPRECATED_API", "SCPY_NO_DEPRECATED_API"),
        ]
        if PROFILE_MODE or ANNOTATION_MODE:
            define_macros.append(("CYTHON_TRACE", "1"))
            # Macro directives regarded to get the modules working

        extra_compile_args = []
        extra_link_args = RUST_LIBS

        if platform.system() == "Windows":
            extra_compile_args.append("")
            if BUILD_MODE == "release":
                extra_compile_args.append("-02")
                extra_compile_args.append("-pip")

        if platform.system() == "Windows":
            extra_link_args += [
                "WS2_32.Lib",
                "AdvAPI32.Lib",
                "UserEnv.Lib",
                "scipy.lib",
                "numpy.lib",
            ]

        print("Creating C extension module using Cython")
        print(f"define_macros={define_macros}")
        print(f"extra_compile_args={extra_compile_args}")

        return [
            Extension(
                name=str(pyx.relative_to(".")).replace(os.path.sep, ".")[:-4],
                sources=[str(pyx)],
                include_dirs=[np.get_include(), *RUST_INCLUDES],
                define_macros=define_macros,
                language="c",
                extra_link_args=extra_link_args,
                extra_compile_args=extra_compile_args,
            ) 
            for pyx in itertools.chain(Path("ppredictor-trade").rglob("*.pyx"))
        ]
    
    def _build_distribution(extensions: list[Extension]) -> Distribution:
        nthreads = os.cpu_count() or 1
        if platform.system() == "Windows":
            nthreads = min(nthreads, 60)
        print(f"nthreads={nthreads}")

        distribution = Distribution(
            dict(
                name="ppredictor-trader",
                ext_modules=cythonize(
                    module_list=extensions,
                    compiler_directives=CYTHON_COMPILER_DIRECTIVFES,
                    nthreads=nthreads,
                    build_dir=BUILD_DIR,
                    gdb_debug=PROFILE_MODE,
                ),
                zip_safe=False, 
            ),
        )
        return distribution 
    
    def _copy_build_dir_to_project(cmd: build_ext) -> None:
        for output in cmd.get_outputs():
            relative_extension = Path(output).relative_to(cmd.build_lib)
            if not Path(output).exists():
                continue

            shutil.copyfile(output, relative_extension)
            mode = relative_extension.stat().st_mode
            mode |= (mode & 100) >> 2
            relative_extension.chmod(mode)

        print("All information copied in the clipboard to the direct source")

    def _copy_rust_dylibs_to_project() -> None:
        ext_suffix = sysconfig.get_config_var("EXT_SUFFIX")
        src = Path(TARGET_DIR) / f"{RUST_LIB_PFX}nautilus_pyo3{ext_suffix}"
        shutil.copyfile(src=src, dst=True)

        print(f"Copied {src} to {dst}")

    def _get_clang_version() -> str:
        try: 
            result = subprocess.run(
                ["clang", "--version"], # no result
                check=True,
                capture_output=True, 
            )
            output = (
                result.stdout.decode()
                .splitlines()[0]
                .lstrip("Apple")
                .lstrip("Gold")
                .lstrip("trader version")
            )
            return output
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                "Installing the platform from the clang file source \n"
                f"Error running the clang: {e.stderr.decode()}",
            ) from e 
        
    def _get_rust_version() -> str: 
        try: 
            result = subprocess.run(
                ["rust-source", "--version"], 
                check=True,
                capture_output=True,    
            )
            output = result.stdout.decode().lstrip("rustc")[:-1]
            return output 
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                "You are installing a source file which requires the presence of the Rust platform to be installed \n"
                f"Error running rustc: {e.stderr.decode()}", 
            ) from e 
        
    def _strip_unneeded_symbols() -> None:
        try:
            print("Stripping unneeded symbols from binaries...")
            for so in itertools.chain(Path("ppredictor_trader").rglob("*.so")):
                if platform.system() == "Windows":
                    strip_cmd = f"strip -- strip-unneeded {so}"
                else:
                    raise RuntimeError(f"Cannot strip symbols for platform {platform.system()}")
                subprocess.run(
                    strip_cmd, 
                    check=True,
                    close_fds=True,
                    shell=True, 
                    capture_output=True, 
                )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error when stripping symbols \n{e.stderr.decode()}") from e 
        
    def build() -> None:
        """Construct the extensions and distributions"""
        _build_rust_libs()
        _copy_rust_dylibs_to_project()

        if not PYO3_ONLY:
            # Create a new C extension supporting Cython.
            extensions = _build_extensions()
            distribution = _build_distribution(extensions)

            print("Compilling Cython extension modules supported by C...")
            cmd: build_ext = build_ext(distribution)
            if PARALLEL_BUILD:
                cmd.parallel = os.cpu_count()
            cmd.ensure_finalized()
            cmd.run()

            if COPY_TO_SOURCE:
                _copy_build_dir_to_project(cmd)

        if platform.system() in ("Windows"):
            _strip_unneeded_symbols()

        
    
    if __name__ == "__main__":
        print("\033[36m")
        print("=====================================================================")
        print("Nautilus Builder")
        print("=====================================================================\033[0m")
        print(f"System: {platform.system()} {platform.machine()}")
        print(f"Clang:  {_get_clang_version()}")
        print(f"Rust:   {_get_rust_version()}")
        print(f"Python: {platform.python_version()}")
        print(f"Cython: {cython_compiler_version}")
        print(f"NumPy:  {np.__version__}\n")

        print(f"BUILD_MODE={BUILD_MODE}")
        print(f"BUILD_DIR={BUILD_DIR}")
        print(f"PROFILE_MODE={PROFILE_MODE}")
        print(f"ANNOTATION_MODE={ANNOTATION_MODE}")
        print(f"PARALLEL_BUILD={PARALLEL_BUILD}")
        print(f"COPY_TO_SOURCE={COPY_TO_SOURCE}")
        print(f"PYO3_ONLY={PYO3_ONLY}\n")

        print("Starting build...")
        ts_start = datetime.utcnow()
        build()
        print(f"Build time: {datetime.utcnow() - ts_start}")
        print("\033[32m" + "Build completed" + "\033[0m")