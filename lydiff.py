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

from lydiff.lyversions import Versions

def main():

    try:
        opt = options()
    except Exception as e:
        print()
        print(e)
        exit(1)
    versions = Versions(opt.path)
    #print(opt.versions)
    print(opt)
    # set all pairs of variables
    inputs = tuple(opt.files)
    inputbases = tuple(os.path.splitext(f)[0] for f in inputs)
    inputversions = tuple(getfileversion(f) for f in inputs)
    targetversions = list(opt.versions)
    for i, ov in enumerate(opt.versions):
        if ov == 'fromfile':
            targetversions[i] = inputversions[i]
        elif ov == 'latest':
            targetversions[i] = versions.get(ov)[0]
    targetversions = tuple(targetversions)
    exeversions = tuple(versions.get(v)[0] for v in targetversions)
    executables = tuple(versions.get(v)[1] for v in targetversions)
    convertlys = tuple(exe[:-8] + 'convert-ly' for exe in executables)
    converted = tuple('tmp-%s-%s.ly' % (b, v) for b, v in zip(inputbases, exeversions))
    for i in [0, 1]:
        if targetversions[i] != exeversions[i] and targetversions[i] != 'latest':
            print("Warning: LilyPond %s is not available. File %d %r will be run using version %s instead." %
                  (targetversions[i], i+1, inputs[i], exeversions[i]))
    images = tuple(f.replace('.ly', '.png') for f in converted)
    npages = []
    if opt.output is None:
        if equal(inputs):
            opt.output = 'diff_%s_%s-%s.png' % (inputbases[0], *exeversions)
        elif equal(targetversions):
            opt.output = 'diff_%s-%s_%s.png' % (*inputbases, exeversions[0])
        else:
            opt.output = 'diff_%s-%s_%s-%s.png' % (*inputbases, *exeversions)

    # check
    if equal(inputs) and equal(targetversions) and equal(opt.convert):
        print("Warning: Equal inputs won't generate differences")

    if not opt.quiet:
        print("Running this:   ___ 1 _______________     ___ 2 _______________")
        print("Files:      %25s %25s" % tuple("%s (%s)" % (i, v) for i, v in zip(inputs, inputversions)))
        #print("convert:    %25s %25s" % tuple(['no', 'yes'][int(b)] for b in opt.convert))
        print("target version: %21s %25s" % targetversions)
        print("convert-ly: %25s %25s" % convertlys)
        print("converted:  %25s %25s" % converted)
        print("executable: %25s %25s" % executables)
        print("images:     %25s %25s" % images)
        print("output:     %45s" % opt.output)
    i = [l.replace('~', os.path.expanduser('~')) for l in opt.lilypondoptions]

    cmd = (
        [executables[0]] + i[0].split() + ['--png', '-dresolution=%d' % opt.resolution, '-danti-alias-factor=2', '-o', images[0][:-4], converted[0]],
        [executables[1]] + i[1].split() + ['--png', '-dresolution=%d' % opt.resolution, '-danti-alias-factor=2', '-o', images[1][:-4], converted[1]],
    )

    if not opt.quiet:
        print("Run tools ... ", end='', flush=True)
    if opt.dryrun or opt.showoutput:
        print()
    if opt.convert[0]:
        runconvert(convertlys[0], inputs[0], converted[0], opt.dryrun, opt.showoutput)
    if opt.convert[1]:
        runconvert(convertlys[1], inputs[1], converted[1], opt.dryrun, opt.showoutput)
    runlily(cmd[0], opt.dryrun, opt.showoutput)
    runlily(cmd[1], opt.dryrun, opt.showoutput)
    if opt.showoutput:
        print('-'*48)
    ret = compare(images, opt.output, opt.dryrun)
    if not opt.quiet:
        print('done')
    print('Outputs', ['differ', 'are identical'][int(ret)])
    if opt.diff is not None:
        difftool(opt.diff, converted, opt.dryrun)
    return not ret

def equal(pair):
    return pair[0] == pair[1]


def difftool(tool, files, dry):
    if dry:
        print('- Run diff:    ', tool, *files)
    else:
        if tool.startswith('diff'):
            print('-'*48)
            print('diff:')
        subprocess.call([*tool.split(), *files])


def runconvert(convert, filein, fileout, dry, show):
    cmd = [convert, '-c', filein]
    if dry:
        print("- Run convert: ", ' '.join(cmd), '>', fileout)
    else:
        with open(fileout, 'w') as f:
            if show:
                print('-'*48)
                subprocess.call(cmd, stdout=f)
            else:
                subprocess.call(cmd, stdout=f, stderr=subprocess.DEVNULL)


def getfileversion(file):
    version = None
    with open(file) as f:
        for line in f:
            if r'\version' in line:
                _, version, _ = line.split('"', 2)
                break
    return version


def options():
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
                                 '~/lilypond/usr/bin']),
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

    #if len(args.convert) == 1:
    #    args.convert *= 2
    args.convert = [not args.noconvert] * 2
    # why do you name the option "test" when you *use* it only as "dryrun"?
    # if this is only for the option letter I strongly suggest to reconsider
    # the issue. Suggestion:
    # - don't offer the '-d' short option for either --diff or --dryrun
    args.dryrun = args.test

    return args


def runlily(cmd, dry, show):
    if dry:
        print('- Run LilyPond:', ' '.join(cmd))
    elif show:
        print('-'*48)
        subprocess.call(cmd)
    else:
        subprocess.call(cmd, stderr=subprocess.DEVNULL)


def compare(images, output, dry):
    cmd = ['convert', *reversed(images),
           '-channel', 'red,green', '-background', 'black',
           '-combine', '-fill', 'white', '-draw', "color 0,0 replace", output]
    comp = ['compare', '-metric', 'AE', *images, 'null:']
    if dry:
        print('- Run compare: ', ' '.join([repr(s) if ' ' in s else s for s in cmd]))
        print('- Run compare: ', ' '.join(comp))
        return True

    subprocess.call(cmd)
    process = subprocess.Popen(comp, stderr=subprocess.PIPE)
    _, npixels = process.communicate()
    #print(_, int(npixels))
    return int(npixels) == 0



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
