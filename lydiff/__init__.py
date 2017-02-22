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


# plausibility checks
def check_empty_comparison(opt):
    """Check for unnecessary comparison that can't produce different files."""
    result = equal(opt['input_files']) and equal(opt['target_versions']) and equal(opt['convert'])
    if result:
        print("Warning: Equal input_files won't generate differences")
    return result

def check_available_versions(opt):
    """Check and warn if fallback LilyPond versions will be used."""
    target_versions = opt['target_versions']
    lily_versions = opt['lily_versions']
    for i in [0, 1]:
        if target_versions[i] != lily_versions[i] and target_versions[i] != 'latest':
            print("Warning: LilyPond %s is not available. File %d %r will be run using version %s instead." %
                  (target_versions[i], i+1, opt['input_files'][i], lily_versions[i]))



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



def runconvert(opt):
    for i in [0, 1]:
        cmd = [opt['convert_lys'][i], '-c', opt['input_files'][i]]
        fileout = opt['tmp_files'][i]
        if opt['dryrun']:
            print("- Run convert: ", ' '.join(cmd), '>', fileout)
        else:
            with open(fileout, 'w') as f:
                if opt['show_output']:
                    print('-'*48)
                    subprocess.call(cmd, stdout=f)
                else:
                    subprocess.call(cmd, stdout=f, stderr=subprocess.DEVNULL)

def runlily(opt):
    for i in [0, 1]:
        cmd = opt['commands'][i]
        if opt['dryrun']:
            print('- Run LilyPond:', ' '.join(cmd))
        elif opt['show_output']:
            print('-'*48)
            subprocess.call(cmd)
        else:
            subprocess.call(cmd, stderr=subprocess.DEVNULL)


def compare(opt):
    images = opt['image_files']
    cmd = ['convert', *reversed(images),
           '-channel', 'red,green', '-background', 'black',
           '-combine', '-fill', 'white', '-draw', "color 0,0 replace", opt['diff_file']]
    comp = ['compare', '-metric', 'AE', *images, 'null:']
    if opt['dryrun']:
        print('- Run compare: ', ' '.join([repr(s) if ' ' in s else s for s in cmd]))
        print('- Run compare: ', ' '.join(comp))
        return True

    subprocess.call(cmd)
    process = subprocess.Popen(comp, stderr=subprocess.PIPE)
    _, npixels = process.communicate()
    #print(_, int(npixels))
    return int(npixels) == 0


def do_diff(opt):
    diff_tool = opt['diff_tool']
    if diff_tool is not None:
        if opt['dryrun']:
            print('- Run diff:    ', diff_tool, *opt['tmp_files'])
        else:
            if diff_tool.startswith('diff'):
                print('-'*48)
                print('diff:')
            subprocess.call([*diff_tool.split(), *opt['tmp_files']])
