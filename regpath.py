#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""regpath - pathlib and winreg
"""
import pathlib
import collections.abc
import winreg
import ctypes
import ctypes.wintypes

__version__ = '0.1.0'
__author__ = __author_email__ = 'chrono-meter@gmx.net'
__license__ = 'PSF'
__url__ = 'https://github.com/chrono-meter/regpath'
__download_url__ = 'http://pypi.python.org/pypi/regpath'
# http://pypi.python.org/pypi?%3Aaction=list_classifiers
__classifiers__ = [
    'Development Status :: 4 - Beta',
    'Environment :: Win32 (MS Windows)',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Python Software Foundation License',
    'Operating System :: Microsoft :: Windows',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Topic :: Software Development :: Libraries :: Python Modules',
]
__all__ = 'RegistryPath', 'RegExpandSz'


STANDARD_RIGHTS_READ = 0x20000
STANDARD_RIGHTS_WRITE = 0x20000


class RegExpandSz(str):
    def _get_regvalue(self):
        return self, winreg.REG_EXPAND_SZ


# TODO: REG_LINK
# class RegLink(str):
#     def _get_regvalue(self):
#         return self, winreg.REG_LINK


class _RegistryFlavour(pathlib._WindowsFlavour):
    reserved_names = ()
    rootkey_map = {
        'HKEY_CLASSES_ROOT': winreg.HKEY_CLASSES_ROOT,
        'HKCR': winreg.HKEY_CLASSES_ROOT,
        'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER,
        'HKCU': winreg.HKEY_CURRENT_USER,
        'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE,
        'HKLM': winreg.HKEY_LOCAL_MACHINE,
        'HKEY_USERS': winreg.HKEY_USERS,
        'HKU': winreg.HKEY_USERS,
        'HKEY_PERFORMANCE_DATA': winreg.HKEY_PERFORMANCE_DATA,
        'HKEY_CURRENT_CONFIG': winreg.HKEY_CURRENT_CONFIG,
        'HKCC': winreg.HKEY_CURRENT_CONFIG,
        'HKEY_DYN_DATA': winreg.HKEY_DYN_DATA,
    }

    def splitroot(self, part, sep=pathlib._WindowsFlavour.sep):
        drv, root, part = super().splitroot(part, sep=sep)

        if drv.startswith('\\\\'):
            pass

        elif part.split(self.sep, 1)[0].upper() in self.rootkey_map:
            if self.sep in part:
                drv, part = part.split(self.sep, 1)
                root = self.sep
            else:
                drv, part = part, ''

        return drv, root, part

    def join_parsed_parts(self, drv, root, parts, drv2, root2, parts2):
        if drv2:
            return drv2, root2, parts2
        else:
            if not root and parts2:
                root = self.sep
            return drv, root, parts + parts2

    def make_uri(self, path):
        # In PowerShell: Registry::HKEY_CURRENT_USER\Software\Microsoft\Notepad
        #                URI cannot include value name.
        raise NotImplementedError

    def gethomedir(self, username):
        return 'HKEY_CURRENT_USER'


class RegistryPath(pathlib.PureWindowsPath, collections.abc.MutableMapping):
    _flavour = _RegistryFlavour()
    _root_key = None
    handle = None
    handle_access = 0
    _typemap = {
        winreg.REG_EXPAND_SZ: RegExpandSz,
        # winreg.REG_LINK: RegLink,
    }

    @classmethod
    def _from_parsed_parts(cls, drv, root, parts, init=True):
        if len(parts) == 1:
            root = ''
            parts = [drv + root]
        return super()._from_parsed_parts(drv, root, parts, init=True)

    @property
    def root_key(self):
        if self._root_key is None:
            if self._drv.startswith('\\\\'):
                computer, key = self._drv.rsplit('\\', 1)
                self._root_key = winreg.ConnectRegistry(computer, self._flavour.rootkey_map[key.upper()])
            else:
                self._root_key = self._flavour.rootkey_map[self._drv.upper()]
        return self._root_key

    @property
    def path(self):
        return self._flavour.join(self.parts[1:])

    def open(self, access=winreg.KEY_READ):
        if not self.handle or (access & self.handle_access) != access:
            if access & (winreg.KEY_SET_VALUE | winreg.KEY_CREATE_SUB_KEY):
                self.handle = self.CreateKeyEx(access=access)
            else:
                self.handle = self.OpenKeyEx(access=access)

            self.handle_access = access

        return self.handle

    def close(self):
        if self.handle:
            self.handle.Close()
        self.handle = None
        self.handle_access = 0

    #
    # winreg interface
    #

    # ConnectRegistry(computer_name, key)

    def CreateKey(self):
        return winreg.CreateKey(self.root_key, self.path)

    def CreateKeyEx(self, reserved=0, access=winreg.KEY_WRITE):
        return winreg.CreateKeyEx(self.root_key, self.path, reserved, access)

    def DeleteKey(self):
        self.open(access=winreg.KEY_WRITE)
        return winreg.DeleteKey(self.handle, '')

    def DeleteKeyEx(self, access=winreg.KEY_WOW64_64KEY, reserved=0):
        self.open(access=winreg.KEY_WRITE)
        return winreg.DeleteKeyEx(self.handle, '', access, reserved)

    def DeleteValue(self, value):
        self.open(access=winreg.KEY_WRITE)
        return winreg.DeleteValue(self.handle, value)

    def EnumKey(self):
        """Iterate sub-key names.
        """
        self.open()
        number_of_sub_keys, number_of_values, last_modified = winreg.QueryInfoKey(self.handle)
        for i in range(number_of_sub_keys):
            yield winreg.EnumKey(self.handle, i)

    def EnumValue(self):
        """Iterate (value name, value data, value type).
        Note that `EnumValue` returns unnamed value's name when unnamed value is set.
        """
        self.open()
        number_of_sub_keys, number_of_values, last_modified = winreg.QueryInfoKey(self.handle)
        for i in range(number_of_values):
            yield winreg.EnumValue(self.handle, i)

    def FlushKey(self):
        if self.handle:
            winreg.FlushKey(self.handle)

    def LoadKey(self, file_name):
        self.open(access=winreg.KEY_WRITE)
        return winreg.LoadKey(self.handle, None, str(file_name))

    def OpenKey(self, reserved=0, access=winreg.KEY_READ):
        return winreg.OpenKey(self.root_key, self.path, reserved, access)

    def OpenKeyEx(self, reserved=0, access=winreg.KEY_READ):
        return winreg.OpenKeyEx(self.root_key, self.path, reserved, access)

    def QueryInfoKey(self):
        self.open()
        return winreg.QueryInfoKey(self.handle)

    def QueryValue(self):
        self.open()
        return winreg.QueryValue(self.handle, None)

    def QueryValueEx(self, value_name):
        self.open()
        return winreg.QueryValueEx(self.handle, value_name)

    def SaveKey(self, file_name):
        self.open(access=winreg.KEY_WRITE)
        return winreg.SaveKey(self.handle, str(file_name))

    def SetValue(self, type, value):
        self.open(access=winreg.KEY_WRITE)
        return winreg.SetValue(self.handle, None, type, value)

    def SetValueEx(self, value_name, reserved, type, value):
        self.open(access=winreg.KEY_WRITE)
        return winreg.SetValueEx(self.handle, value_name, reserved, type, value)

    # DisableReflectionKey(key)
    # EnableReflectionKey(key)
    # QueryReflectionKey(key)

    #
    # Win32API interface
    #

    def CopyTree(self, dest):
        assert isinstance(dest, type(self))
        self.open(access=winreg.KEY_WRITE)
        dest.open(access=winreg.KEY_WRITE)
        result = ctypes.windll.advapi32.RegCopyTreeW(int(self.handle), None, int(dest.handle))
        if result != 0:
            raise ctypes.WinError(result)
        return result

    def DeleteTree(self):
        """Deletes the subkeys and values of the specified key recursively.
        """
        self.open(access=winreg.KEY_ALL_ACCESS)
        result = ctypes.windll.advapi32.RegDeleteTreeW(int(self.handle), None)
        if result != 0:
            raise ctypes.WinError(result)
        return result

    #
    # pathlib.Path like interface
    #

    def exists(self):
        """Whether this path exists.
        """
        try:
            self.OpenKeyEx(access=STANDARD_RIGHTS_READ)
        except OSError:
            return False
        else:
            return True

    def mkdir(self, access=winreg.KEY_WRITE, parents=False):
        """Make this key.
        """
        # if not exist_ok and self.exists():
        #     raise FileExistsError(str(self))

        if parents and not self.parent.exists():
            self.parent.mkdir(parents=parents)

        self.open(access=access)

    def iterdir(self):
        """Iterate sub-keys.
        """
        for name in self.EnumKey():
            yield self / name

    def rmdir(self):
        """Remove this key.
        """
        self.DeleteKey()
        self.close()

    #
    # shutil like interface
    #

    copytree = CopyTree

    def rmtree(self):
        for child in self.iterdir():
            child.rmtree()
        self.rmdir()

    #
    # dict interface (collections.abc.MutableMapping)
    #
    def __contains__(self, name):
        try:
            self.QueryValueEx(name)
        except FileNotFoundError:
            return False
        else:
            return True

    def __iter__(self):
        for name, value, type in self.EnumValue():
            yield name

    def __len__(self):
        return self.QueryInfoKey()[1]

    def __getitem__(self, name):
        value, type = self.QueryValueEx(name)

        if type in self._typemap:
            value = self._typemap[type](value)

        return value

    def __setitem__(self, name, value):
        if hasattr(value, '_get_regvalue'):
            value, type = value._get_regvalue()
        elif isinstance(value, str):
            type = winreg.REG_SZ
        elif isinstance(value, bytes):
            type = winreg.REG_BINARY
        elif isinstance(value, int):
            if value < 0:
                raise ValueError('non negative number')
            elif value <= 0xFFFFFFFF:
                type = winreg.REG_DWORD
            else:
                raise NotImplementedError('REG_QWORD')
                # type = 11  # winreg.REG_QWORD
        elif isinstance(value, list):
            type = winreg.REG_MULTI_SZ
        elif value is None:
            type = winreg.REG_NONE
        else:
            raise TypeError(value)

        self.SetValueEx(name, 0, type, value)

    def __delitem__(self, name):
        self.DeleteValue(name)
