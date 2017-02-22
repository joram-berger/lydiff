#!/usr/bin/env python3
"""
Program `lydiff`
© 2017 Joram Berger
License: GPL3+

Usage examples:
1 .ly, 2 bin
 lydiff file.ly -l lilypond /my/other/lilypond -o diff_file.png

1 .ly, 2 versionen, viele bins
 lydiff file.ly
 lydiff file.ly -v 2.18.0 2.19.50 [--convert] -i /my/paths  -o diff_file_2-18-0_2-19-50.png
2 .ly, 1 bin/1 version
 lydiff file1.ly file2.ly -l lilypond
3 .ly, -g commit1 commit2 -l lilypond
 lydiff file.ly -g a677be ffe523

"""
import argparse
import os
import subprocess

import lydiff
from lydiff.lyversions import Versions

def main():

    try:
        cli_opts = cli_options()
        available_versions = Versions(cli_opts.path)
    except Exception as e:
        print()
        print(e)
        exit(1)

    cli_opts.available_versions = available_versions
    opt = lydiff.configure(cli_opts)

    # make options available as local variables
    input_files = opt['input_files']
    input_versions = opt['input_versions']
    target_versions = opt['target_versions']
    lily_versions = opt['lily_versions']
    executables = opt['executables']
    convert_lys = opt['convert_lys']
    tmp_files = opt['tmp_files']
    image_files = opt['image_files']
    diff_file = opt['diff_file']
    diff_tool = opt['diff_tool']
    quiet = opt['quiet']
    dryrun = opt['dryrun']
    convert = opt['convert']
    show_output = opt['show_output']
    commands = opt['commands']

    # plausibility checks    
    if lydiff.equal(input_files) and lydiff.equal(target_versions) and lydiff.equal(opt.convert):
        print("Warning: Equal input_files won't generate differences")

    for i in [0, 1]:
        if target_versions[i] != lily_versions[i] and target_versions[i] != 'latest':
            print("Warning: LilyPond %s is not available. File %d %r will be run using version %s instead." %
                  (target_versions[i], i+1, input_files[i], lily_versions[i]))
    
    if not quiet:
        print_report(opt)

    # compile the scores
    if dryrun or show_output:
        print()
    for i in [0, 1]:
        if convert[i]:
            lydiff.runconvert(convert_lys[i], input_files[i], tmp_files[i], dryrun, show_output)
        lydiff.runlily(commands[i], dryrun, show_output)

    # perform comparison
    if show_output:
        print('-'*48)
    ret = lydiff.compare(image_files, diff_file, dryrun)
    if not quiet:
        print('done')
    print('Outputs', ['differ', 'are identical'][int(ret)])
    if diff_tool is not None:
        lydiff.difftool(diff_tool, tmp_files, dryrun)
    return not ret



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


def print_report(opt):
    print("Running this:   ___ 1 _______________     ___ 2 _______________")
    print("Files:      %25s %25s" % tuple("%s (%s)" % (i, v) for i, v in zip(opt['input_files'], opt['input_versions'])))
    #print("convert:    %25s %25s" % tuple(['no', 'yes'][int(b)] for b in opt.convert))
    print("target version: %21s %25s" % opt['target_versions'])
    print("convert-ly: %25s %25s" % opt['convert_lys'])
    print("tmp_files:  %25s %25s" % opt['tmp_files'])
    print("executable: %25s %25s" % opt['executables'])
    print("images:     %25s %25s" % opt['image_files'])
    print("output:     %45s" % opt['diff_file'])
    print("Run tools ... ", end='', flush=True)

if __name__ == "__main__":
    exit(main())
    vv = Versions("/usr/bin ~/Technik/sw/ly/*/bin")
    #print(vv)
    #print(vv.get("2.18.0"))
    #print(vv.get("2.18.5"))
    #print(vv.get("2.19.53"))
    #print(vv.get("2.20.0"))
    #comp = ['compare', '-metric', 'AE', 'tmp-test3-2.18.2.png', 'tmp-test3-2.19.53.png', 'null:']
    #subprocess.call(comp)
    #import subprocess
