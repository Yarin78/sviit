import logging
import sys

from disk import Disk

def show_track_usage(disk):
    side2_has_data = False
    print "Track usage: ",
    for trk_no in range(0, disk.no_tracks()):
        cd = disk.track_contains_data(trk_no)
        if cd == 0:
            sys.stdout.write('.')
        elif cd < 0:
            sys.stdout.write('?')
        else:
            sys.stdout.write('#')
        if trk_no >= 40 and cd != 0:
            side2_has_data = True
    print
    if side2_has_data:
        print "Side 2 has data!"

def show_boot_track(disk):
    track = disk.tracks[0]
    print "Boot track:",
    if "Disk version" in track:
        print "Disk Basic"
    elif disk.track_contains_data(0):
        print "Unknown data"
    else:
        print "Empty"

def show_files(disk):
    files = disk.get_all_files()

    used_existing = [0] * disk.no_tracks()
    used_deleted = [0] * disk.no_tracks()

    ref_tracks = [False] * disk.no_tracks()
    ref_tracks[0] = ref_tracks[1] = ref_tracks[2] = ref_tracks[20] = True
    for file in files:
        for trk_no in file.tracks:
            ref_tracks[trk_no] = True


    has_deletes = False
    for file in files:
        if file.deleted:
            has_deletes = True
        for trk in file.tracks:
            if trk < 0 or trk >= disk.no_tracks():
                logging.warning('Invalid track reference for file %s: %d' % (file.filename, trk))
            else:
                if file.deleted:
                    used_deleted[trk] += 1
                else:
                    used_existing[trk] += 1

    for x in range(0, disk.no_tracks()):
        if used_existing[x] >= 2:
            logging.warning('Multiple existing files uses same track!?')

    print 'FILES'
    print '-----'
    for file in files:
        if file.deleted:
            continue
        print '%-11s %s %5d bytes   Tracks: %s' % (file.filename, file.attr, file.size, file.tracks)
    print

    if has_deletes:
        print 'DELETED FILES'
        print '-------------'
        for file in files:
            if not file.deleted:
                continue
            status = 'Data may exist'
            for trk in file.tracks:
                if not disk.track_contains_data(trk):
                    status = 'Data is empty'
                    break
                if used_existing[trk]:
                    status = 'Data is overwritten'
                    break
                if used_deleted[trk] > 1:
                    status = 'Data may be overwritten'

            print '%-11s %s %5d bytes   Tracks: %-15s Status: %s' % (file.filename, file.attr, file.size, file.tracks, status)
        print

    for trk_no in range(0, disk.no_tracks()):
        if disk.track_contains_data(trk_no) and not ref_tracks[trk_no]:
            print 'Track %d contains data but is not referenced in FAT!' % trk_no

def main():
    disk = Disk(sys.argv[1])
    show_track_usage(disk)
    print
    show_boot_track(disk)
    print
    print 'Disk attributes: %s' % disk.get_disk_attributes()
    print 'IPL: %s' % disk.get_ipl_command()
    print
    show_files(disk)

if __name__ == "__main__":
    main()
