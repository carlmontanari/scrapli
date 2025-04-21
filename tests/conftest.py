def pytest_addoption(parser):
    parser.addoption(
        "--record",
        action="store_true",
        default=False,
        help="record unit/integration test data from the real device",
    )

    parser.addoption(
        "--update",
        action="store_true",
        default=False,
        help="update the unit/integration test golden files",
    )
