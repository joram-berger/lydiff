# Issues

Open issues for the `lydiff` tool. In this early state of the development, it is easier to maintain this file than the github issue tracker because there are so many. If you have any issues, please feel free to open it on the tracker.

### Open `meld` in background

**Status**: open

### Handle multipage scores
**Status**: open

### Allow options for `diff`
**Status**: open

### Allow `colordiff`

### Add configuration file
**Status**: open

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

**Status**: open

### Include `compare` from ImageMagick
The metric option can check whether there are any changes at all. Colouring common pixels grey makes differences more visible.

Check metrics:

```for met in AE FUZZ MAE MEPP MSE NCC PHASH PSNR RMSE; do echo; echo $met $(compare tmp-test2-2.18.2.png tmp-test3-2.18.2.png -metric $met  output.png); echo $(compare tmp-test2-2.18.2.png tmp-test4-2.18.2.png -metric $met  output.png); done```

**Status**: open

### Improve error handling

**Status**: open

### Move temporary files to /tmp

* Pro: clean working dir
* Con: user cannot easily diff the temporary files

**Status**: open

### Implement »latest« and »stable«

**Status**: open

### Check: Version must not be older than file

**Status**: open

### Raise DPI and make new option

**Status**: open

### Add option to unify the tagline

In order to avoid that files differ just because of the version
appearing in the tagline the lower part of the page could be
cut off.

**Status**: open
