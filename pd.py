

# Copyright (c) 2019 Gurjit Singh

# This source code is licensed under the MIT license that can be found in
# the accompanying LICENSE file or at https://opensource.org/licenses/MIT.


import sys
import datetime
import pathlib
import argparse

from tinytag import TinyTag


def parseArgs():

    def dirPath(pth):
        pthObj = pathlib.Path(pth)
        if pthObj.is_dir():
            return pthObj
        else:
            raise argparse.ArgumentTypeError("Invalid Directory path")

    parser = argparse.ArgumentParser(description="Generate an RSS feed \
                                     from audio files located within a \
                                     specified folder.")
    parser.add_argument("dir", metavar="DirPath",
                        help="Directory path", type=dirPath)
    pargs = parser.parse_args()

    return pargs


class Config:

    ext = (".mp3", ".m4a", ".ogg", ".aac")

    audioType = {".mp3" : "audio/mpeg", ".m4a" : "audio/x-m4a",
                 ".ogg" : "audio/ogg", ".aac" : "audio/x-aac"}

    outFile = "feed.xml"

    url = "http://10.1.1.9/"

    artwork = "artwork.jpg"

    @staticmethod
    def fakeDate(i):
        date = datetime.datetime(2009, 1, 1, 10, 10, 10)
        timedelta = datetime.timedelta(days=float(i), hours=float(i))
        fDate = (date + timedelta)
        return str(fDate.strftime("%a, %d %b %Y %H:%M:%S GMT"))


class FeedDir:

    def __init__(self, pargs):

        self.path = pargs.dir.resolve()

        self.name = self.path.name

        self.outFile = self.path.joinpath(Config.outFile)

        self.files = [file for file in self.path.iterdir()
                      for ext in Config.ext if file.suffix == ext]


class Tag:

    def __init__(self, file):

        self.get = TinyTag.get(file)

        self._lst = (self.get.album, self.get.title, self.get.albumartist,
                     self.get.artist, self.get.track)


        self._lststrp = [bool(((str(x)).rstrip()).replace("None", ""))
                         for x in self._lst]

        self.skip = not all(self._lststrp)


class FeedGen:

    closer = """
    </channel>
</rss>

    """

    @staticmethod
    def feed(albumTitle, albumAuthor, url):
        return """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:content="http://purl.org/rss/1.0/modules/content/">


    <channel>
        <title>{albumTitle}</title>
        <language>en-us</language>
        <itunes:author>{albumAuthor}</itunes:author>
        <itunes:explicit>false</itunes:explicit>
        <itunes:type>serial</itunes:type>
        <itunes:image href="{url}{artwork}" />

        """.format(albumTitle=albumTitle, albumAuthor=albumAuthor,
                   url=url, artwork=Config.artwork).rstrip(" ")


    @staticmethod
    def perTrack(title, filename, atype, size, author, duration, num, url):
        dtmin = datetime.datetime.min
        timedelta = datetime.timedelta(seconds=int(duration))
        time = (dtmin + timedelta)
        return """
        <item>
            <title>{title}</title>
            <itunes:title>{title}</itunes:title>
            <enclosure url="{url}{filename}" type="{atype}" length="{size}"/>
            <guid>"{url}{filename}"</guid>
            <itunes:author>{author}</itunes:author>
            <itunes:duration>{duration}</itunes:duration>
            <itunes:explicit>false</itunes:explicit>
            <itunes:episode>{num}</itunes:episode>
            <pubDate>{fakeDate}</pubDate>
        </item> 

        """.format(title=title, filename=filename,
                   atype=atype, size=size,
                   author=author, num=num,
                   duration=str(time.strftime("%H:%M:%S")),
                   url=url, fakeDate=Config.fakeDate(num))


def main():

    feedDir = FeedDir(parseArgs())

    if not feedDir.files:
        print("No Audio Files found.")
        sys.exit()

    perTrack = ""
    count = 0
    url = Config.url + feedDir.name + "/"

    for file in feedDir.files:
        tag = Tag(str(file))
        if tag.skip:
            print("Skipped " + file.name)
            continue

        args = {"filename" : file.name,
                "size" : file.stat().st_size,
                "title" : tag.get.title,
                "author" : tag.get.artist,
                "duration" : tag.get.duration,
                "num" : tag.get.track,
                "atype" : Config.audioType[(file.suffix)],
                "url" : url}

        perTrack += (FeedGen.perTrack(**args))

        count += 1
        if count == 1:
            feedOut = FeedGen.feed(albumTitle=tag.get.album, url=url,
                                   albumAuthor=tag.get.albumartist,)

        print("Added " + file.name)

    if not perTrack:
        print("Invalid Audio files or missing tags")
        sys.exit()

    feedFile = (feedOut + perTrack + FeedGen.closer)

    print(f"\nAdded { count } files")

    with open((feedDir.outFile), "w") as file:
        file.write(feedFile)


main()
