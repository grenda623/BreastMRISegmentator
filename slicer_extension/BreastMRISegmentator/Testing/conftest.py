"""pytest configuration for the extension's Slicer-runtime tests."""


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "slow: end-to-end tests needing a GPU and the Exp4x weights.",
    )
