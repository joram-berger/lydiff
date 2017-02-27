#!/usr/bin/env python3
"""
Program `lydiff`
© 2017 Joram Berger, Urs Liska
License: GPL3+

Visually compares two LilyPond scores.

Use cases:
a)
1 .ly file, two LilyPond versions:
  - fromfile (default)
  - latest (default)
  - specific version
b)
2 .ly files, one or two LilyPond versions
c)
2 versions of 1 .ly file (not implemented yet)
"""

import lydiff
from lydiff import cliopts

def main():

    try:
        lyDiff = lydiff.LyDiff(lydiff.cliopts.CliOptions())
    except Exception as e:
        exit("\n{}\n".format(e))

    if lyDiff.options.installed_versions:
        print(lyDiff.options.available_versions)
        exit()

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
        exit("\n{}\nTemporary files are *not* purged, please inspect. Aborting".format(e))

    if not lyDiff.options.quiet:
        print('done')

    print('Outputs', ['differ', 'are identical'][int(ret)])

    lyDiff.do_diff()

    if not lyDiff.options.keep_intermediate_files:
        lyDiff.purge_temporary_files()

    return not ret

if __name__ == "__main__":
    main()
