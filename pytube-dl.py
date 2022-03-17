import pytube
import googleapiclient.discovery
import os
import re
import subprocess
import requests
import shutil
import eyed3
import config
import argparse
from eyed3.id3.frames import ImageFrame
from urllib.parse import parse_qs, urlparse
from pytube import YouTube
from pytube import Playlist

# global var declared in generateURLS(), is equal to the name of the playlist and used to tell function where to store data
directory = ""

def generateURLs(url):
    urlList = []

    # tell python to use global var
    global directory
    directory = Playlist(url).title

    # playlist url to extract sigle video urls from
    query = parse_qs(urlparse(url).query, keep_blank_values=True)
    playlist_id = query["list"][0]
    print(f'get all playlist items links from {directory}')

    # use google dev key to interact with goole discovery based API
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey = config.getDevKey())

    # api results top out at a maximum of 50
    request = youtube.playlistItems().list(
        part = "snippet",
        playlistId = playlist_id,
        maxResults = 50
    )
    response = request.execute()

    # as long as we havent gotten all playlist items start the request again
    playlist_items = []
    while request is not None:
        response = request.execute()
        playlist_items += response["items"]
        request = youtube.playlistItems().list_next(request, response)

    # create links for each YouTube video and append it to a list
    print(f"total: {len(playlist_items)}") 
    for item in playlist_items:
        urlList.append(f'https://www.youtube.com/watch?v={item["snippet"]["resourceId"]["videoId"]}')
    return urlList

# function to download each video
def download(urlList):
    for item in enumerate(urlList):
        yt = YouTube(str(item))
        try:
            print("Downloading {} ...".format(yt.title))
            print("Audio Stream: {}".format(yt.streams.filter(only_audio=True).last()))

            # last audio stream is usually the one with the highest quality
            yt.streams.filter(only_audio=True).last().download("./{}".format(directory))

            # get thumbnail URL for album art
            imgUrl = yt.thumbnail_url
            r = requests.get(imgUrl, stream=True)
            r.raw.decode_content = True
            with open("./{}/thumbnail.jpg".format(directory), "wb") as f:
                shutil.copyfileobj(r.raw, f)
            
            # convert .webm to mp3
            convert()

            print("Done!\n")
        
        # exceptions
        except pytube.exceptions.VideoPrivate as err:
            print("Could not acces Video {} because {}".format(item, err))
        except pytube.exceptions.VideoUnavailable as err:
            print("Could not acces Video {} because {}".format(item, err))
        except Exception as excep:
            print("excep :" + excep + " occured")

# function to convert .webm to .mp3
def convert():
    for f in os.listdir(directory):
        path = directory + "/" + f
        if f.endswith(".webm"):
            # construct mp3 name
            mp3Name = f[:-5] + ".mp3"

            # convert .webm to .mp3 using ffmpeg
            print("Converting {} from .webm to .mp3...".format(f))
            subprocess.check_call(["ffmpeg", "-i", directory + "/" + f, "-ar", "44100", "-ac", "2", "-b:a", "192k", 
                                    directory + "/" + f[:-5] +".mp3"], stdout=open(os.devnull, 'wb'), stderr=subprocess.STDOUT)     

            # remove .webm file              
            os.remove(path)

            # add adlbum art
            addAlbumArt(str(mp3Name))
    
# function to add album art to song
def addAlbumArt(filename):
    print("Adding Thumbnail to {} ...".format(filename))
    path = directory + "/" + filename
    audiofile = eyed3.load(path)
    if (audiofile.tag == None):
        audiofile.initTag()
    audiofile.tag.images.set(ImageFrame.FRONT_COVER, open("./{}/thumbnail.jpg".format(directory),"rb").read(), "image/jpeg")
    audiofile.tag.save()
    os.remove("./{}/thumbnail.jpg".format(directory))


if __name__ == "__main__":
    # Initialize parser
    parser = argparse.ArgumentParser()
    
    # Adding optional argument
    parser.add_argument("-u", "--URL", help = "Add Playlist URL")
    
    # Read arguments from command line
    args = parser.parse_args()
    url = vars(args)["URL"]
    
    urlList = generateURLs(url)
    download(urlList)