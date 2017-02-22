#!/usr/bin/env python3

from distutils.spawn import find_executable
import os
import glob
import subprocess

class Versions:
    def __init__(self, paths, search=True):
        self._list = []
        if ':' in paths:
            self._paths = paths.split(':')
        else:
            self._paths = [paths]
        if search:
            self._executables()

    def _executables(self):
        """search for executables and fill internal list"""
        pattern = ['%s/lilypond' % p for p in self._paths]
        available_binaries = []

        for p in pattern:
            path = find_executable(p)
            if path:
                available_binaries.append(path)
            else:
                available_binaries += glob.glob(os.path.expanduser(p))
        for binary in available_binaries:
            version = subprocess.check_output([binary, "--version"])
            version = [int(i) for i in version.split()[2].decode().split('.')]
            self._list.append((*version, binary))
        self._list.sort()

    def _tuple(self, string):
        return tuple(int(i) for i in string.split("."))

    def _str(self, tup):
        return '.'.join([str(i) for i in tup])

    def __str__(self):
        string = ""
        for version in self._list:
            string += "  %2d.%2d.%2d  %s\n" % version
        return string[:-1]

    @property
    def binaries(self):
        return [v[3] for v in self._list]

    @property
    def versions(self):
        #print(self._list[0][:3])
        return [self._str(v[:3]) for v in self._list]

    def get(self, version, similarfirst=True):
        """algo in 'next', 'previous', 'sameminor' """
        #print(version, self._list)
        if version in self.versions:
            return version, self.binaries[self.versions.index(version)]
        if version == 'latest':
            return self.versions[-1], self.binaries[-1]
        # version not found, looking for best match according to algo
        v = self._tuple(version)
        if v < self._list[0][:3]:
            print("Warning: required version %s is older than any installed version" % version)
            return self.versions[0], self.binaries[0]
        if v > self._list[-1][:3]:
            print("Warning: required version %s is newer than any installed version" % version)
            return self.versions[-1], self.binaries[-1]
        if similarfirst:  # TODO: not implemented
            shortlist = [entry for entry in self._list if entry[:2] == v[:2]]
            for i, available in enumerate(shortlist):
                if available[:3] > v:
                    break
            print("Warning: required version %s is not installed. Using %s instead." % (
                  version, self.versions[i]))
            return self.versions[i], self.binaries[i]

        for i, available in enumerate(self._list):
            if available[:3] > v:
                break
        print("Warning: required version %s is not installed. Using %s instead." % (
              version, self.versions[i]))
        return self.versions[i], self.binaries[i]

