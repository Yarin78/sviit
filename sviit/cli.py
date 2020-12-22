import click
import click_log
import logging
from sviit import disk_viewer, basic_tokenizer
from sviit.disk import Disk

"""
sviit disk list
sviit disk view <myfile>
"""

logger = logging.getLogger("sviit_cli")
click_log.basic_config(logger)

@click.group()
def main():
    pass

@main.group()
def disk():
    pass

@disk.command()
@click.option("--image", help='The name of the disk image file', required=True)
@click.option("--swechars", help="Decode tokens as Swedish characters", default=False, is_flag=True)
def list(image, swechars):
    disk_viewer.show(image, swechars)

@disk.command()
@click.option("--image", help='The name of the disk image file', required=True)
@click.option("--file", help='The name of the file on the disk image to view')
@click.option("--tracks", help='The track ids to view')
@click.option("--swechars", help="Decode tokens as Swedish characters", default=False, is_flag=True)
def view(image, file=None, tracks=None, swechars=False):
    disk = Disk(image)
    if file:
        try:
            f = disk.get_file(file, swechars)
        except Exception as e:
            logging.exception(e)
            click.echo(f"Failed to load {file} from disk image")
            raise click.Abort()
        data = f.read()
    else:
        data = bytes()
        for track_num in map(int, tracks.split(',')):
            data += disk.tracks[track_num]

    lines = basic_tokenizer.detokenize(data, swechars)
    for line in lines:
        print(line)
