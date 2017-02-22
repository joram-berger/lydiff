#!/usr/bin/env python3

import os
import subprocess

def configure(opt):
    """Configure process, based on given options determine names,
    paths and operations."""

    def get_target_versions(versions, av):
        result = versions
        for i, ov in enumerate(versions):
            if ov == 'fromfile':
                result[i] = input_versions[i]
            elif ov == 'latest':
                result[i] = av.get(ov)[0]
        return tuple(result)

    def get_exe_versions(tv, av):
        versions = [available_versions.get(v) for v in target_versions]
        exe_versions = (versions[0][0], versions[1][0])
        binaries =  (versions[0][1], versions[1][1])
        return (exe_versions, binaries)

    # input files
    input_files = tuple(opt.files)
    input_basenames = tuple(os.path.splitext(f)[0] for f in input_files)

    # LilyPond versions
    input_versions = tuple(getfileversion(f) for f in input_files)
    available_versions = opt.available_versions
    target_versions = get_target_versions(opt.versions, available_versions)
    lily_versions, executables = get_exe_versions(target_versions, available_versions)

    # temp and output files
    convert_lys = tuple(os.path.join(os.path.dirname(exe), 'convert-ly') for exe in executables)    
    tmp_files = tuple('tmp-%s-%s.ly' % (b, v) for b, v in zip(input_basenames, lily_versions))
    image_files = tuple(f.replace('.ly', '.png') for f in tmp_files)
    diff_file = opt.output
    if diff_file is None:
        if equal(input_files):
            diff_file = 'diff_%s_%s-%s.png' % (input_basenames[0], *lily_versions)
        elif equal(target_versions):
            diff_file = 'diff_%s-%s_%s.png' % (*input_basenames, lily_versions[0])
        else:
            diff_file = 'diff_%s-%s_%s-%s.png' % (*input_basenames, *lily_versions)

    # LilyPond command line
    lily_options = [l.replace('~', os.path.expanduser('~')) for l in opt.lilypondoptions]
    commands = (
        [executables[0]] + lily_options[0].split() + ['--png', '-dresolution=%d' % opt.resolution, '-danti-alias-factor=2', '-o', image_files[0][:-4], tmp_files[0]],
        [executables[1]] + lily_options[1].split() + ['--png', '-dresolution=%d' % opt.resolution, '-danti-alias-factor=2', '-o', image_files[1][:-4], tmp_files[1]],
    )

    return {
        'input_files': input_files,
        'input_basenames': input_basenames,
        'input_versions': input_versions,
        'available_versions': available_versions,
        'target_versions': target_versions,
        'lily_versions': lily_versions,
        'executables': executables,
        'convert_lys': convert_lys,
        'convert': opt.convert,
        'quiet': opt.quiet,
        'dryrun': opt.dryrun,
        'show_output': opt.showoutput,
        'diff_tool': opt.diff,
        'tmp_files': tmp_files,
        'image_files': image_files,
        'diff_file': diff_file,
        'lily_options': lily_options, # is this actually used?
        'commands': commands
        }

def getfileversion(file):
    version = None
    with open(file) as f:
        for line in f:
            if r'\version' in line:
                _, version, _ = line.split('"', 2)
                break
    return version

def equal(pair):
    return pair[0] == pair[1]

