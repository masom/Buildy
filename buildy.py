#!/bin/env python
'''
Copyright (2012) Martin Samson
License: LGPL
'''
import rpm
import os, subprocess, urllib, getpass
from argparse import ArgumentParser

SOURCES = '{0}/rpmbuild/SOURCES'.format(os.getenv('HOME'))

parser = ArgumentParser()

parser.add_argument('-u', '--user', help='SCP User', required=True)
parser.add_argument('--host', help='SCP Host', default='10.0.254.23')
parser.add_argument('-d', '--dest', help='SCP Destination directory', default='/usr/local/www/rpms')
parser.add_argument('-j', '--jail', help='Jail Type (content/database)', default='content')
parser.add_argument('-U', action='store_true', help='Update source archive.')
parser.add_argument('spec', help='RPM Spec file')
options = parser.parse_args()

if not os.path.exists(options.spec):
    raise RuntimeError("Provided spec file does not exists: `{0}`".format(options.spec))

transaction = rpm.ts()
spec = transaction.parseSpec(options.spec)
source_url = spec.sources[0][0]

source_file = spec.sourceHeader[rpm.RPMTAG_SOURCE][0]
if source_file is None:
    raise RuntimeError('Error, source file cannot be None.')

source_archive = '{0}/{1}'.format(SOURCES, source_file)

if not os.path.exists(source_archive) or options.U:
    if os.path.exists(source_archive):
        os.unlink(source_archive)
    print('Downloading `{0}`.'.format(source_url))
    urllib.urlretrieve(source_url, source_archive)

if not os.path.exists(source_archive):
    raise RuntimeError('Source archive missing! ({0})'.format(source_archive))

cmd = ['rpmbuild', '-bb', '--clean', options.spec]

process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
retcode = process.wait()
result_rpm = None
for line in process.stdout:
    # we are looking for something like this: Wrote: /usr/src/redhat/RPMS/i386/cdplayer-1.0-1.i386.rpm
    if not line.startswith('Wrote:'):
        continue

    result_rpm = line.split(" ")[1].strip()

if result_rpm is None or not os.path.exists(result_rpm):
    raise RuntimeError('RPM Build error: File `{0}` does not exists.'.format(result_rpm))

rpm = os.path.basename(result_rpm)

destination = "{0}/{1}/{2}".format(options.dest, options.jail, rpm)

dst = "{0}@{1}:{2}".format(options.user, options.host, destination)
cmd = ['scp']
cmd.append(result_rpm)
cmd.append(dst)
print("Uploading `{0}` to `{1}`".format(rpm, dst))
subprocess.Popen(cmd).wait()
