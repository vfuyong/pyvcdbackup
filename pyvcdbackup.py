import subprocess
import os
import socket
import re
import glob
from docopt import *

__doc__ = """
Usage: pyvcdbackup.py [-h] [--max=<max>]

Create a vCloud Director backup then remove old backup files

Arguments:
    
Options:
    -h --help           show this
    --max=<max>         max number of backups to keep [default: 14]
"""

if __name__ == "__main__":
    options = docopt(__doc__, argv=None, help=True, version=None, options_first=False)

    print('options:')
    print(options)

    max = int(options['--max'])

    # Get cluster status and hostname
    query_cmd = 'sudo -i -u postgres /opt/vmware/vpostgres/10/bin/repmgr -f /opt/vmware/vpostgres/10/etc/repmgr.conf cluster show'
    print(query_cmd)
    query_output = subprocess.check_output([
        '/usr/bin/sudo', '-i', '-u', 'postgres',
        '/opt/vmware/vpostgres/10/bin/repmgr',
        '-f', '/opt/vmware/vpostgres/10/etc/repmgr.conf',
        'cluster', 'show'
    ])
    hostname = socket.gethostname().split(".")[0]

    print(query_output)
    print('My hostname is %s' % hostname)

    # Tell whether I am primary
    is_primary = False
    lines = query_output.split(os.linesep)
    for line in lines:
        if re.search(hostname, line) and re.search(r'primary', line):
            is_primary = True
            break

    # Backup if primary
    if is_primary:
        print('I am primary')
        print('Creating backup')
        backup_cmd = '/opt/vmware/appliance/bin/create-db-backup'
        try:
            subprocess.check_output([backup_cmd])
        except subprocess.CalledProcessError as grepexc:
            print "error code", grepexc.returncode, grepexc.output
        files = glob.glob('/opt/vmware/vcloud-director/data/transfer/pgdb-backup/db-backup-*.tgz')

        # Sort backup files in ascending order
        files.sort()

        # Delete excessive backups if applicable
        current = len(files)
        if current > max:
            print('There are %d backups - keeping %d backups only' % (current, max))
            for i in range(current - max):
                print('Deleting %s' % files[i])
                os.remove(files[i])
        else:
            print('There are %d backups - no cleanup required' % current)
    else:
        print('I am not primary')
