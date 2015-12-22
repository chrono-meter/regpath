#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
import time

from regpath import *


class Test(unittest.TestCase):
    def test_PurePath_compatiblilty(self):
        # construct and __str__
        self.assertEqual(
            str(RegistryPath(r'HKEY_LOCAL_MACHINE')),
            r'HKEY_LOCAL_MACHINE')
        self.assertEqual(
            str(RegistryPath(r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList')),
            r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList')
        self.assertEqual(
            str(RegistryPath(r'HKEY_LOCAL_MACHINE') / r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList'),
            r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList')
        self.assertEqual(
            str(RegistryPath(
                r'HKEY_CURRENT_USER') / r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList'),
            r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList')
        self.assertEqual(
            str(RegistryPath(
                r'HKEY_LOCAL_MACHINE') / 'SOFTWARE' / 'Microsoft' / 'Windows NT' / 'CurrentVersion' / 'ProfileList'),
            r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList')

        # __eq__
        self.assertEqual(
            RegistryPath(r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList'),
            RegistryPath(
                r'HKEY_CURRENT_USER') / r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList')

        # properties and is_*() functions
        p = RegistryPath(r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList')
        self.assertEqual(p.drive, 'HKEY_LOCAL_MACHINE')
        self.assertEqual(p.root, '\\')
        self.assertEqual(p.anchor, 'HKEY_LOCAL_MACHINE\\')  # anchor == drive + root
        self.assertEqual(p.name, 'ProfileList')
        self.assertEqual(p.suffix, '')
        self.assertListEqual(p.suffixes, [])
        self.assertEqual(p.stem, 'ProfileList')
        self.assertTupleEqual(p.parts, (
            'HKEY_LOCAL_MACHINE\\', 'SOFTWARE', 'Microsoft', 'Windows NT', 'CurrentVersion', 'ProfileList'))
        self.assertEqual(str(p.parent), r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion')
        self.assertListEqual([str(x) for x in p.parents],
                             ['HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion',
                              'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT',
                              'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft', 'HKEY_LOCAL_MACHINE\\SOFTWARE',
                              'HKEY_LOCAL_MACHINE'])
        self.assertTrue(p.is_absolute())
        self.assertFalse(p.is_reserved())
        # TODO: .match()

        with self.assertRaises(NotImplementedError):
            p.as_uri()

    def test_remote(self):
        p = RegistryPath(r'\\computername\HKCU\Software')
        self.assertEqual(str(p), r'\\computername\HKCU\Software')
        self.assertEqual(p.drive, r'\\computername\HKCU')
        self.assertEqual(p.root, '\\')
        self.assertEqual(p.anchor, '\\\\computername\\HKCU\\')  # anchor == drive + root

    def test_dict_interface(self):
        p = RegistryPath(r'HKEY_CLASSES_ROOT\.exe')

        self.assertEqual(str(p), r'HKEY_CLASSES_ROOT\.exe')  # __str__

        self.assertTrue(p.exists())  # exists

        self.assertGreater(len(p), 1)  # __len__

        self.assertIn('', p)  # __contains__

        self.assertTrue(p[''])  # __getitem__

        p = RegistryPath(r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList')
        self.assertEqual(str(p), r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList')
        self.assertTrue(p.exists())

        self.assertIn('ProfilesDirectory', [x for x in p])  # __iter__

        self.assertIn('S-1-5-18', [x.name for x in p.iterdir()])  # iterdir

    def test_types(self):
        p = RegistryPath(r'HKCU\Software\test_%s' % time.time())
        p.mkdir()
        try:
            p['NoneType'] = None
            self.assertEqual(p['NoneType'], None)

            p['StringType'] = 'hello, world'
            self.assertEqual(p['StringType'], 'hello, world')

            p['BytesType'] = b'hello, world'
            self.assertEqual(p['BytesType'], b'hello, world')

            p['IntType'] = 0x12345678
            self.assertEqual(p['IntType'], 0x12345678)

            p['StringListType'] = ['a', 'b', 'c']
            self.assertListEqual(p['StringListType'], ['a', 'b', 'c'])

            p['EnvStringType'] = RegExpandSz('%AppData%\\Python')
            self.assertEqual(p['EnvStringType'], '%AppData%\\Python')
            self.assertIsInstance(p['EnvStringType'], RegExpandSz)

        finally:
            p.rmdir()

    def test_write(self):
        p = RegistryPath(r'HKCU\Software\test_%s' % time.time())
        self.assertFalse(p.handle)
        self.assertFalse(p.exists())
        self.assertFalse(p.handle)

        p.mkdir()
        try:
            self.assertTrue(p.exists())
            self.assertTrue(p.handle)

            p['val'] = 'hello, world'
            self.assertEqual(p['val'], 'hello, world')
            del p['val']
            with self.assertRaises(OSError):
                p['val']

        finally:
            p.rmdir()
            self.assertFalse(p.exists())

    def test_rmtree(self):
        p = RegistryPath(r'HKCU\Software\test_%s' % time.time())
        p.mkdir()
        p['a value'] = 'hello, world'
        (p / 'subkey').mkdir()

        with self.assertRaises(OSError):
            p.rmdir()

        p.rmtree()

        self.assertFalse(p.exists())

    # TODO: CopyTree

    def test_DeleteTree(self):
        p = RegistryPath(r'HKCU\Software\test_%s' % time.time())
        p.mkdir()
        p['a value'] = 'hello, world'
        (p / 'subkey').mkdir()

        p.DeleteTree()
        self.assertTrue(p.exists())

        with self.assertRaises(OSError):
            p['a value']

        self.assertFalse((p / 'subkey').exists())

        p.rmdir()
        self.assertFalse(p.exists())


if __name__ == '__main__':
    unittest.main()
