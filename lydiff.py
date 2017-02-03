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
import glob
import subprocess
import yaml
from distutils.spawn import find_executable

def main():

    opt = options()
    versions = Versions(opt.path)
    #print(opt.version)
    print(opt)
    # set all pairs of variables
    inputs = tuple(opt.files)
    inputbases = tuple(f.replace('.ly', '') for f in inputs)
    inputversions = tuple(getfileversion(f) for f in inputs)
    targetversions = list(opt.version)
    for i, ov in enumerate(opt.version):
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
    # default config and config files
    config = {
        'lilypondoptions': [''],
        'path': '/usr/bin ~/opt/*/bin',
        'diff': None,
        'resolution': 200,
    }
    for configfile in ["~/.lydiff"]:
        try:
            with open(os.path.expanduser(configfile)) as f:
                config.update(yaml.load(f))
        except FileNotFoundError:
            pass
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
    parser.add_argument('-v', '--version', type=str, default=[None], nargs='+',
        help='lilypond version to use (default: fromfile [latest])')
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

    # prepare options
    if args.version[0] is None:
        if len(args.files) == 1:
            args.version = ["fromfile", "latest"]
        else:
            args.version = ["fromfile", "fromfile"]
    if len(args.files) == 1:
        args.files *= 2
    if len(args.version) == 1:
        args.version *= 2
    if len(args.lilypondoptions) == 1:
        args.lilypondoptions *= 2
    #if len(args.convert) == 1:
    #    args.convert *= 2
    args.convert = [not args.noconvert] * 2
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


class Versions:
    def __init__(self, paths, search=True):
        self.paths = paths
        self.list = []
        if ' ' in paths:
            self.paths = paths.split()
        if search:
            self._executables()

    def _executables(self):
        """search for executables and fill internal list"""
        pattern = ['%s/lilypond' % p for p in self.paths]
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
            self.list.append((*version, binary))
        self.list.sort()

    def _tuple(self, string):
        return tuple(int(i) for i in string.split("."))

    def _str(self, tup):
        return '.'.join([str(i) for i in tup])

    def __str__(self):
        string = ""
        for version in self.list:
            string += "  %2d.%2d.%2d  %s\n" % version
        return string[:-1]

    @property
    def binaries(self):
        return [v[3] for v in self.list]

    @property
    def versions(self):
        #print(self.list[0][:3])
        return [self._str(v[:3]) for v in self.list]

    def get(self, version, similarfirst=True):
        """algo in 'next', 'previous', 'sameminor' """
        #print(version, self.list)
        if version in self.versions:
            return version, self.binaries[self.versions.index(version)]
        if version == 'latest':
            return self.versions[-1], self.binaries[-1]
        # version not found, looking for best match according to algo
        v = self._tuple(version)
        if v < self.list[0][:3]:
            print("Warning: required version %s is older than any installed version" % version)
            return self.versions[0], self.binaries[0]
        if v > self.list[-1][:3]:
            print("Warning: required version %s is newer than any installed version" % version)
            return self.versions[-1], self.binaries[-1]
        if similarfirst:  # TODO: not implemented
            shortlist = [entry for entry in self.list if entry[:2] == v[:2]]
            for i, available in enumerate(shortlist):
                if available[:3] > v:
                    break
            print("Warning: required version %s is not installed. Using %s instead." % (
                  version, self.versions[i]))
            return self.versions[i], self.binaries[i]

        for i, available in enumerate(self.list):
            if available[:3] > v:
                break
        print("Warning: required version %s is not installed. Using %s instead." % (
              version, self.versions[i]))
        return self.versions[i], self.binaries[i]


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
