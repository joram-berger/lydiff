#!/usr/bin/env python3

import os
import glob
import subprocess

class LyDiff(object):

    def __init__(self, options):
        self.options = options
        if self.check_empty_comparison():
            raise Exception("Warning: Equal input_files won't generate differences. Aborting.")

    @property
    def task_list(self):
        """Generate a string list with the task that are about to be executed."""
        res = []
        res.append("Running this:   ___ 1 _______________     ___ 2 _______________")
        res.append("Files:      %25s %25s" % tuple("%s (%s)" % (i, v) for i, v in zip(
            self.options.input_files, self.options.input_versions)))
        res.append("target version: %21s %25s" % self.options.target_versions)
        res.append("convert-ly: %25s %25s" % self.options.convert_lys)
        res.append("tmp_files:  %25s %25s" % self.options.tmp_files)
        res.append("executable: %25s %25s" % self.options.executables)
        res.append("output:     %45s" % self.options.diff_file)
        res.append("Run tools ...\n")

        return res

    def check_empty_comparison(self):
        """Check for unnecessary comparison that can't produce different files."""
        return equal(self.options.input_files) and equal(self.options.target_versions) and equal(self.options.convert)

    def check_version_mismatch(self):
        """Check and warn if fallback LilyPond versions will be used."""
        target_versions = self.options.target_versions
        lily_versions = self.options.lily_versions
        result = []
        for i in [0, 1]:
            if target_versions[i] != lily_versions[i] and target_versions[i] != 'latest':
                result.append(
                "Warning: LilyPond %s is not available. File %d %r will be run using version %s instead." %
                      (target_versions[i], i+1, self.options.input_files[i], lily_versions[i]))
        return result

    def find_temporary_files(self, ext=""):
        """Return a list with all temporary files.
           A comprehensive list of potential file names is tested,
           but only those actually existing are returned as a list."""
        files = [glob.glob(
                   "{}*{}".format(
                        os.path.join(self.options.input_paths[i], self.options.tmp_files[i]),
                        ext))
                for i in [0, 1]]
        result = files[0]
        result.extend(files[1])
        return result

    def _delete_temporary_files(self):
        """Find existing and remove the tmp files."""
        del_list = self.find_temporary_files()
        if self.options.dryrun or self.options.show_output:
            print(" - " + "\n - ".join(del_list))
        for f in del_list:
            os.remove(f)
        
    def purge_dirs(self):
        """Purge files that are to be generated, so in case of interruption
           there are no 'old' files confusing the output."""
        result = ["Purge old files:"]
        self._delete_temporary_files()
        outfile_base = os.path.join(self.options.input_paths[0], self.options.diff_file)
        outfiles = glob.glob("{}*".format(outfile_base))
        for f in outfiles:
            if self.options.dryrun or self.options.show_output:
                result.append(" - {}".format(f))
            if not self.options.dryrun:
                os.remove(f)
        return result

    def purge_temporary_files(self):
        """Remove temporary files at the end."""
        if not self.options.quiet:
            print("Purge temporary files:")
        self._delete_temporary_files()
        
    def run_convert(self):
        for i in [0, 1]:
            path = self.options.input_paths[i]
            infile = os.path.join(path, self.options.input_files[i])
            cmd = [self.options.convert_lys[i], '-c', infile]
            fileout = os.path.join(path, self.options.tmp_files[i] + '.ly')
            if self.options.dryrun:
                print("- Run convert: ", ' '.join(cmd), '>', fileout)
            else:
                with open(fileout, 'w') as f:
                    if self.options.show_output:
                        print('-'*48)
                        subprocess.call(cmd, stdout=f)
                    else:
                        subprocess.call(cmd, stdout=f, stderr=subprocess.DEVNULL)

    def run_lily(self):
        for i in [0, 1]:
            cmd = self.options.commands[i]
            if self.options.dryrun:
                print('- Run LilyPond:', ' '.join(cmd))
            elif self.options.show_output:
                print('-'*48)
                subprocess.call(cmd)
            else:
                subprocess.call(cmd, stderr=subprocess.DEVNULL)




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


def compare(opt):
    changes = []
    images = tuple(
        [glob.glob(os.path.join(opt['input_paths'][i], opt['tmp_files'][i] + '*.png'))
         for i in [0, 1]])
    for i in [0, 1]:
        images[i].sort()
    image_pairs = list(zip(images[0], images[1]))
    # number of pages for both scores
    page_counts = (len(images[0]), len(images[1]))
    # page count for longer score (if different)
    page_count = max(page_counts[0], page_counts[1])

    if page_counts[0] == 0 or page_counts[1] == 0:
        # one or both LilyPond compilations failed
        files = ["\n - {} ({})".format(
            os.path.basename(opt['input_files'][i]),
            opt['lily_versions'][i])
            for i in [0, 1]
            if page_counts[i] == 0]
        msg = "LilyPond failed to produce score(s) from file(s):{}".format("".join(files))
        raise FileNotFoundError(msg)

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
    tail = int(page_counts[1] > page_counts[0])
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
