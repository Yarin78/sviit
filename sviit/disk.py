from sviit.util import str_from_swechar
import sys
import logging
from typing import List, Tuple, Optional, Union

ENCODING = "cp1252"

SIZE_TRACK_0 = 18*128
SIZE_TRACK_X = 17*256
SIZE_SS = SIZE_TRACK_0 + 39 * SIZE_TRACK_X
SIZE_DS = SIZE_TRACK_0 + 79 * SIZE_TRACK_X


class FileNotFoundException(Exception):
    pass

class File:
    def __init__(self, disk, filename: str, type: int, size: int, deleted: bool, tracks, index_position):
        self.disk = disk
        self.filename = filename.strip()
        self.type = type
        self.size = size
        self.deleted = deleted
        self.tracks = tracks
        self.index_position = index_position

        pattr = " "
        rattr = " "
        if type & 0x10:
            pattr = "P"
            type -= 0x10
        if type & 0x40:
            rattr = "R"
            type -= 0x40
        delim = ' '
        if type == 0x00:
            delim = ' '
        elif type == 0x01:
            delim = '*'
        elif type == 0x80:
            delim = '.'
        elif type == 0xA0:
            delim = '#'
        else:
            delim = '?'
        self.displayname = "%s%s%s" % (filename[0:6], delim, filename[6:9])
        self.attr = "%c%c" % (pattr, rattr)

    def is_basic_file(self):
        return (self.type & 0xA1) == 0x80

    def read(self):
        data = bytes()
        for trk in self.tracks:
            if trk < 0 or trk >= len(self.disk.tracks):
                logging.warning('File %s is stored on track %d which doesn''t exist' % (self.displayname, trk))
                break
            data += self.disk.tracks[trk]

        return data[:self.size]


