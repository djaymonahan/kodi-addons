# -*- coding: utf-8 -*-
# Name:        login_widow
# Author:      Roman V.M.
# Created:     18.02.2014
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html

import pyxbmct
from simpleplugin import Plugin

plugin = Plugin()
_ = plugin.initialize_gettext()


class LoginWindow(pyxbmct.AddonDialogWindow):
    """ Login window class """

    def __init__(self, username='', password='', captcha=''):
        """ Class constructor """
        super(LoginWindow, self).__init__()
        self.setGeometry(500, 300, 5, 2)
        self.setWindowTitle(_('Rover.Info login'))
        self.username = username
        self.password = password
        self.captcha_text = ''
        self.login_cancelled = True
        self._captcha = captcha
        self._set_controls()
        self._set_navigation()

    def _set_controls(self):
        """ Set UI controls """
        username_label = pyxbmct.Label(_('Username:'))
        self.placeControl(username_label, 0, 0)
        self._username_entry = pyxbmct.Edit('')
        self.placeControl(self._username_entry, 0, 1)
        self._username_entry.setText(self.username)
        password_label = pyxbmct.Label(_('Password:'))
        self.placeControl(password_label, 1, 0)
        self._password_entry = pyxbmct.Edit('', isPassword=True)
        self.placeControl(self._password_entry, 1, 1)
        self._password_entry.setText(self.password)
        if self._captcha:
            self._captcha_image = pyxbmct.Image(self._captcha)
            self.placeControl(self._captcha_image, 2, 0, rowspan=2)
            captcha_label = pyxbmct.Label(_('Text on the picture:'))
            self.placeControl(captcha_label, 2, 1)
            self._captcha_entry = pyxbmct.Edit('')
            self.placeControl(self._captcha_entry, 3, 1)
        self._cancel_button = pyxbmct.Button(_('Cancel'))
        self.placeControl(self._cancel_button, 4, 0)
        self.connect(self._cancel_button, self.close)
        self._login_button = pyxbmct.Button(_('Login'))
        self.placeControl(self._login_button, 4, 1)
        self.connect(self._login_button, self._login)

    def _set_navigation(self):
        """ Set navigation rules for controls """
        self._username_entry.controlUp(self._login_button)
        self._username_entry.controlDown(self._password_entry)
        self._password_entry.controlUp(self._username_entry)
        if self._captcha:
            self._password_entry.controlDown(self._captcha_entry)
            self._captcha_entry.controlUp(self._password_entry)
            self._captcha_entry.controlDown(self._login_button)
            self._login_button.setNavigation(self._captcha_entry, self._username_entry,
                                             self._cancel_button, self._cancel_button)
            self._cancel_button.setNavigation(self._captcha_entry, self._username_entry,
                                              self._login_button, self._login_button)
        else:
            self._password_entry.controlDown(self._login_button)
            self._login_button.setNavigation(self._password_entry, self._username_entry,
                                             self._cancel_button, self._cancel_button)
            self._cancel_button.setNavigation(self._password_entry, self._username_entry,
                                              self._login_button, self._login_button)
        self.setFocus(self._username_entry)

    def _login(self):
        """ Login user """
        self.login_cancelled = False
        self.username = self._username_entry.getText()
        self.password = self._password_entry.getText()
        if self._captcha:
            self.captcha_text = self._captcha_entry.getText()
        self.close()

    def close(self):
        """ Cancel login """
        if self.login_cancelled:
            self.username = ''
            self.password = ''
            self.captcha_text = ''
        super(LoginWindow, self).close()
