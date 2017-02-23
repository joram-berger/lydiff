#!/usr/bin/env python3

import os
import glob
import subprocess

def configure(opt):
    """Configure process, based on given options determine names,
    paths and operations."""

    def get_paths_and_files(input_files):
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
    input_paths, input_files, input_basenames = get_paths_and_files(opt.files)

    # LilyPond versions
    input_versions = tuple(getfileversion(f) for f in input_files)
    available_versions = opt.available_versions
    target_versions = get_target_versions(opt.versions, available_versions)
    lily_versions, executables = get_exe_versions(target_versions, available_versions)

    # temp and output files
    convert_lys = tuple(os.path.join(os.path.dirname(exe), 'convert-ly') for exe in executables)    
    tmp_files = tuple('tmp-%s-%s' % (b, v) for b, v in zip(input_basenames, lily_versions))
    diff_file = opt.output
    if diff_file is None:
        if equal(input_files):
            diff_file = 'diff_%s_%s-%s' % (input_basenames[0], *lily_versions)
        elif equal(target_versions):
            diff_file = 'diff_%s-%s_%s' % (*input_basenames, lily_versions[0])
        else:
            diff_file = 'diff_%s-%s_%s-%s' % (*input_basenames, *lily_versions)

    # LilyPond command line
    lily_options = [l.replace('~', os.path.expanduser('~')) for l in opt.lilypondoptions]
    commands = tuple(
        [[executables[i]] +
         lily_options[i].split() +
         ['--png',
          '-dresolution=%d' % opt.resolution,
          '-danti-alias-factor=2',
          '-o',
          os.path.join(input_paths[i], tmp_files[i]),
          os.path.join(input_paths[i], tmp_files[i] + '.ly')]
          for i in [0, 1]]
    )

    return {
        'input_paths': input_paths,
        'input_files': input_files,
        'input_basenames': input_basenames,
        'input_versions': input_versions,
        'available_versions': available_versions,
        'target_versions': target_versions,
        'lily_versions': lily_versions,
        'executables': executables,
        'convert_lys': convert_lys,
        'convert': opt.convert,
        'keep_intermediate_files': opt.keep_intermediate_files,
        'quiet': opt.quiet,
        'dryrun': opt.dryrun,
        'show_output': opt.showoutput,
        'diff_tool': opt.diff,
        'tmp_files': tmp_files,
        'diff_file': diff_file,
        'lily_options': lily_options, # is this actually used?
        'commands': commands
        }


# plausibility checks
def check_empty_comparison(opt):
    """Check for unnecessary comparison that can't produce different files."""
    return equal(opt['input_files']) and equal(opt['target_versions']) and equal(opt['convert'])

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

def print_report(opt):
    print("Running this:   ___ 1 _______________     ___ 2 _______________")
    print("Files:      %25s %25s" % tuple("%s (%s)" % (i, v) for i, v in zip(opt['input_files'], opt['input_versions'])))
    #print("convert:    %25s %25s" % tuple(['no', 'yes'][int(b)] for b in opt.convert))
    print("target version: %21s %25s" % opt['target_versions'])
    print("convert-ly: %25s %25s" % opt['convert_lys'])
    print("tmp_files:  %25s %25s" % opt['tmp_files'])
    print("executable: %25s %25s" % opt['executables'])
    print("output:     %45s" % opt['diff_file'])
    print("Run tools ... ", end='', flush=True)


def find_temporary_files(opt):
    """Return a list with all temporary files.
       A comprehensive list of potential file names is tested,
       but only those actually existing are returned as a list."""
    files = [glob.glob(
               "{}*".format(
                    os.path.join(opt['input_paths'][i], opt['tmp_files'][i])))
            for i in [0, 1]]
    result = files[0]
    result.extend(files[1])
    return result

