# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.phonon import Phonon

from ui_mainwindow import Ui_MainWindow
#from ui_progresswindow import Ui_progressDialog
#from ui_settingswindow import Ui_SettingsWindow
#import testray

import time
import pickle
from DBOperation import CreateDatabase
import os

version = 0.0002
musicPath = ''
global nameFile
form = None
DEFAULT_COVER = '\icons\\nocover.jpg'


##------------------------------------------------------------------------------
class TWindow(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        self.setWindowTitle('PyPlayer!')
        #-----------------------------------
        self.m_media = None
        self.currentRow = 0
        self.coverImage.setScaledContents(1)
        #-----------------------------------
        #Подключение к коллекции
        self.Coll = CreateDatabase(0)
        #Заполняем artistList, albumList, titleList
        self.getArtist()
##        self.getAlbum()
        self.delayedInit()
        #Загружаем настройки
        self.readSettings()
##        self.m_media.pause()

        #Подключаем обработчики
        self.connect(self.pushButton,QtCore.SIGNAL("clicked()"),self.play)#phononPlay
        self.artistList.itemClicked.connect(self.getAlbum)
        self.albumList.itemClicked.connect(self.getTracks)
        self.titleList.itemClicked.connect(self.getTracksToView)
        self.tableWidget.itemDoubleClicked.connect(self.tableWidgetClick)
        self.playButton.clicked.connect(self.PlayPausePlayer)
        self.stopButton.clicked.connect(self.StopPlayer)
        self.pushButton.clicked.connect(self.playNextTrack)
        self.prevButton.clicked.connect(self.playPrevTrack)
        self.newPlsButton.clicked.connect(self.generateM3U)
        self.clearPlsButton.clicked.connect(self.clearPlaylist)

        #показываем фс
        model = QFileSystemModel()
        model.setRootPath('C:\\')
        self.treeView.setModel(model)
        self.loadM3U()

    def closeEvent(self, event):
        self.writeSettings()
    def keyPressEvent(self, e):
        #----CTRL+1,2,3,4,5-------------
        if e.key() == QtCore.Qt.Key_1:
            if (e.modifiers() & QtCore.Qt.CTRL):
                print 'Ctrl+1'
        if e.key() == QtCore.Qt.Key_2:
            if (e.modifiers() & QtCore.Qt.CTRL):
                print 'Ctrl+2'
        if e.key() == QtCore.Qt.Key_3:
            if (e.modifiers() & QtCore.Qt.CTRL):
                print 'Ctrl+3'
        if e.key() == QtCore.Qt.Key_4:
            if (e.modifiers() & QtCore.Qt.CTRL):
                print 'Ctrl+4'
        if e.key() == QtCore.Qt.Key_5:
            if (e.modifiers() & QtCore.Qt.CTRL):
                print 'Ctrl+5'
            #оценка 1 звезда
            #update запись в бд




    def tock(self, time):
        time = time/1000
        h = time/3600
        m = (time-3600*h) / 60
        s = (time-3600*h-m*60)
        self.lcdNumber.display('%02d:%02d:%02d'%(h,m,s))

#--------------Инит для плеера--------------------------------------------------
    def delayedInit(self):
        if not self.m_media:
            print 'Player\'s init!'
            self.m_media = Phonon.MediaObject(self)
            self.audioOutput = Phonon.AudioOutput(Phonon.MusicCategory, self)
            Phonon.createPath(self.m_media, self.audioOutput)
            self.m_media.setTickInterval(100)
            self.m_media.tick.connect(self.tock)
            self.seekSlider.setMediaObject(self.m_media)
            self.volumeSlider.setAudioOutput(self.audioOutput)
            self.m_media.aboutToFinish.connect(self.playNextTrack)

    def PlayPausePlayer(self):
        if (self.m_media.state() == 2):
            self.m_media.pause()
            self.playButton.setIcon(QIcon('Icons\control_play_blue.png'))
        else:
            self.m_media.play()
            self.playButton.setIcon(QIcon('Icons\control_pause_blue.png'))

    def StopPlayer(self):
        self.m_media.stop()


    def play(self, path):
        self.delayedInit()
        if os.path.exists(path):
            print 'Path exists!'
        else:
            print 'Path NOT exists!'
        print path
        self.m_media.setCurrentSource(Phonon.MediaSource(path))
        self.m_media.play()

        #ставим обложку трека
        self.album = unicode(self.tableWidget.item(self.oldRow,3).text())
        aList = self.Coll.QueryToCollection('select cover_path from music where album="'\
            +unicode(self.album)+'"')
        self.coverImage.setScaledContents(1)
        self.coverImage.setPixmap(QPixmap(aList[0]))

#---------------Сохранение/Загрузка---------------------------------------------
    def writeSettings(self):
        settings = QtCore.QSettings('settings.ini',QtCore.QSettings.IniFormat)
        settings.beginGroup('MainWindow')
        settings.setValue('size',self.size())
        settings.endGroup()
        settings.beginGroup('tableWidget')
        settings.setValue('rowCount', self.tableWidget.rowCount())
        settings.setValue('currentRow',self.tableWidget.currentRow())
        settings.setValue('oldRow', self.oldRow)
        row_str = ''
        for row in xrange(self.tableWidget.rowCount()):
            for col in xrange(self.tableWidget.columnCount()):
                if self.tableWidget.item(row,col) != None:
                    row_str += self.tableWidget.item(row,col).text()+';'
                else:
                    row_str += ';'
            settings.setValue(str(row), unicode(row_str))
            row_str = ''
        settings.endGroup()

        settings.beginGroup('Lists')
        settings.setValue('artistListCurRow',self.artistList.currentRow())
        settings.setValue('albumListCurRow',self.albumList.currentRow())
        settings.setValue('titleListCurRow',self.titleList.currentRow())
        settings.endGroup()

        settings.beginGroup('Player')
        settings.setValue('currentTime',self.m_media.currentTime())
        settings.setValue('currentSource',self.m_media.currentSource().fileName())
        settings.setValue('currentVolume',self.audioOutput.volume())
        settings.endGroup()

        settings.beginGroup('lcdNumber')
        settings.setValue('displayStr',self.lcdNumber.value())
        settings.endGroup()
        settings.beginGroup('cover')
        #получаем обложку из бд
        print self.oldRow
        self.album = unicode(self.tableWidget.item(self.oldRow,3).text())
        print self.album
        aList = self.Coll.QueryToCollection('select cover_path from music where album="'\
            +unicode(self.album)+'"')
        if len(aList) > 0:
            settings.setValue('coverImage',aList[0])
        else:
            settings.setValue('coverImage',DEFAULT_COVER)
        settings.endGroup()

        settings.beginGroup('System')
        global musicPath
        settings.setValue('MusicPath',musicPath)
        settings.endGroup()

    def readSettings(self):
        settings = QtCore.QSettings('settings.ini',QtCore.QSettings.IniFormat)
        settings.beginGroup('MainWindow')
        self.resize(settings.value('size',QSize(400,400)).toSize())
        settings.endGroup()
        settings.beginGroup('System')
        global musicPath
        musicPath = settings.value('MusicPath').toString()
        settings.endGroup()
        settings.beginGroup('tableWidget')
        self.oldRow = settings.value('oldRow',0).toInt()[0]
        self.tableWidget.setRowCount( settings.value('rowCount').toInt()[0])
        row_list=[]
        row_str =''
        for row in xrange(self.tableWidget.rowCount()):
            row_str = unicode( settings.value(str(row),'roy').toString())
            row_list = row_str.split(';')
            for col in xrange(self.tableWidget.columnCount()):
                newItem = QTableWidgetItem(unicode(row_list[col]))
                self.tableWidget.setItem(row,col,newItem)
        settings.endGroup()

        settings.beginGroup('Player')
        print settings.value('currentTime').toInt()[0]
        self.m_media.seek( settings.value('currentTime').toInt()[0])
        self.m_media.setCurrentSource(Phonon.MediaSource(settings.value('currentSource').toString()) )
        self.audioOutput.setVolume( settings.value('currentVolume').toFloat()[0])
        settings.endGroup()

        settings.beginGroup('cover')
        s = settings.value('coverImage').toString()
        print 'S = ',s
        self.coverImage.setPixmap(QPixmap(s))
        settings.endGroup()

        settings.beginGroup('Lists')
        self.artistList.setCurrentRow( settings.value('artistListCurRow').toInt()[0] )
        self.albumList.setCurrentRow( settings.value('albumListCurRow').toInt()[0] )
        self.titleList.setCurrentRow( settings.value('titleListCurRow').toInt()[0] )
        settings.endGroup()
#-------------------------------------------------------------------------------

    def AppendToList(self):
##        print self.artistList.item(self.artistList.currentRow()).text()
##        self.artistList.addItem(self.lineEdit.text())
        self.artist = self.artistList.currentItem().text()

    def showSplash(self,splash):
        splash.showMessage('Loadng')
        QtGui.qApp.processEvents()

    def showProgress(self):
        progressWindow = QtGui.QWidget(self, flags=QtCore.Qt.SubWindow)
##        progressWindow.setWindowFlags(QtCore.Qt.SubWindow)
        progressWindow.setWindowTitle('Progress...')
        progressWindow.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        progressWindow.resize(200,90)
        progressWindow.show()


    def getArtist(self):
        self.artistList.clear()
        aList = self.Coll.QueryToCollection('select distinct artist from music')
        for item in aList:
            self.artistList.addItem(item)

    def getAlbum(self):
        self.artist = self.artistList.currentItem().text()
        self.albumList.clear()
        aList = self.Coll.QueryToCollection('select distinct album from music where artist="'+unicode(self.artist)+'"')
        for item in aList:
            self.albumList.addItem(item)

    def getTracks(self):
        self.album = self.albumList.currentItem().text()
        self.titleList.clear()
        aList = self.Coll.QueryToCollection('select title from music where album="'\
            +str(self.album)+'" and artist="'+self.artist.decode('cp1251')+'"')
        for item in aList:
            self.titleList.addItem(item)
    def getTracksToView(self):
        curRow = self.tableWidget.rowCount()
        print 'curRow = ',curRow
        self.tableWidget.setRowCount(curRow+1)

        curCol = 0
        self.title = self.titleList.currentItem().text()

        aList = self.Coll.QueryToCollection('select track from music where title="'\
            +unicode(self.title)+'"')
        print aList[0]
        newItem = QTableWidgetItem(aList[0])
        self.tableWidget.setItem(curRow,curCol,newItem)

        curCol+=1
        newItem = QTableWidgetItem(self.title)
        self.tableWidget.setItem(curRow,curCol,newItem)

        curCol+=1
        aList = self.Coll.QueryToCollection('select artist from music where title="'\
            +unicode(self.title)+'"')
        print aList[0]
        newItem = QTableWidgetItem(aList[0])
        self.tableWidget.setItem(curRow,curCol,newItem)

        curCol+=1
        aList = self.Coll.QueryToCollection('select album from music where title="'\
            +unicode(self.title)+'"')
        print aList[0]
        newItem = QTableWidgetItem(aList[0])
        self.tableWidget.setItem(curRow,curCol,newItem)

        curCol+=1
        aList = self.Coll.QueryToCollection('select play_time from music where title="'\
            +unicode(self.title)+'"')
        print aList[0]
        newItem = QTableWidgetItem(aList[0])
        self.tableWidget.setItem(curRow,curCol,newItem)

        curCol+=1
        aList = self.Coll.QueryToCollection('select date from music where title="'\
            +unicode(self.title)+'"')
        print aList[0]
        newItem = QTableWidgetItem(aList[0])
        self.tableWidget.setItem(curRow,curCol,newItem)

        curCol+=1
        aList = self.Coll.QueryToCollection('select genre from music where title="'\
            +unicode(self.title)+'"')
        print aList[0]
        newItem = QTableWidgetItem(aList[0])
        self.tableWidget.setItem(curRow,curCol,newItem)


        curCol+=1
        aList = self.Coll.QueryToCollection('select file_size from music where title="'\
            +unicode(self.title)+'"')
        newItem = QTableWidgetItem(aList[0])
        self.tableWidget.setItem(curRow,curCol,newItem)

        curCol+=1
        aList = self.Coll.QueryToCollection('select path from music where title="'\
            +unicode(self.title)+'"')
        print aList[0]
        newItem = QTableWidgetItem(aList[0])
        self.tableWidget.setItem(curRow,curCol,newItem)

    def playNextTrack(self):
        #УБИРАЕМ иконку "воспроизведения"
        self.tableWidget.item(self.oldRow,0).setIcon(QIcon(QPixmap('')))
        if (self.tableWidget.item(self.oldRow+1,8).text() != ''):
            #получаем путь из таблицы. ЕСЛИ он есть, иначе из БД
            path = self.tableWidget.item(self.oldRow+1,8).text()
            #СТАВИМ иконку "воспроизведения"
            self.tableWidget.item(self.oldRow+1,0).setIcon(QIcon(QPixmap('Icons/select_play.png')))
            self.play(path)
        else:
            print 'Field is null'
        self.oldRow += 1
##        print 'Old row=',self.oldRow
##        print 'Current row=',self.tableWidget.currentRow()
##        path = unicode(self.tableWidget.item(self.oldRow+1,8).text())
##        print path
##        print unicode(self.tableWidget.item(0,8).text())
##        self.play(path)
    def playPrevTrack(self):
        #убираем иконку "воспроизведения"
        self.tableWidget.item(self.oldRow,0).setIcon(QIcon(QPixmap('')))
        if (self.tableWidget.item(self.oldRow-1,8).text() !=''):
            path = self.tableWidget.item(self.oldRow-1,8).text()
            #ставим иконку "воспроизведения"
            self.tableWidget.item(self.oldRow-1,0).setIcon(QIcon(QPixmap('Icons/select_play.png')))
            self.play(path)
        else:
            print 'Field is empty'
        self.oldRow -= 1

    def tableWidgetClick(self):
        #запоминаем текущую строку
        self.oldRow = self.tableWidget.currentRow()
        #получаем название трека из таблицы и по нему делаем запрос->получаем полный путь
        self.title = unicode(self.tableWidget.item(self.tableWidget.currentRow(),1).text())
        aList = self.Coll.QueryToCollection('select path from music where title="'\
            +unicode(self.title)+'"')
        #проигрываем указанный путь
        print 'Play!'
        self.play(aList[0])

    def generateM3U(self,filename=u'Pls/main.m3u'):
        #колонки: название - 1; артист - 2; длина - 4; путь - 8;
        fp = file(filename, "w")
        fp.write("#EXTM3U\n")
        for row in xrange(self.tableWidget.rowCount()):
##            str1 += self.tableWidget.item(row,col).text()
            #получаем данные для формрования m3u
            title = self.tableWidget.item(row,1).text()
            artist = self.tableWidget.item(row,2).text()
            track_length = self.tableWidget.item(row,4).text()
            full_path = self.tableWidget.item(row,8).text()
            #формируем m3u плейлист
            fp.write("#EXTINF" + ":" + track_length + "," +\
                             artist + " - " + title + "\n")
            fp.write(full_path + "\n")
        fp.close()
    def loadM3U(self, filename=u'Pls/main.m3u'):
        pass


    def clearPlaylist(self):
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)


def main():
    app = QtGui.QApplication(sys.argv)
    #Подключаем стили css
    #app.setStyleSheet(open("style.css","r").read())
    global form

    splash = QtGui.QSplashScreen(QtGui.QPixmap('splash.png'))
    splash.show()
    QtGui.qApp.processEvents()
    form = TWindow()

    form.showSplash(splash)
    form.show()

    splash.finish(form)
    app.exec_()

if __name__ == "__main__":
    main()