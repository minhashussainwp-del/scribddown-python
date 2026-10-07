"""Entry point for Botkeep: `python main.py`.

Reads PORT from the environment (default 8000), binds 0.0.0.0, and serves
the Flask app through gunicorn for production robustness.
"""
import os

from gunicorn.app.base import BaseApplication

from app import create_app

app = create_app()


class StandaloneApplication(BaseApplication):
    """Programmatic gunicorn runner (no config file needed)."""

    def __init__(self, flask_app, options=None):
        self.options = options or {}
        self.application = flask_app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def main():
    port = int(os.environ.get("PORT", "8000"))
    workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
    StandaloneApplication(app, {
        "bind": f"0.0.0.0:{port}",
        "workers": workers,
        # Long timeout: Scribd scrapes can take minutes.
        "timeout": 300,
        "graceful_timeout": 30,
        "accesslog": "-",
        "errorlog": "-",
    }).run()


if __name__ == "__main__":
    main()
