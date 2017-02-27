#!/usr/bin/env python3

import os

from . import lyversions
from . import equal
from . import getfileversion

# default configuration values and config file
DEFAULT_CONFIG = {
    'lilypondoptions': [''],
    'path': os.pathsep.join(['/usr/bin',
                             '~/opt/*/bin',
                             '~/lilypond']),
    'diff': None,
    'resolution': 200,
}

CONFIG_FILE = "~/.lydiff"

class Options(object):

    def __init__(self):
        self.input_paths = None
        self.input_files = None
        self.input_basenames = None
        self.tmp_files = None
        self.diff_file = None
        self.lily_options = None
        self.commands = None
        self.input_versions = None
        self.target_versions = None
        self.git = None
        self.lily_path = None
        self.lily_versions = None
        self.executables = None
        self.convert_lys = None
        self.diff_tool = None
        self.convert = None
        self.keep_intermediate_files = None
        self.quiet = None
        self.dryrun = None
        self.show_output = None
        self.installed_versions = None
        self._available_versions = None

        self._config = self._init_config()

    def _set_options(self, opt):
        raise NotImplementedError
        
    def _init_config(self):

        config = DEFAULT_CONFIG
        for configfile in [CONFIG_FILE]:
            try:
                import yaml
                with open(os.path.expanduser(configfile)) as f:
                    config.update(yaml.load(f))
            except FileNotFoundError:
                pass
            except ImportError:
                raise Exception("Module pyyaml dependency is not satisfied. " +
                    "Please install using 'pip' or your operating system's package manager")
        for k, v in config.items():
            if k not in ['path', 'diff', 'resolution'] and not isinstance(v, list):
                config[k] = [v, v]

        return config

    def _set_options(self, opt):

        # only show installed versions
        if opt.installed_versions:
            self.installed_versions = True
            self.lily_path = opt.path
            return

        # input files
        self.input_paths, self.input_files, self.input_basenames = self.get_paths_and_files(opt.files)

        # LilyPond versions
        self.input_versions = tuple(getfileversion(f) for f in self.input_files)
        self.lily_path = opt.path
        self.target_versions = self.get_target_versions(opt.versions, self.available_versions)
        self.lily_versions, self.executables = self.get_exe_versions(self.target_versions, self.available_versions)

        # temp and output files
        self.convert_lys = tuple(os.path.join(os.path.dirname(exe), 'convert-ly') for exe in self.executables)    
        self.tmp_files = tuple('tmp-%s-%s' % (b, v) for b, v in zip(self.input_basenames, self.lily_versions))
        diff_file = opt.output
        if diff_file is None:
            if equal(self.input_files):
                diff_file = 'diff_%s_%s-%s' % (self.input_basenames[0], *self.lily_versions)
            elif equal(target_versions):
                diff_file = 'diff_%s-%s_%s' % (*self.input_basenames, self.lily_versions[0])
            else:
                diff_file = 'diff_%s-%s_%s-%s' % (*self.input_basenames, *self.lily_versions)
        self.diff_file = diff_file

        # Git configuration
        if opt.git is not None:
            if not opt.git:
                # No argument given: default for both
                opt.git = ['HEAD', 'index']
            elif len(opt.git) == 1:
                # One argument given: default for second only
                opt.git.append('index')
            self.git = tuple([opt.git[0], opt.git[1]])

        # LilyPond command line
        self.lily_options = [l.replace('~', os.path.expanduser('~')) for l in opt.lilypondoptions]
        self.commands = tuple(
            [[self.executables[i]] +
             self.lily_options[i].split() +
             ['--png',
              '-dresolution=%d' % opt.resolution,
              '-danti-alias-factor=2',
              '-o',
              os.path.join(self.input_paths[i], self.tmp_files[i]),
              os.path.join(self.input_paths[i], self.tmp_files[i] + '.ly')]
              for i in [0, 1]]
        )

        self.convert = opt.convert
        self.keep_intermediate_files = opt.keep_intermediate_files
        self.quiet = opt.quiet
        self.dryrun = opt.dryrun
        self.show_output = opt.showoutput
        self.diff_tool = opt.diff

        
    def validate_files(self, files):
        """Check for validity of file argument(s)"""
        if len(files) == 1:
            files *= 2
        elif len(files) > 2:
            raise Exception("Please specify one or two input files")
        for f in files:
            if not os.path.exists(f):
                raise Exception("File not found: {}".format(f))
        return files

    def validate_versions(self, versions, files):
        """Check for validity of version argument(s)"""
        if len(versions) > 2:
            raise Exception("Please specify one or two LilyPond versions")
        if len(versions) == 1:
            versions *= 2
        if versions[0] is None:
            # no versions are given, take from file(s)
            if files[0] == files[1]:
                # only one file, default: compare original to latest version
                versions = ["fromfile", "latest"]
            else:
                versions = ["fromfile", "fromfile"]
        return versions

    def validate_lilypond_options(self, options):
        """Check for validity of LilyPond option(s) argument(s)"""
        # TODO: This is incomplete, some checks for the -dsomething options
        # have to be implemented.
        if len(options) == 1:
             options *= 2
        elif len(options) > 2:
            raise Exception("Please specify onr or two sets of LilyPond options")
        return options

    def get_paths_and_files(self, input_files):
        current_dir = os.getcwd()
        paths = []
        files = []
        basenames = []
        for i in [0, 1]:
            real_path = os.path.normpath(os.path.realpath(os.path.join(current_dir, input_files[i])))
            paths.append(os.path.dirname(real_path))
            files.append(real_path)
            basenames.append(os.path.splitext(os.path.basename(real_path))[0])
        return (tuple(paths), tuple(files), tuple(basenames))
        
    def get_file_version(self, filename):
        version = None
        with open(filename) as f:
            for line in f:
                if r'\version' in line:
                    _, version, _ = line.split('"', 2)
                    break
        return version

    def get_target_versions(self, versions, av):
        result = versions
        for i, ov in enumerate(versions):
            if ov == 'fromfile':
                result[i] = self.input_versions[i]
            elif ov == 'latest':
                result[i] = av.get(ov)[0]
        return tuple(result)

    def get_exe_versions(self, tv, av):
        versions = [self.available_versions.get(v) for v in self.target_versions]
        exe_versions = (versions[0][0], versions[1][0])
        binaries =  (versions[0][1], versions[1][1])
        return (exe_versions, binaries)

    @property
    def available_versions(self):
        if not self._available_versions:
            self._available_versions = lyversions.Versions(self.lily_path)
        return self._available_versions

