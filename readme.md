# Diff for LilyPond Scores

`lydiff` is a tool to compare LilyPond scores similar to comparing text using `diff`.
LilyPond is a music engraving program.

## Installation

`lydiff` requires a python3 installation including the packages argparse, glob, os and subprocess. Additionally, the programs diff, lilypond (and convert-ly) and ImageMagick needs to be installed. meld is optional.
The examples an the documentation expect that you create a symlink called `lydiff` to the python file [lydiff.py](lydiff.py) from this repository in a directory in the path of your operating system.

## Usage

To compare files (first line) or LilyPond versions (line 2 and 3) please use the following commands:
```
lydiff file1.ly file2.ly
lydiff file.ly -v fromfile latest
lydiff file.ly -v 2.18.2 2.19.54
```
The result is contained in the output file which is usually named "diff_&lt;files&gt;_&lt;versions&gt;.png".

For further information, please read the [documentation] and refer to the help command `lydiff -h`.

[documentation]: documentation.md

## Author

This tool is originally written by [Joram Berger](https://github.com/joram-berger "Github profile").

## License

This tool is licensed under the [GPL3] or any later version. See [license.md] for details.

[GPL3]: https://www.gnu.org/licenses/gpl.html "GPL3"
[license.md]: license.md "GPL3+"