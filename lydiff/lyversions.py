#!/usr/bin/env python3

from distutils.spawn import find_executable
import os
import glob
import subprocess

class Versions:
    def __init__(self, paths, search=True):
        if os.pathsep in paths:
            self._paths = paths.split(os.pathsep)
        else:
            self._paths = [paths]
        if search:
            self._list = self._executables()
        else:
            self._list = []

    def _executables(self):
        """search for executables and fill internal list"""

        def release_binary(base):
            """Generate a LilyPond executable name in a binary release directory"""
            return os.path.join(base, 'usr', 'bin', 'lilypond')

        def build_binary(base):
            """Generate a LilyPond executable name in a custom build directory"""
            return os.path.join(base, 'out', 'bin', 'lilypond')

        def package_binary(base):
            """Generate a LilyPond executable name directly in the path"""
            return os.path.join(base, 'lilypond')
            
        result = []
        available_binaries = []
        for p in self._paths:
            # walk over all given paths and their immediate subdirectories,
            # testing each for 'lilypond' executables, both in the place for
            # binary releases and for local builds.
            
            p = os.path.expanduser(p)
            if not os.path.exists(p) and (not os.path.isdir(p)):
                print("Warning: Path {} doesn't point to a directory. Skipping.".format(p))
                continue

            # Create list with path and all its subdirectories (assuming path is
            # either the LilyPond directory itself or a parent directory
            # with multiple installations)
            dirs = [p] + [os.path.join(p, d) for d in os.listdir(p) if os.path.isdir(os.path.join(p, d))]

            for d in dirs:
                binaries = [b for b in [release_binary(d), build_binary(d), package_binary(d)] if os.access(b, os.X_OK)]
                available_binaries.extend(binaries)

        # Retrieve version for each LilyPond binary
        # TODO: Should this be error-checked
        # ('lilypond' might not be a LilyPond executable)?
        for binary in available_binaries:
            version = subprocess.check_output([binary, "--version"])
            version = [int(i) for i in version.split()[2].decode().split('.')]
            result.append((*version, binary))

        result.sort()
        return result

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

