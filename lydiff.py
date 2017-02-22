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
import os
import subprocess

import lydiff
from lydiff.lyversions import Versions
from lydiff.cliopts import cli_options

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
