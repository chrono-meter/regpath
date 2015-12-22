regpath - pathlib and winreg
============================

Dependencies
------------

* Python 3.4, 3.5
* `pathlib <https://pypi.python.org/pypi/pathlib>`_ (Standard library in Python 3.4)


Install
-------

``pip install regpath``


Examples
--------

Import::

    >>> from regpath import URL

Create object::

    >>> p = RegistryPath('HKCU')

Access PurePath compaitble propertyes::

    >>> p
    RegistryPath('HKCU')
    >>> print(p)
    HKCU
    >>> p.drive, p.root, p.parts
    ('HKCU', '', ('HKCU',))

List keys::

    >>> list(p.iterdir())
    [RegistryPath('HKCU/AppEvents'), RegistryPath('HKCU/AppXBackupContentType'), RegistryPath('HKCU/Console'),
     RegistryPath('HKCU/Control Panel'), RegistryPath('HKCU/Environment'), RegistryPath('HKCU/EUDC'),
     RegistryPath('HKCU/Keyboard Layout'), RegistryPath('HKCU/Network'), RegistryPath('HKCU/Printers'),
     RegistryPath('HKCU/Software'), RegistryPath('HKCU/System'), RegistryPath('HKCU/Volatile Environment')]

Join path::

    >>> p = p / 'Environment'
    >>> p
    RegistryPath('HKCU/Environment')
    >>> print(p)
    HKCU\Environment
    >>> p.drive, p.root, p.parts
    ('HKCU', '\\', ('HKCU', 'Environment'))

List values::

    >>> list(p)
    ['TEMP', 'TMP']
    >>> p['Temp']
    '%USERPROFILE%\\AppData\\Local\\Temp'

Then::

    >>> p = RegistryPath(r'HKCU\Software\{d017c5cb-d6a6-453e-b41a-f3dc270628c0}\subkey')

    >>> p.exists()
    False
    >>> p.mkdir(parents=True)
    >>> p.exists()
    True

    >>> list(p)
    []
    >>> p[''] = 'This is unnamed value.'
    >>> list(p)
    ['']
    >>> p['']
    'This is unnamed value.'
    >>> p['number'] = 0x12345678
    >>> p['number']
    305419896
    >>> list(p)
    ['', 'number']
    >>> del p['number']
    >>> list(p)
    ['']
    >>> del p['']
    >>> list(p)
    []

    >>> p['msg'] = 'hello, world'
    >>> p.parent.rmdir()
    Traceback (most recent call last):
    ...
    PermissionError: [WinError 5] Access is denied.

    >>> p.parent.rmtree()
    >>> p.parent.exists()
    False
    >>> p.exists()
    False
    >>> list(p)
    Traceback (most recent call last):
    ...
    OSError: [WinError 1018] Illegal operation attempted on a Registry key which has been marked for deletion.