def _delete_temporary_files(opt):
    """Find existing and remove the tmp files."""
    del_list = find_temporary_files(opt)
    if opt['dryrun'] or opt['show_output']:
        print(" - " + "\n - ".join(del_list))
    for f in del_list:
        os.remove(f)
    
def purge_dirs(opt):
    """Purge files that are to be generated, so in case of interruption
       there are no 'old' files confusing the output."""
    if not opt['quiet']:
        print("Purge old files:")
    _delete_temporary_files(opt)
    outfile = os.path.join(opt['input_paths'][0], opt['diff_file'])
    if os.path.exists(outfile):
        if opt['dryrun'] or opt['show_output']:
            print(" - {}".format(outfile))
        os.remove(outfile)

def purge_temporary_files(opt):
    """Remove temporary files at the end."""
    if not opt['quiet']:
        print("Purge temporary files:")
    _delete_temporary_files(opt)
    
def runconvert(opt):
    for i in [0, 1]:
        path = opt['input_paths'][i]
        infile = os.path.join(path, opt['input_files'][i])
        cmd = [opt['convert_lys'][i], '-c', infile]
        fileout = os.path.join(path, opt['tmp_files'][i] + '.ly')
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
    changes = []
    images = tuple(
        [glob.glob(os.path.join(opt['input_paths'][i], opt['tmp_files'][i] + '*.png'))
         for i in [0, 1]])
    for i in [0, 1]:
        images[i].sort()
    image_pairs = list(zip(images[0], images[1]))
    from_count = len(images[0])
    to_count = len(images[1])
    page_count = max(from_count, to_count)

    if page_count == 1:
        outfiles = [os.path.join(opt['input_paths'][0], "{}.png".format(opt['diff_file']))]
    else:
        outfiles = [os.path.join(opt['input_paths'][0], "{}-{}.png".format(
            opt['diff_file'], i + 1))
            for i in range(page_count)]

    # first process actual image pairs
    for i in range(len(image_pairs)):
        images = image_pairs[i]
        conv = ['convert', *reversed(images),
               '-channel', 'red,green', '-background', 'black',
               '-combine', '-fill', 'white', '-draw', "color 0,0 replace", outfiles[i]]
        comp = ['compare', '-metric', 'AE', *images, 'null:']
        if opt['dryrun'] or opt['show_output']:
            print('- Run convert: ', ' '.join([repr(s) if ' ' in s else s for s in conv]))
            print('- Run compare: ', ' '.join(comp))
        if not opt['dryrun']:
            subprocess.call(conv)
            process = subprocess.Popen(comp, stderr=subprocess.PIPE)
            _, npixels = process.communicate()
            changes.append(int(npixels))

    # process trailing pages if one score is longer than the other
    tail = int(to_count > from_count)
    diff_base = os.path.join(opt['input_paths'][0], opt['diff_file'])
    for i in range(len(image_pairs), page_count):
        from_file = os.path.join(
            opt['input_paths'][0],
            "{}-page{}.png".format(opt['tmp_files'][tail], i + 1))
        if opt['dryrun']:
            print("Copy page file {}".format(i + 1))
        else:
            # TODO: instead of copying the original file it would be better
            # to also convert it changing the color to the proper one
            # corresponding to the longer score
            import shutil
            shutil.copy2(from_file, "{}-{}.png".format(diff_base, i + 1))

    if opt['dryrun']:
        return True

    if len(images[0]) != len(images[1]):
        return False
    else:
        return sum(npixels) == 0


def do_diff(opt):
    diff_tool = opt['diff_tool']
    diff_files = tuple(
        [os.path.join(opt['input_paths'][i], opt['tmp_files'][i] + '.ly')
         for i in [0, 1]])
    if diff_tool is not None:
        if opt['dryrun']:
            print('- Run diff:    ', diff_tool, *diff_files)
        else:
            if diff_tool.startswith('diff'):
                print('-'*48)
                print('diff:')
            subprocess.call([*diff_tool.split(), *diff_files])
