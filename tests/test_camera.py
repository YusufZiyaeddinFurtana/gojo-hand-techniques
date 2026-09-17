import time
import unittest
from unittest.mock import Mock
from gojo.camera import _authorize_camera, CameraPermissionError


class CameraPermissionTests(unittest.TestCase):
    def device(self, status):
        device = Mock()
        device.authorizationStatusForMediaType_.return_value = status
        return device

    def test_authorized_does_not_prompt(self):
        device = self.device(3)
        _authorize_camera(device, 'video', Mock())
        device.requestAccessForMediaType_completionHandler_.assert_not_called()

    def test_denied_and_restricted_do_not_reprompt(self):
        for status in (1, 2):
            device = self.device(status)
            with self.assertRaises(CameraPermissionError):
                _authorize_camera(device, 'video', Mock())
            device.requestAccessForMediaType_completionHandler_.assert_not_called()

    def test_pending_waits_for_callback(self):
        device = self.device(0)
        callbacks = []
        device.requestAccessForMediaType_completionHandler_.side_effect = lambda media, cb: callbacks.append(cb)
        pump = Mock(side_effect=lambda: callbacks[0](True))
        _authorize_camera(device, 'video', pump)
        pump.assert_called_once()

    def test_user_denial_is_reported(self):
        device = self.device(0)
        device.requestAccessForMediaType_completionHandler_.side_effect = lambda media, cb: cb(False)
        with self.assertRaises(CameraPermissionError):
            _authorize_camera(device, 'video', Mock())

    def test_unanswered_prompt_times_out(self):
        with self.assertRaises(CameraPermissionError):
            _authorize_camera(self.device(0), 'video', lambda: time.sleep(.002), timeout=.001)
