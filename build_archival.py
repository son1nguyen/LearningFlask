#!/usr/bin/env python

import os
import shutil
import subprocess

if __name__ == '__main__':

    dirs = ['/home/ubuntu/builds/master/Build_CDM',
            '/home/ubuntu/builds/42/Build_CDM',
            '/home/ubuntu/builds/41/Build_CDM']
    print subprocess.check_output(['find', '/home/ubuntu/builds/', '-name', 'archive.zip'])
    for dir in dirs:
        sub_dirs = os.listdir(dir)
        sub_dirs.sort(key=int, reverse=True)

        for sub_dir in sub_dirs[20:]:
            abs_dir = '{}/{}'.format(dir, sub_dir)
            print "Deleting dir {}".format(abs_dir)
            shutil.rmtree(abs_dir)
