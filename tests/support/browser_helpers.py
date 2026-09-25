"""Report browser console and uncaught JavaScript errors."""

from contextlib import contextmanager


@contextmanager
def checked_page(page, *, expected_page_errors=()):
    errors = []
    page_errors = []

    def console(message):
        if message.type == "error":
            errors.append(message.text)

    def pageerror(error):
        page_errors.append(str(error))

    def requestfailed(request):
        errors.append(f"Request failed: {request.url}: {request.failure}")

    def dialog(dialog):
        errors.append(f"Unexpected {dialog.type} dialog: {dialog.message}")
        dialog.dismiss()

    page.on("console", console)
    page.on("pageerror", pageerror)
    page.on("requestfailed", requestfailed)
    page.on("dialog", dialog)
    page.set_default_timeout(5000)
    page.set_default_navigation_timeout(10000)
    try:
        yield page
    finally:
        page.remove_listener("console", console)
        page.remove_listener("pageerror", pageerror)
        page.remove_listener("requestfailed", requestfailed)
        page.remove_listener("dialog", dialog)
        assert not errors, f"Browser errors: {errors}"
        assert page_errors == list(expected_page_errors), f"Uncaught browser errors: {page_errors}"
