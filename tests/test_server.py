import pytest
from mock import MagicMock, call
from aspyrobot.server import RobotServer


@pytest.fixture
def server():
    server = RobotServer(robot=None, logger=MagicMock())
    return server


def test_process_request(server):
    server.calibrate = MagicMock(return_value=None)
    message = {'operation': 'calibrate', 'parameters': {'target': 'middle'}}
    response = server.process_request(message)
    assert server.calibrate.call_args == call(target='middle')
    assert response['error'] is None


def test_process_request_returns_error_for_invalid_operation(server):
    message = {'operation': 'does_not_exist', 'parameters': {}}
    response = server.process_request(message)
    assert response['error'] == 'invalid request'


def test_on_robot_update(server):
    server.update_some_attr = MagicMock()
    server.on_robot_update("{'set': 'some_attr', 'value': 5, 'extra': 'info'}")
    assert server.update_some_attr.call_args == call(value=5, extra='info')


def test_on_robot_update_with_bad_string(server):
    server.on_robot_update("{")
    assert server.logger.error.called is True


def test_on_robot_update_missing_method(server):
    server.on_robot_update("{'set': 'unexpected_attr'}")
    assert server.logger.warning.called is True


def test_on_robot_update_with_unexpected_attributes(server):
    def update_some_attr(value):
        pass
    server.update_some_attr = update_some_attr
    server.on_robot_update("{'set': 'some_attr', 'value': 5, 'extra': 'info'}")
    assert server.logger.error.called is True
