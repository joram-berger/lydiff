#!/usr/bin/env python3

import os
import argparse

def cli_options():
    """Read options from config file and commandline"""

    def validate_files(files):
        """Check for validity of file argument(s)"""
        if len(files) == 1:
            files *= 2
        elif len(files) > 2:
            raise Exception("Please specify one or two input files")
        for f in files:
            if not os.path.exists(f):
                raise Exception("File not found: {}".format(f))
        return files

    def validate_versions(versions, files):
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

    def validate_lilypond_options(options):
        """Check for validity of LilyPond option(s) argument(s)"""
        # TODO: This is incomplete, some checks for the -dsomething options
        # have to be implemented.
        if len(options) == 1:
             options *= 2
        elif len(options) > 2:
            raise Exception("Please specify onr or two sets of LilyPond options")
        return options

    # default config and config files
    config = {
        'lilypondoptions': [''],
        'path': os.pathsep.join(['/usr/bin',
                                 '~/opt/*/bin',
                                 '~/lilypond']),
        'diff': None,
        'resolution': 200,
    }
    for configfile in ["~/.lydiff"]:
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

    # commandline options
    parser = argparse.ArgumentParser(description='Diff LilyPond scores')
    parser.add_argument('files', metavar='files', type=str, nargs='+',
        help='files to diff')
    parser.add_argument('-n', '--noconvert', action="store_true",
        help='Do not run convert-ly to update the input file to the required '
        'lilypond version')
    parser.add_argument('-v', '--versions', type=str, default=[None], nargs='+',
        help='lilypond version(s) to use (default: fromfile [latest])')
    parser.add_argument('-o', '--output', type=str, default=None,
        help='output file name (default: diff_<file1>-<file2>.png)')
    parser.add_argument('-l', '--lilypondoptions', type=str, nargs='+',
        default=config['lilypondoptions'],
        help='additional command line options for lilypond')
    parser.add_argument('-t', '--test', action='store_true',
        help='Do not generate files just print the actions')
    parser.add_argument('-k', '--keep-intermediate-files', action='store_true',
        help='Keep intermediate files instead of removing them')
    parser.add_argument('-d', '--diff', type=str, default=config['diff'],
        help="diff the converted inputs using diff (diff or meld)")
    parser.add_argument('-s', '--showoutput', action='store_true',
        help='show stdout of tools in use')
    parser.add_argument('-q', '--quiet', action='store_true',
        help='Do not show information')
    parser.add_argument('-p', '--path', type=str, default=config['path'],
        help="Search path for lilypond executables")
    parser.add_argument('-r', '--resolution', type=int, default=config['resolution'],
                        help="Resolution of the output image in dpi")
    # parser.add_argument('-g', '--git', type=str, nargs=2, default=[None, None],
    #                     help="compare file in different git revisions")
    args = parser.parse_args()

    # validate options
    args.files = validate_files(args.files)
    args.versions = validate_versions(args.versions, args.files)
    args.lilypondoptions = validate_lilypond_options(args.lilypondoptions)
    # TODO: Discuss whether a way to use "convert" 
    args.convert = [not args.noconvert] * 2

    # why do you name the option "test" when you *use* it only as "dryrun"?
    # if this is only for the option letter I strongly suggest to reconsider
    # the issue. Suggestion:
    # - don't offer the '-d' short option for either --diff or --dryrun
    args.dryrun = args.test

    return args

