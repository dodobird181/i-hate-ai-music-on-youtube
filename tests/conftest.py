import pathlib

import pytest

from models import DB_PATH, init_db


@pytest.fixture(autouse=True)
def use_db(request):
    """
    Delete the test database and re-initialize it. Then run the test and delete the test database again afterwards.
    Use on a test by adding the `@pytest.mark.use_db` decorator.
    """
    if request.node.get_closest_marker("use_db"):
        if pathlib.Path(DB_PATH).exists():
            pathlib.Path(DB_PATH).unlink()
        init_db()
        yield
        if pathlib.Path(DB_PATH).exists():
            pathlib.Path(DB_PATH).unlink()
    else:
        # unmarked tests: do nothing
        yield
