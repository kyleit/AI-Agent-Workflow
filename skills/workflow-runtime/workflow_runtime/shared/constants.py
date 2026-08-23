MAX_FILE_LINES: int = 500
DEFAULT_ENCODING: str = "utf-8"
DEFAULT_TIMEOUT: int = 30
STDLIB_ONLY_MODULES: tuple[str, ...] = (
    "dataclasses",
    "enum",
    "typing",
    "datetime",
    "abc",
    "pathlib",
    "hashlib",
    "json",
    "sys",
    "ast",
    "re",
    "os",
    "math",
    "uuid",
    "itertools",
    "functools",
    "collections",
)
LOG_FILE_PATH: str = ".agents/runtime/tests.log"
SANDBOX_ROOT: str = "python-runtime-dev"
