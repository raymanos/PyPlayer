# -*- coding: utf-8 -*-
import _sqlite3 as sqlite
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
import os
import fnmatch
from os.path import getsize
from PyQt4.QtCore import QDir
from os.path import basename

"""AddToCollection(all tags)"""
version = 0.0001
Debug_ = 1

def debug(text):
	if Debug_:
		print(text)

class CreateDatabase:
    def __init__(self,drop):
        #ProgramTable: DateStart,MusicSearchStart
        self.connection = sqlite.Connection('music.db')
        self.cursor = self.connection.cursor()
        self.cursor.execute('select name from SQLITE_MASTER where name = "music"')
        if self.cursor.fetchone() is None:
            self.createTableMusic()
            debug('This is first start! Make Library')
        else:
            if (drop):
                debug('Drop table music')
                self.dropTable('music')
                self.createTableMusic()

        self.progress = 0
        self.dirCount = 0

    def dropTable(self, table):
        self.cursor.execute('drop table '+table)

    def createTableMusic(self):
        self.cursor.execute('create table music (id integer primary key, artist varchar(30),\
        album varchar(30),title varchar(30),date varchar(15),genre varchar(20),\
        track varchar(10),path varchar(50), cover_path varchar(50),play_time varchar(10),\
        file_size varchar(10), stars varchar(3), plays varchar(10))')

    def CoverFind(self, directory):
        if os.path.exists(directory + '\\' + 'cover.jpg'):
            return directory + '\\' + 'cover.jpg'

        items = os.listdir(directory)
        covers = fnmatch.filter(items,'*.jpg')
        #for cover in covers:
        if covers.__len__() != 0:
            return directory + '\\' + covers[0]  #возвращаем первый найденный jpeg
        else:
            return 'default.jpg'

    def getTags(self, fullpath, path):
        tag_list=[]
        try:
            audio = EasyID3(fullpath)
        except ID3NoHeaderError:
            debug('!Error! Id3 tags missing. File: '+fullpath)
        info_track = MP3(fullpath)

        #если нет тегов: title-берем из имени файла
        #------ARTIST-----
        try:
            art = audio['artist'][0]
            tag_list.append(art)
            #debug(art)
        except:
            tag_list.append('No_Artist')
            #debug('No_Artist')
        #------ALBUM-------
        try:
            alb = audio['album'][0]
            tag_list.append(alb)
            #debug(alb)
        except:
            tag_list.append('No_Album')
            #debug('No_Album')
        #-----TITLE-------
        try:
            tit = audio['title'][0]
            tag_list.append(tit)
            #debug(tit)
        except:
            tag_list.append(basename(fullpath))
            #debug(basename(fullpath))
        #Genre
        try:
            gen = audio['genre'][0]
            tag_list.append(gen)
            #debug(gen)
        except:
            tag_list.append('No_Genre')
            #debug(basename(fullpath))

        try:
            dat = audio['date'][0]
            tag_list.append(dat)
            #debug(dat)
        except:
            tag_list.append('')
            #debug('')

        try:
            tra = audio['tracknumber'][0]
            tag_list.append(tra)
            #debug(tra)
        except:
            tag_list.append('')
            #debug('')

        tag_list.append( fullpath.decode('cp1251') )
        tag_list.append( self.CoverFind(path.decode('cp1251')) )
        tag_list.append( self.S2HMS(info_track.info.length))
        tag_list.append( getsize(fullpath) )
        debug(fullpath.decode('cp1251'))
        tag_list.append( '0' )#оценка(по умолчанию 0)
        tag_list.append( '0' )#колчиество проигрываний
        return tag_list


    def ScanFolders(self, PathCollection):
        fullpath = ''
        cover_path = ''
        countAddedFiles = 0
        countIgnoredFiles = 0
        ignoredFiles=[]

        if os.path.exists(PathCollection):
            self.dirCount = QDir(PathCollection).count()
            #debug(self.progress)

            for path, files, dirs in os.walk(PathCollection):
                for name in dirs:
                    #Windows way
                    fullpath = path + '\\' + name
                    #Linux way
                    #fullpath = path + '/' + name
                    if not os.path.exists(fullpath):
                        debug('NOT EXISTS-'+fullpath)
                    if name[-3:] == 'mp3':
                        try:
                            if getsize(fullpath) > 0:
                                tag_list = self.getTags(fullpath,path)
                                #self.AddToCollection(tag_list)
                                countAddedFiles += 1

                        except:
                            ignoredFiles.append(fullpath)
                            countIgnoredFiles += 1
                            debug('Error[getsize]: Incorrect filename. '+fullpath)


                if(self.progress < self.dirCount):
                    self.progress += 1
                else:
                    self.progress = self.dirCount
                print(str(self.progress)+'/'+str(self.dirCount))
        debug('Files added: '+str(countAddedFiles))
        debug('Ignored files('+str(countIgnoredFiles)+')')
        debug('\n'.join(ignoredFiles))


    def AddToCollection(self,tag_list):
        query = u'insert into music (artist,album,title,genre,date,track,path,cover_path,\
        play_time,file_size,stars,plays) values (?,?,?,?,?,?,?,?,?,?,?,?)'
        self.cursor.execute(query,\
        (tag_list[0],tag_list[1],tag_list[2],tag_list[3],tag_list[4],tag_list[5],\
        tag_list[6],tag_list[7],tag_list[8],tag_list[9],tag_list[10],tag_list[11]))
        self.connection.commit()
	
    def getTrackToList(self, title):
        self.cursor.execute('select path from music where title="+title+"')
        filename = self.cursor.fetchone()
        debug(filename)
        return filename

    def QueryToCollection(self, query):
        listQuery = []
        self.cursor.execute(query)
        items = self.cursor.fetchall()
        for item in items:                  #перебор всех элементов в выдаче
            listQuery.append(item[0])

        return listQuery

    def getArtists(self):
        debug('start art')
        artistList = []
        self.cursor.execute('select distinct artist from music')
        artists = self.cursor.fetchall()
        for artist in artists:
            artistList.append(artist[0])
            debug(artist)
        return artistList
		
    def S2HMS(self,t):
    #Converts seconds to a string formatted H:mm:ss
        if t > 3600:
            h = int(t/3600)
            r = t-(h*3600)
            m = int(r / 60)
            s = int(r-(m*60))
            return '{0}:{1:02n}:{2:02n}'.format(h,m,s)
        else:
            m = int(t / 60)
            s = int(t-(m*60))
            return '{0}:{1:02n}'.format(m,s)