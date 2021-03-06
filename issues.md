# Issues

Open issues for the `lydiff` tool. In this early state of the development, it is easier to maintain this file than the github issue tracker because there are so many. If you have any issues, please feel free to open it on the tracker.

### Open `meld` in background

**Status**: open

### Handle multipage scores
**Status**: open

### Allow options for `diff`
This is possible in quotes: `-d "diff -u"`.

**Status**: closed

### Allow `colordiff`

### Add configuration file
**Status**: closed

### Fix lilypondoptions option

Specifying something like `-dpaper-size` fails because `argparse` thinks `-d` is the next option and complains
about a missing argument to `-l`.

### Work around lilypond-book-preamble
Varying output sizes break the convert (diff) step.
Inclusion of the lilypond-book-preamble should be commented.

**Status**: open

### Perform diff step on SVG outputs

Anti-aliasing effects etc. are problematic. A vector-graphic diff would be cleaner. Inkscape can do unions and diffs of paths. Scriptable?

**Status**: open

### Add lydiff between git commits

**Status**: open

### Make comparison between fromversion and latest default for single file

**Status**: closed

### Include `compare` from ImageMagick
The metric option can check whether there are any changes at all. Colouring common pixels grey makes differences more visible.

Check metrics:

```
for met in AE FUZZ MAE MEPP MSE NCC PHASH PSNR RMSE; do echo; echo $met $(compare tmp-test2-2.18.2.png
tmp-test3-2.18.2.png -metric $met  output.png); echo $(compare tmp-test2-2.18.2.png tmp-test4-2.18.2.png
-metric $met  output.png); done
```

**Status**: in progress

### Improve error handling

**Status**: in progress

### Move temporary files to /tmp

* Pro: clean working dir
* Con: user cannot easily diff the temporary files

*UL*: I think this is obsolete since the temporary files are purged automatically now.  
However, what I can imagine to be useful is specifying a common output directory
(currently the temporary files are in the directories of the two input files and the output file
is in the directory of the first file (usually this won't make a difference, but we *can* compare
files in different directories)). A common output directory can make sense together with the
`--keep-temporary-files` option

**Status**: open

### Implement »latest« and »stable«

**Status**: in progress

### Check: Version must not be older than file

**Status**: open

### Raise DPI and make new option

**Status**: closed

### Add option to unify the tagline

In order to avoid that files differ just because of the version
appearing in the tagline the lower part of the page could be
cut off.

*UL:* I'd rather suggest to make the tagline *disappear* by injecting some code in the LilyPond files.
Cutting it off doesn't seem reliable. I'm not sure about the injection, but it would be preferable to
make the tagline white rather than making it disappear because it might otherwise affect the music layout.

**Status**: open
