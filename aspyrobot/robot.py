from time import time

from epics import PV, poll

from .exceptions import RobotError


DELAY_TO_PROCESS = .3


class Robot(object):
    """
    The ``Robot`` class creates EPICS connections to the robot IOC. It is
    intended to be supplied to ``RobotServer`` and not used directly.

    Args:
        prefix (str): Prefix of the robot IOC PVs. Eg ``'SR03ID01:'``.

    """
    attrs = {
        'status': 'RSTATUS_MON',
        'current_task': 'COP_MON',
        'task_args': 'RA_CMD',
        'task_message': 'TASKMSG_MON',
        'task_progress': 'TASKPROG_MON',
        'task_result': 'RRESULT_MON',
        'model': 'MODEL_MON',
        'time': 'TIME_MON',
        'at_home': 'ATHOME_STATUS',
        'motors_on': 'MOTOR_STATUS',
        'motors_on_command': 'MOTOR_CMD',
        'toolset': 'TOOL_MON',
        'toolset_command': 'TOOL_CMD',
        'foreground_done': 'FDONE_STATUS',
        'system_error_message': 'ERRMSG_MON',
        'foreground_error': 'FERR_STATUS',
        'foreground_error_message': 'FOREEMSG_MON',
        'safety_gate': 'SAFETYON_STATUS',
        'generic_command': 'GENERIC_CMD',
        'generic_float_command': 'GENERICFLOAT_CMD',
        'generic_string_command': 'GENERICSTR_CMD',
        'client_update': 'CLIENTUPDATE_MON',
        'client_response': 'CLIENTRESP_MON',
        'closest_point': 'CLOSESTP_MON',
    }
    attrs_r = {v: k for k, v in attrs.items()}

    def __init__(self, prefix):
        self._prefix = prefix
        for attr, suffix in self.attrs.items():
            pv = PV(prefix + suffix, form='ctrl')
            setattr(self, attr, pv)

    def snapshot(self):
        data = {}
        for attr in self.attrs:
            pv = getattr(self, attr)
            if 'string' in pv.type or 'char' in pv.type:
                value = pv.char_value
            else:
                value = pv.value
            data[attr] = value
        return data

    def execute(self, attr):
        pv = getattr(self, attr)
        pv.put(1, wait=True)
        pv.put(0)

    def run_task(self, name, args='', timeout=.5):
        if not self.foreground_done.get():
            raise RobotError('busy')
        self.task_args.put(args or '\0')
        poll(DELAY_TO_PROCESS)
        self.generic_command.put(name)
        self._wait_for_foreground_busy(timeout)
        self._wait_for_foreground_free()
        poll(DELAY_TO_PROCESS)
        # TODO: Check for foreground_error
        result = self.task_result.get(as_string=True)
        status, _, message = result.partition(' ')
        if status.lower() not in {'ok', 'normal'}:  # TODO
            raise RobotError(message)
        return message

    def _wait_for_foreground_busy(self, timeout):
        t0 = time()
        while time() < t0 + timeout:
            if self.foreground_done.get() == 0:
                break
            poll(.01)
        else:
            raise RobotError('operation failed to start')

    def _wait_for_foreground_free(self):
        while True:
            if self.foreground_done.get() == 1:
                break
            poll(.01)
