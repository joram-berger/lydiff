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
from distutils.spawn import find_executable

def main():
    #print("Start")
    #v = Version("2.22.2")
    #w = Version((2, 23, 4))
    #print(v)
    #print(w)
    # read options
    opt = options()
    # mode
    ll = opt.path
    # prepare
    # files

    #print(opt)
    assert len(opt.files) == 2
    inputs = tuple(opt.files)
    inputbases = tuple(f.replace('.ly', '') for f in inputs)
    inputversions = tuple(getfileversion(f) for f in inputs)

    targetversions = list(opt.version)
    for i, ov in enumerate(opt.version):
        if ov == 'fromfile':
            targetversions[i] = inputversions[i]
    targetversions = tuple(targetversions)
    exeversions = tuple(['.'.join([str(i) for i in list(findexec(ll, v)[1])]) for v in targetversions])
    executables = tuple(findexec(ll, v)[0] for v in targetversions)
    convertlys = tuple(exe[:-8] + 'convert-ly' for exe in executables)
    converted = tuple('tmp-' + i.replace('.ly', '-%s.ly' % v) for i, v in zip(inputs, exeversions))
    for i in [0, 1]:
        if targetversions[i] != exeversions[i]:
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

    print("Running this:                  side 1                    side 2:")
    print("Files:      %25s %25s" % inputs)
    print("in version: %25s %25s" % inputversions)
    print("convert:    %25s %25s" % tuple(['no', 'yes'][int(b)] for b in opt.convert))
    print("target ver: %25s %25s" % targetversions)
    print("to version: %25s %25s" % exeversions)
    print("convert-ly: %25s %25s" % convertlys)
    print("converted:  %25s %25s" % converted)
    print("executable: %25s %25s" % executables)
    print("images:     %25s %25s" % images)
    print("output:     %45s" % opt.output)
    i = [l.replace('~', os.path.expanduser('~')) for l in opt.lilypondoptions]

    cmd = (
        [executables[0]] + i[0].split() + ['--png', '-o', images[0][:-4], converted[0]],
        [executables[1]] + i[1].split() + ['--png', '-o', images[1][:-4], converted[1]],
    )
    # conversions


    # binaries

    # run convert-ly

    #if opt.convert:
    #    runconvert(inputs, exeversions)

    # run lily

    # compare
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
    compare(images, opt.output, opt.dryrun)
    print('done')
    if opt.diff is not None:
        difftool(opt.diff, converted, opt.dryrun)


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


class Version(tuple):
    def __init__(self, init):
        print("I", init)
        if isinstance(init, str):
            print( init, init.split('.'))
            t = tuple(int(i) for i in init.split('.'))
            print(t)
            self = t
        elif isinstance(init, tuple):
            self = init
        else:
            print("ERROR:", init)
        print("S", self, len(self))
    def __str__(self):
        print("P", len(self), type(self), type(self[1]))
        return '.'.join([str(i) for i in list(self)])
    def __repr__(self):
        return str(self)

def getfileversion(file):
    version = None
    with open(file) as f:
        for line in f:
            if r'\version' in line:
                _, version, _ = line.split('"', 2)
                break
    return version

def options():
    """
       file(s)
    -o diff_f1_f2.png
    -l lilyversions
    -i installpaths
      lyoptions
    -h
    -v "fromfile fromfile"

    ly > convert > run > png (x2)
    """
    parser = argparse.ArgumentParser(description='Diff LilyPond scores')
    parser.add_argument('files', metavar='files', type=str, nargs='+',
        help='files to diff')
    parser.add_argument('-n', '--noconvert', action="store_true",
        help='Do not run convert-ly to update the input file to the required lilypond version')
    parser.add_argument('-v', '--version', type=str, default=['fromfile'], nargs='+',
        help='lilypond version to use (default: fromfile)')
    parser.add_argument('-o', '--output', type=str, default=None,
        help='output file name (default: diff_<file1>-<file2>.png)')
    parser.add_argument('-l', '--lilypondoptions', type=str, nargs='+',
                        help='additional command line options for lilypond')
    parser.add_argument('-t', '--test', action='store_true',
        help='Do not generate files just print the actions')
    parser.add_argument('-d', '--diff', type=str, default=None,
                        help="diff the converted inputs using diff (diff or meld)")
    parser.add_argument('-s', '--showoutput', action='store_true',
                        help='show stdout of tools in use')
    parser.add_argument('-p', '--path', type=str, default='/usr/bin ~/opt/*/bin',
                        help="Search path for lilypond executables")
    # parser.add_argument('-g', '--git', type=str, nargs=2, default=[None, None],
    #                     help="compare file in different git revisions")
    args = parser.parse_args()
    #print(args)

    # prepare options
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
    if dry:
        print('- Run compare: ', ' '.join([repr(s) if ' ' in s else s for s in cmd]))
    else:
        subprocess.call(cmd)

def findexec(pattern, version):
    """Find lilypond binary with minimum version

    Find the lilypond binary which matches the pattern and has at least the
    required version."""
    available_binaries = []
    lst = [int(i) for i in version.split('.')] + ['required version']
    lst = [tuple(lst)]
    pattern = ['%s/lilypond' % p for p in pattern.split()]
    #print(lst)
    for p in pattern:
        path = find_executable(p)
        #print(p, path)
        if path:
            available_binaries.append(path)
        else:
            available_binaries += glob.glob(os.path.expanduser(p))
    for binary in available_binaries:
        #print(binary)
        version = subprocess.check_output([binary, "--version"])
        version = [int(i) for i in version.split()[2].decode().split('.')]
        lst.append((*version, binary))
    lst.sort()
    now = False
    for l in lst:
        if l[3] == 'required version':
            now = True
            continue
        #print("  %s" % ' *'[bool(now is True)], end='')
        #print("%2d.%2d.%2d  %s" % l)
        if now is True:
            now = l[3]
            ver = l[:3]

    if now is True:
        now = lst[-2][3]
        ver = lst[-2][:3]
    #print(now, ver)
    return now, ver


main()
