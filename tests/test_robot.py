import pytest
from mock import MagicMock, call

from aspyrobot.robot import Robot, RobotError


@pytest.fixture
def robot():
    robot = Robot('TEST_ROBOT:')
    for attr in robot.attrs:
        setattr(robot, attr, MagicMock())
    robot.foreground_done.get.return_value = 1
    return robot


def test_execute(robot):
    robot.calibrate = MagicMock()
    robot.execute('calibrate')
    assert robot.calibrate.put.call_args_list == [call(1, wait=True), call(0)]


def test_run_foreground_operation_raises_exception_if_busy(robot):
    robot.foreground_done.get.return_value = 0
    with pytest.raises(RobotError) as exception:
        robot.run_foreground_operation('calibrate', 'l 0')
    assert 'busy' in str(exception)


def test_run_foreground_operation_sets_args_and_issues_command(robot):
    robot.foreground_done.get.side_effect = [1, 0, 1]
    robot.task_result.get.return_value = 'ok done'
    result = robot.run_foreground_operation('calibrate', 'l 0')
    assert robot.run_args.put.call_args == call('l 0')
    assert robot.generic_command.put.call_args == call('calibrate')
    assert result == 'ok done'


def test_run_foreground_operation_raises_exception_if_op_doesnt_start(robot):
    with pytest.raises(RobotError) as exception:
        robot.run_foreground_operation('calibrate', 'l 0', timeout=0.1)
    assert 'failed to start' in str(exception)


def test_snapshot():

    class SimpleRobot(Robot):
        attrs = {
            'num_attr': 'NUM_ATTR',
            'str_attr': 'STR_ATTR',
            'char_attr': 'CHAR_ATTR',
        }

        def __init__(self, prefix, **kwargs):
            self.num_attr = MagicMock(type='ctrl_double', value=1)
            self.str_attr = MagicMock(type='time_string', char_value='s')
            self.char_attr = MagicMock(type='ctrl_char', char_value='c')

    robot = SimpleRobot('TEST_ROBOT:')
    response = robot.snapshot()
    assert response == {'num_attr': 1, 'str_attr': 's', 'char_attr': 'c'}