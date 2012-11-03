## {{{ http://code.activestate.com/recipes/286234/ (r1)
import os
import sys
import getopt
import mad
import ID3

__doc__ = "Generate m3u playlists (default: local dir)"

FORMAT_DESCRIPTOR = "#EXTM3U"
RECORD_MARKER = "#EXTINF"

def generate_list(name="songs_list.m3u", path=".",
                  sort=True, walk=False):
    """ generates the M3U playlist with the given file name

    and in the given path """

    fp = None

    fp = file(name, "w")
    fp.write(FORMAT_DESCRIPTOR + "\n")

    for track in mp3_list:
                if not walk:
                    track = os.path.join(path, track)
                else:
                    track = os.path.abspath(track)
                # open the track with mad and ID3
                mf = mad.MadFile(track)
                id3info = ID3.ID3(track)

                # M3U format needs seconds but
                # total_time returns milliseconds
                # hence i convert them in seconds
                track_length = mf.total_time() / 1000

                # get the artist name and the title
                artist, title = id3info.artist, id3info.title

                # if artist and title are there
                if artist and title:
                    fp.write(RECORD_MARKER + ":" + str(track_length) + "," +\
                             artist + " - " + title + "\n")
                else:
                    fp.write(RECORD_MARKER + ":" + str(track_length) + "," +\
                             os.path.basename(track)[:-4] + "\n")

                # write the fullpath
                fp.write(track + "\n")

        except (OSError, IOError), e:
            print e
    finally:
        if fp:
            fp.close()