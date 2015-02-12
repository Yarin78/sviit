import logging
import sys

from disk import Disk

def main():
    disk = Disk(sys.argv[1])
    disk.create_file_from_tracks("adven2", 128, [5, 4])
    disk.save_to_file(sys.argv[2])

if __name__ == "__main__":
    main()
