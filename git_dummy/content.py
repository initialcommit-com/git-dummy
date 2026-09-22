"""Realistic-looking content for the generated history: a small web service
with a handful of files, commit messages that read like a real log, and a few
authors. Everything comes from one seeded random generator, so the same seed
gives the same repository."""

from __future__ import annotations

import random
from typing import List, Tuple

AUTHORS = [
    ("Ada Lovelace", "ada@example.com"),
    ("Grace Hopper", "grace@example.com"),
    ("Linus Torvalds", "linus@example.com"),
    ("Margaret Hamilton", "margaret@example.com"),
    ("Dennis Ritchie", "dennis@example.com"),
]

# Files of a small service, with the first version of each.
FILES = {
    "README.md": "# Orders service\n\nA small HTTP service that stores and lists orders.\n",
    "app.py": "from routes import register\n\n\ndef create_app():\n    app = App()\n    register(app)\n    return app\n",
    "models.py": "class Order:\n    def __init__(self, id, total):\n        self.id = id\n        self.total = total\n",
    "routes.py": "def register(app):\n    app.get('/orders', list_orders)\n\n\ndef list_orders(request):\n    return []\n",
    "utils.py": "def parse_int(value, default=0):\n    try:\n        return int(value)\n    except ValueError:\n        return default\n",
    "config.yaml": "port: 8080\nlog_level: info\n",
    "requirements.txt": "flask==3.0.0\n",
    "tests/test_orders.py": "def test_list_orders_empty():\n    assert list_orders(None) == []\n",
}

# (message template, files it touches, line it appends)
CHANGES = [
    ("Add pagination to the orders list", ["routes.py"], "    page = parse_int(request.args.get('page'), 1)\n"),
    ("Validate order totals", ["models.py"], "        if total < 0:\n            raise ValueError('total must not be negative')\n"),
    ("Fix off-by-one in pagination", ["routes.py"], "    start = (page - 1) * PAGE_SIZE\n"),
    ("Log the request path", ["app.py"], "    app.before(lambda req: log.info(req.path))\n"),
    ("Document the /orders endpoint", ["README.md"], "\n## GET /orders\n\nReturns the orders, newest first.\n"),
    ("Pin the test dependencies", ["requirements.txt"], "pytest==8.0.0\n"),
    ("Handle missing config values", ["utils.py"], "\n\ndef get(cfg, key, default=None):\n    return cfg.get(key, default)\n"),
    ("Add a health check", ["routes.py"], "\n\ndef health(request):\n    return {'ok': True}\n"),
    ("Cover pagination in the tests", ["tests/test_orders.py"], "\n\ndef test_pagination_starts_at_one():\n    assert page_start(1) == 0\n"),
    ("Raise the default log level", ["config.yaml"], "request_log: true\n"),
    ("Return 404 for unknown orders", ["routes.py"], "\n\ndef get_order(request, id):\n    return find(id) or NotFound()\n"),
    ("Refactor Order into a dataclass", ["models.py"], "\n\n# TODO: replace the constructor with @dataclass\n"),
    ("Add created_at to orders", ["models.py"], "        self.created_at = now()\n"),
    ("Speed up the order query", ["routes.py"], "    orders = Order.query(limit=PAGE_SIZE, offset=start)\n"),
    ("Update the README quickstart", ["README.md"], "\nRun `python app.py` and open http://localhost:8080/orders.\n"),
    ("Add currency to totals", ["models.py", "routes.py"], "    # totals are stored in cents\n"),
    ("Fix flaky test on Windows", ["tests/test_orders.py"], "\n\n# the temp dir is cleaned up per test\n"),
    ("Retry failed database connections", ["app.py"], "    app.retries = 3\n"),
    ("Export orders as CSV", ["routes.py"], "\n\ndef export_csv(request):\n    return to_csv(Order.all())\n"),
    ("Bump flask", ["requirements.txt"], "flask==3.1.0\n"),
]

BRANCH_NAMES = [
    "feature/pagination",
    "fix/order-totals",
    "feature/health-check",
    "chore/dependencies",
    "docs/readme",
    "feature/csv-export",
    "fix/windows-tests",
    "feature/retries",
]

STASH_NOTES = ["half-done pagination", "debugging totals", "wip: csv export", "try a bigger page size"]

INITIAL_MESSAGE = "Initial commit"


class Content:
    """Deterministic picker of authors, messages, files and branch names."""

    def __init__(self, seed: int):
        self.rng = random.Random(seed)
        self._changes = list(CHANGES)
        self.rng.shuffle(self._changes)
        self._i = 0

    def author(self) -> Tuple[str, str]:
        return self.rng.choice(AUTHORS)

    def change(self):
        """(message, [(file, appended text), ...]) for the next commit."""
        template = self._changes[self._i % len(self._changes)]
        self._i += 1
        message, files, line = template
        if self._i > len(self._changes):
            message = f"{message} (again)"
        return message, [(f, line) for f in files]

    def branch_name(self, index: int) -> str:
        if index - 1 < len(BRANCH_NAMES):
            return BRANCH_NAMES[index - 1]
        return f"feature/topic-{index}"

    def stash_note(self, index: int) -> str:
        return STASH_NOTES[index % len(STASH_NOTES)]

    @staticmethod
    def initial_files() -> List[Tuple[str, str]]:
        return list(FILES.items())
