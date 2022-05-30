import yaml


def pytest_assert(left, right, message):
    assert left == right, message


def verify_fixture(name: str, data: bytes):
    filename = f'tests/autofixtures/{name}.yaml'
    try:
        with open(filename) as f:
            original = yaml.unsafe_load(f)
        assert original == data, f"Response for {filename} differs"
    except FileNotFoundError:
        with open(filename, 'w') as f:
            yaml.dump(data, f)