class Disk:
    tracks: List[bytes]

    def __init__(self, filename: str):
        self.tracks = self.load_from_file(filename)

    def is_single_sided(self):
        return len(self.tracks) == 40

    def is_double_sided(self):
        return len(self.tracks) == 80

    def no_tracks(self):
        return len(self.tracks)

    def has_fat(self):
        dir_track = self.tracks[20]
        fats = [dir_track[14*256:15*256], dir_track[15*256:16*256], dir_track[16*256:17*256]]

        for fat in fats:
            if fat[0] != 254 or fat[1] != 254 or fat[2] != 254 or fat[20] != 254:
                return False

        return True

    def track_contains_data(self, track_no: int):
        # Returns 0 if no data (just one value)
        # Returns -1 if probably no data (at most 4 different values)
        # Returns 1 if data
        cnt=[0] * 256
        for byte in self.tracks[track_no]:
            cnt[byte] += 1
        dif = len([x for x in cnt if x > 0])
        if dif == 1:
            return 0
        if dif <= 4:
            return -1
        return 1

    def load_from_file(self, filename: str) -> List[bytes]:
        with open(filename, "rb") as f:
            data: bytes = f.read(1000000)

        tracks = [data[:SIZE_TRACK_0]]
        if len(data) == SIZE_SS:
            for trk in range(0,39):
                tracks.append(data[SIZE_TRACK_0 + trk * SIZE_TRACK_X:SIZE_TRACK_0 + (trk + 1) * SIZE_TRACK_X])
        elif len(data) == SIZE_DS:
            for trk in range(0,39):
                start = SIZE_TRACK_0 + (trk * 2 + 1) * SIZE_TRACK_X
                tracks.append(data[start:start + SIZE_TRACK_X])
            for trk in range(0,40):
                start = SIZE_TRACK_0 + trk * 2 * SIZE_TRACK_X
                tracks.append(data[start:start + SIZE_TRACK_X])
        else:
            raise Exception('Invalid image size: %d bytes' % len(data))

        return tracks

    def save_to_file(self, filename: str):
        with open(filename, "wb") as f:
            f.write(bytearray(self.tracks[0]))
            if self.is_double_sided():
                f.write(bytearray(self.tracks[40]))
            for trk in range(1,40):
                f.write(bytearray(self.tracks[trk]))
                if self.is_double_sided():
                    f.write(bytearray(self.tracks[40 + trk]))

    def get_disk_attributes(self) -> str:
        dir_track = self.tracks[20]
        dat = dir_track[13*256:14*256]
        if dat[0] == 0x00:
            return 'None'
        elif dat[0] == 0x10:
            return 'P'
        elif dat[0] == 0x40:
            return 'R'
        elif dat[0] == 0x50:
            return 'PR'
        return 'Unknown (%d)' % dat[0]

    def get_ipl_command(self) -> str:
        dir_track = self.tracks[20]
        dat = dir_track[13*256:14*256]
        ipl_command: bytes = dat[1:].split(b"\0", 1)[0]
        return ipl_command.decode(ENCODING)

    def get_files(self) -> List[File]:
        return [f for f in self.get_all_files() if not f.deleted]

    def get_deleted_files(self) -> List[File]:
        return [f for f in self.get_all_files() if f.deleted]

    def _get_directory(self) -> Tuple[bytes, bytes, bytes]:
        dir_track = self.tracks[20]
        directory = dir_track[0:13*256]
        dat = dir_track[13*256:14*256]
        fat = [dir_track[14*256:15*256], dir_track[15*256:16*256], dir_track[16*256:17*256]]

        if fat[0][0:256] != fat[1][0:256] or fat[0][0:256] != fat[2][0:256]:
            logging.warning('FAT mismatches')

        fat = fat[0] # TODO: Pick most common

        if fat[0] != 254 or fat[1] != 254 or fat[2] != 254 or fat[20] != 254:
            logging.warning('FAT not formatted properly')

        return directory, dat, fat

    def _write_directory(self, directory: bytes=None, dat: bytes=None, fat: bytes=None):
        dir_track = self.tracks[20]

        if not directory:
            directory = dir_track[0:13*256]
        if not dat:
            dat = dir_track[13*256:14*256]
        if not fat:
            fat = dir_track[14*256:15*256]

        self.tracks[20] = directory + dat + fat + fat + fat

    def create_file_from_tracks(self, filename: str, file_type: int, tracks: List[int]):
        directory, _, fat = self._get_directory()

        index_no = 0
        while directory[index_no * 16] != 255:
            index_no += 1

        file_entry = ('%-9s%c%c\255\255\255\255\255' % (filename, chr(file_type), chr(tracks[0]))).encode(ENCODING)

        directory = directory[:index_no*16] + file_entry + b"\xFF" + directory[index_no*16+17:]

        mutable_fat = list(fat)
        current = tracks[0]
        for next in tracks[1:]:
            mutable_fat[current] = next
            current = next
        mutable_fat[current] = 0xC0 + 17

        self._write_directory(directory=directory, fat=bytes(mutable_fat))

    def normalize_filename(self, filename: str, swechars=False) -> str:
        if swechars:
            filename = str_from_swechar(filename)
        parts = filename.split('.')
        if len(parts) == 1:
            filename = parts[0].strip()
        else:
            filename = ("%-6s%s" % (parts[0], parts[1])).strip()

        return filename

    def get_file(self, filename: str, swechars=False) -> Optional[File]:
        filename = self.normalize_filename(filename, swechars)

        for f in self.get_files():
            if f.filename == filename:
                return f
        raise FileNotFoundException(f"Failed to get file {filename}")

    def get_all_files(self) -> List[File]:
        directory, _, fat = self._get_directory()

        files = []
        end_reached = False
        for i in range(0, 13*16):
            entry = directory[i*16:i*16+16]
            if entry[0] == 255:
                end_reached = True
                continue

            filename_bytes = entry[0:9]
            is_deleted = False
            if filename_bytes[0] == 0:
                filename = "?%s" % filename_bytes[1:].decode(ENCODING)
                is_deleted = True
            else:
                filename = filename_bytes.decode(ENCODING)

            file_type = entry[9]
            fat_ptr = entry[10]

            file_tracks: List[int] = []

            circular = False
            while fat_ptr < 0xC0:
                file_tracks.append(fat_ptr)
                fat_ptr = fat[fat_ptr]
                if fat_ptr in file_tracks:
                    circular = True
                    break

            if not circular:
                file_size = SIZE_TRACK_X * (len(file_tracks) - 1) + 256 * (fat_ptr - 0xC0)
            else:
                file_size = -1

            files.append(File(self, filename, file_type, file_size, is_deleted or end_reached, file_tracks, i))
        return files

