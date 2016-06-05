#!/usr/bin/python

import os
import sys
import time
import argparse
import logging
import tarfile
import subprocess
import ConfigParser
from lxml import objectify

# ----------------------------------------------------------------------------

GARMIN_VENDOR_ID = '091e'

# ----------------------------------------------------------------------------

logging.basicConfig(format="%(asctime)-15s  %(message)s")
log = logging.getLogger("garminDevBackup")

# ----------------------------------------------------------------------------


def get_device_properties(dev):
    udevadm = subprocess.check_output('udevadm info --query=property ' + dev, shell=True)
    return dict(l.split('=', 1) for l in udevadm.split('\n') if len(l) > 0)


def find_and_parse_garmindevice_xml(root):
    path = os.path.join(root, 'Garmin/GarminDevice.xml')
    if not os.path.exists(path):
        path = os.path.join(root, 'GARMIN/GarminDevice.xml')
        if not os.path.exists(path):
            return

    f = open(path, 'r')
    obj = objectify.parse(f)
    f.close()
    return obj.getroot()


def find_activities_path(root):
    p = os.path.join(root, 'Garmin/Activities')
    if os.path.exists(p):
        return p
    p = os.path.join(root, 'GARMIN/ACTIVITY')
    if os.path.exists(p):
        return p
    log.error('Couldn\'t find activities directory in ' + root)
    return None

# ----------------------------------------------------------------------------
# Specific code for mount/unmount devices using gnome/GIO backend


def automount_garmins__gnome():
    import gio
    import gobject

    garmins = []
    loop = gobject.MainLoop()

    def mount_done_cbk(volume, result):
        volume.mount_finish(result)
        loop.quit()

    drives = gio.VolumeMonitor().get_connected_drives()
    for drive in drives:
        for volume in drive.get_volumes():
            dev = volume.get_identifier('unix-device')
            devprop = get_device_properties(dev)
            if devprop['ID_VENDOR_ID'] != GARMIN_VENDOR_ID:
                continue

            if volume.get_mount() == None:
                log.info('Mounting Garmin device (' + dev + ')...')
                if not volume.can_mount():
                    log.error('Impossible to mount device')
                else:
                    volume.mount(None, mount_done_cbk)
                    loop.run()
                log.debug('Mount done')

            root = volume.get_mount().get_root().get_path()

            devinfo = find_and_parse_garmindevice_xml(root)
            if devinfo is None:
                log.error('Couldn\'t find GarminDevice.xml')
                continue

            log.info('Found Garmin ' + devinfo.Model.Description)

            obj = {'_gnome_volume': volume, 'root': root, 'name': devinfo.Model.Description, 'id': devinfo.Id, 'activities': find_activities_path(root)}
            if obj['activities'] == None:
                continue

            yield obj


def umount__gnome(g):
    import gobject

    mount = g['_gnome_volume'].get_mount()
    if not mount.can_unmount():
        log.error('Can\'t unmount ' + g['name'])
        return

    loop = gobject.MainLoop()

    def unmount_done_cbk(m, result):
        m.unmount_finish(result)
        loop.quit()

    mount.unmount(unmount_done_cbk)
    loop.run()
    log.debug('Unmounted ' + g['name'])


def eject__gnome(g):
    import gobject

    if not g['_gnome_volume'].can_eject():
        log.error('Can\'t eject ' + g['name'])
        return

    loop = gobject.MainLoop()

    def eject_done_cbk(volume, result):
        volume.eject_finish(result)
        loop.quit()

    g['_gnome_volume'].eject(eject_done_cbk)
    loop.run()
    log.debug('Ejected ' + g['name'])

# ----------------------------------------------------------------------------


def main(args):
    if len(args.f) == 0:
        log.error('Filename for backup unspecified')
        sys.exit(1)

    prev_files = set()
    if os.path.exists(args.f):
        try:
            fbk = tarfile.open(args.f, 'a')
        except:
            log.error('Impossible to open backup file')
            sys.exit(1)
        for m in fbk.getmembers():
            if m.isfile():
                prev_files.add(m.name)
    else:
        try:
            fbk = tarfile.open(args.f, 'w')
        except:
            log.error('Impossible to open backup file')
            sys.exit(1)

    found_devices = False
    num_bk = 0
    for g in automount_garmins__gnome():
        found_devices = True
        tarroot = '%s - %d' % (g['name'], g['id'])
        try:
            fbk.getmember(tarroot)
        except KeyError:
            d = tarfile.TarInfo(tarroot)
            d.type = tarfile.DIRTYPE
            d.mtime = int(time.time())
            fbk.addfile(d)

        for act in os.listdir(g['activities']):
            tarpath = os.path.join(tarroot, act)
            if tarpath in prev_files:
                continue
            log.info('Backing up %s/%s' % (g['name'], act))
            act_path = os.path.join(g['activities'], act)
            fbk.add(act_path, tarpath)
            num_bk += 1

        if args.auto_eject:
            eject__gnome(g)
        elif args.auto_umount:
            umount__gnome(g)

    if found_devices:
        if num_bk == 0:
            log.info('All files already backuped!')
        else:
            log.info('Backup complete!')
    else:
        log.error('Couldn\'t find any Garmin device')

    fbk.close()

# ----------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Backup activities from Garmin devices')
    parser.add_argument('-f', help='Output archive for backup')
    parser.add_argument('-v', action='store_true', help='Verbose output')
    parser.add_argument('--auto-umount', action='store_true', help='Automatically unmount Garmin devices after done', default=True)
    parser.add_argument('--auto-eject', action='store_true', help='Automatically eject Garmin devices after done')

    confpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'garminDevBackup.conf')
    if os.path.exists(confpath):
        config = ConfigParser.SafeConfigParser()
        config.read([confpath])
        config = dict(config.items('config'))

        args = vars(parser.parse_args([]))
        err = False
        for key in config.iterkeys():
            if key not in args:
                log.error('Configuration file error: invalid key "%s".' % key)
                err = True
        if err:
            sys.exit(1)
        parser.set_defaults(**config)

    args = parser.parse_args()
    if args.v:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)
    main(args)
