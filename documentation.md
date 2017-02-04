# Documentation of `lydiff`

What is lydiff? TBD

## Requirements

For Ubuntu, all requirements are installed via
`sudo apt install python3 python3-yaml imagemagick lilypond meld`.

## Installation

To be done.



## Comparing different files

Different versions of a file are easily compared with this command:
```
lydiff file1.ly file2.ly
```
By default, the lilypond version mentioned in the version statement
of each file is used to compile this file ("fromfile"). This is
equivalent to these two commands as single arguments are used for
both file:
```
lydiff file1.ly file2.ly -v fromfile
lydiff file1.ly file2.ly -v fromfile fromfile
```

## Comparing different lilypond versions

To use this functionality, several version of lilypond need to be installed
on the systm.

```
lydiff file.ly
```

When providing a single file, the default setting is to compare the
version accoding to the version statement in the file ("fromfile")
with the latest version installed in the search path ("latest").
This can be explicitly entered as

```
lydiff file.ly -v fromfile latest
```

Of course, any installed version of lilypond can be used to compile
the file and generate the output diff:
```
lydiff file.ly -v 2.18.2 2.19.54
```

## More options

Some options steer the program flow:

* `--resolution`: Resolution of the lilypond output in dpi.
* `--test`: Do not run the tools just print the commands that would be run.
* `--quiet`: Do not show versions, files and executables in use.
* `--showoutput`: Show the standard output of the tools in use.
* `--help`: Show a help message explaining all command line options.
* `--output`: Name of the output file.
* `--diff`: Diff tool used to show the diff of the input files after
  running convert-ly. Possible examples are:
  `-d diff`, `-d "diff -u"` and `-d meld`
* `--path`: Search path for lilypond executables. Space separated lists
  are allowed as well as globbing.
  Example: `"/usr/bin ~/opt/*/bin"`.

Options per file:

* `--version`: lilypond version to be used to compile each file.
* `--lilypondoptions`: A string of options passed to the lilypond command.
  Quotes are required if the options contain a space.
