"""Report browser console and uncaught JavaScript errors."""

from contextlib import contextmanager


@contextmanager
def checked_page(page):
    errors = []

    def console(message):
        if message.type == "error":
            errors.append(message.text)

    def pageerror(error):
        errors.append(str(error))

    page.on("console", console)
    page.on("pageerror", pageerror)
    page.set_default_timeout(5000)
    page.set_default_navigation_timeout(10000)
    try:
        yield page
        assert not errors, f"Browser errors: {errors}"
    finally:
        page.remove_listener("console", console)
        page.remove_listener("pageerror", pageerror)
