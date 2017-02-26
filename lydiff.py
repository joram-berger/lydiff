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
from lydiff import cliopts

def main():

    try:
        # instantiate LyDiff object using CLI options
        lyDiff = lydiff.LyDiff(lydiff.cliopts.CliOptions())
    except Exception as e:
#        raise
        exit("\n{}\n".format(e))

    if not lyDiff.options.quiet:
        print('\n - '.join(lyDiff.task_list))

    vm = lyDiff.check_version_mismatch()
    if not lyDiff.options.quiet:
        for v in vm:
            print(v)

    purge = lyDiff.purge_dirs()
    if not lyDiff.options.quiet:
        print('\n'.join(purge))

    lyDiff.run_convert()
    lyDiff.run_lily()

    if lyDiff.options.show_output:
        print('-'*48)

    try:
        ret = lyDiff.compare()
    except FileNotFoundError as e:
        print("\n", e)
        print("Temporary files are *not* purged, please inspect. Aborting")
        exit(1)

    if not lyDiff.options.quiet:
        print('done')

    print('Outputs', ['differ', 'are identical'][int(ret)])

    lyDiff.do_diff()

    if not opt['keep_intermediate_files']:
        lydiff.purge_temporary_files(opt)

    return not ret


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
