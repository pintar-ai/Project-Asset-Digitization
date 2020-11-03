#!/usr/bin/python

import sys
import time
import json
import requests
from requests.exceptions import ConnectionError
import serial
from datetime import datetime

import signal

signal.signal(signal.SIGINT, signal.SIG_DFL)
import sys
sys.path.insert(0,"/home/ibrahim/anaconda2/lib/python2.7/site-packages") #because conda messed up PyQt4, so we fetch it directly
from PyQt4 import QtCore, QtGui, uic

import base64
import cv2
import numpy as np
from fps import FPS

from VideoDetector import VideoInferencePage

from asset_digitization_ui import Ui_Form

shouldrun=False
app = QtGui.QApplication( sys.argv )
app.setApplicationName( 'Asset Digitization' )
app.setWindowIcon(QtGui.QIcon('/workspace/client/asset-digitization.png'))

#global parameter for onboard information
var_longitude=""
var_latitude=""
var_gmt=""
var_altitude=""
var_temperature=""
var_pressure=""

#global param for db encrypt
db_key=""

#initiate database
import sqlite3
conn = sqlite3.connect('app_db.sqlite', check_same_thread=False)
conn.execute("PRAGMA foreign_keys = 1")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def init_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS data_table
    (id INTEGER PRIMARY KEY,
    altitude        TEXT    NOT NULL,
    latitude        TEXT    NOT NULL,
    longitude       TEXT    NOT NULL,
    image           TEXT    NOT NULL,
    date_taken      TIMESTAMP    NOT NULL,
    username        TEXT    NOT NULL,
    sync            BOOLEAN NOT NULL)''')
    conn.commit()

#global param for save PyQt settings
settings = QtCore.QSettings('cairo', 'asset-digitization')
randomid = settings.value('randomid').toString()

#global param for state server IP
server="http://178.128.52.9"

#LoRa Server adress
lora_device = "/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0"

#Create dialog for user login
class Login(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Login, self).__init__(parent)
        self.setWindowTitle("Asset Digitization")
        self.setWindowIcon(QtGui.QIcon('/workspace/client/asset-digitization.png'))
        self.textName = QtGui.QLineEdit(self)
        self.textName.setPlaceholderText('Username')
        self.textName.clearFocus()
        self.textPass = QtGui.QLineEdit(self)
        self.textPass.setEchoMode(QtGui.QLineEdit.Password)
        self.textPass.setPlaceholderText('Password')
        self.textPass.clearFocus()
        self.buttonLogin = QtGui.QPushButton('Login', self)
        self.buttonLogin.clicked.connect(self.handleLogin)
        self.buttonLogin.setFocus()
        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.textName)
        layout.addWidget(self.textPass)
        layout.addWidget(self.buttonLogin)

    def handleLogin(self):
        if (self.register(self.textName.text(), self.textPass.text())):
            settings.setValue('username', str(self.textName.text()))
            self.accept()
        else:
            QtGui.QMessageBox.warning(
                self, 'Error', self.message)

    def register(self, username, password):
        global settings
        url = server+"/register"

        payload = "{\n\t\"username\":\"%s\",\n\t\"password\":\"%s\"\n}"%(str(username),str(password))
        headers = {
            'Content-Type': "application/json",
            'cache-control': "no-cache",
            'Postman-Token': "2dd5710c-e9b2-4ea5-8015-c6da61a019b9"
            }

        try:
            response = requests.request("POST", url, data=payload, headers=headers)
            if response.status_code==200:
                data = response.json()
                if 'randomid' in data:
                    settings.setValue('randomid', str(data['randomid']))
                    return True
                else :
                    self.message = "Bad user or password"
                    return False
            else :
                self.message = "Bad user or password"
                return False
        except ConnectionError:
            self.message = "Check your network"
            return False
        

# Create a class for our main window
class Main(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        
        # This is always the same
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        #Sync Thread
        self.netthread=syncThread()
        self.netthread.syncstatus.connect(self.updatesync)
        self.netthread.start()

        #LoRa Stream
        self.lora = loraThread(lora_device)
        self.lora.llh_signal.connect(self.set_llh)
        self.lora.sensor_signal.connect(self.set_sensor)
        self.lora.start()
        
        #Video stream
        self.video = videoThread("rtmp://localhost/live/stream?liveStreamActive=1")
        #self.video = videoThread(1)
        self.video.newdetected.connect(self.newdetect)
        self.video.start()
        self.ui.video_label.connect(self.video,QtCore.SIGNAL('newImage(QImage)'),self.set_frame)
        self.ui.fps_label.connect(self.video,QtCore.SIGNAL('newFPS(int)'),self.set_fps)

        self.show()

    @QtCore.pyqtSlot(str,str,str)
    def set_llh(self,gmt, lat, lon):
        global var_longitude, var_latitude, var_gmt
        var_longitude=lon
        var_latitude=lat
        var_gmt=gmt

        self.ui.longitude_label.setText(lon)
        self.ui.latitude_label.setText(lat)
        self.ui.gmt_label.setText(str(gmt))

    @QtCore.pyqtSlot(str,str,str)
    def set_sensor(self,temperature, pressure, altitude):
        global var_altitude, var_temperature, var_pressure
        var_altitude=altitude
        var_pressure=pressure
        var_temperature=temperature

        self.ui.altitude_label.setText(altitude+" m")
        self.ui.temperature_label.setText(temperature+" C")
        self.ui.pressure_label.setText(pressure+" mbar")

    def set_frame(self,frame):
        pixmap = QtGui.QPixmap.fromImage(frame)
        self.ui.video_label.setPixmap(pixmap)

    def set_fps(self,fps):
        self.ui.fps_label.setText(str(fps))

    @QtCore.pyqtSlot(str)
    def newdetect(self,image):
        if not (var_altitude and var_longitude and var_latitude):
            print "you need to connected with LoRa before start to detect"
            return
        date_taken = datetime.now().replace(microsecond=0)
        username = str(settings.value('username').toString())
        sync=False
        image = str(image)
        print "\n\n\n\n\n\n===================="
        print "===================="
        print "===================="
        print "NEW IMAGE UPDATED --"
        print username
        print "===================="
        print "===================="
        print "====================\n\n\n\n\n\n"

        try:
            cursor.execute('INSERT INTO data_table (altitude,latitude,longitude,image,date_taken,username,sync) VALUES (?,?,?,?,?,?,?)',
            (var_altitude, var_latitude, var_longitude, image, date_taken, username, sync))
            conn.commit()
        except Exception as e:
            print e.message

    @QtCore.pyqtSlot(str)
    def updatesync(self,data):
        self.ui.sync_label.setText("SYNC "+data)

    def closeEvent(self, event):
        global shouldrun
        shouldrun=False

class syncThread(QtCore.QThread):
    syncstatus = QtCore.pyqtSignal(str)

    def __init__(self):
        super(syncThread,self).__init__()
        self.url = server+"/insert"

    def run(self):
        print "sync worker start syncing"
        if noconnection:
            print "sync worker cant connect to server"
        if not shouldrun:
            print "sync worker forbiden to run"
        while shouldrun and not noconnection:
            #calculate total data in DB
            cursor.execute('SELECT * FROM data_table')
            entry = cursor.fetchall()
            total=len(entry)

            cursor.execute('SELECT * FROM data_table WHERE NOT sync')
            entry = cursor.fetchall()
            notuploaded=len(entry)
            data = str(total-notuploaded)+'/'+str(total)
            self.syncstatus.emit(data)
            print "UPDATE sync status = "+data

            if entry is None:
                time.sleep(30)#try to sync every 30 second
            elif not entry:
                time.sleep(30)#try to sync every 30 second
            else :
                for row in entry:
                    altitude = row['altitude']
                    latitude = row['latitude']
                    longitude = row['longitude']
                    date_taken = row['date_taken']
                    image = row['image']
                    username = row['username']
                    id = row['id']
                    payload = "{\n\"altitude\":\"%s\",\n\"latitude\":\"%s\",\n\"longitude\":\"%s\",\n\"date_taken\":\"%s\",\n\"image\":\"%s\",\n\"username\":\"%s\"\n}"%(str(altitude),str(latitude),str(longitude),str(date_taken),str(image),str(username))
                    if self.upload(payload):
                        try :
                            cursor.execute("""UPDATE data_table SET sync=? WHERE id=?""",(True,id))
                            conn.commit()
                        except Exception as e:
                            print e.message

    def upload(self, payload):
        url = self.url
        headers = {
            'Content-Type': "application/json",
            'cache-control': "no-cache"
            }

        response = requests.request("POST", url, data=payload, headers=headers)
        data = response.json()
        if 'status' in data:
            return True
        else :
            return False


class videoThread(QtCore.QThread):
    newdetected = QtCore.pyqtSignal(str)

    def __init__(self,address):
        super(videoThread,self).__init__()
        self.video_address = address

    def image_resize(self,image, width = None, height = None, inter = cv2.INTER_AREA):
        # initialize the dimensions of the image to be resized and
        # grab the image size
        dim = None
        (h, w) = image.shape[:2]

        # if both the width and height are None, then return the
        # original image
        if width is None and height is None:
            return image

        # check to see if the width is None
        if width is None:
            # calculate the ratio of the height and construct the
            # dimensions
            r = height / float(h)
            dim = (int(w * r), height)

        # otherwise, the height is None
        else:
            # calculate the ratio of the width and construct the
            # dimensions
            r = width / float(w)
            dim = (width, int(h * r))

        # resize the image
        resized = cv2.resize(image, dim, interpolation = inter)

        # return the resized image
        return resized

    def run(self):
        #Activate Detector module
        self.detector = VideoInferencePage()

        # Create a VideoCapture object and read from input file
        # If the input is the camera, pass 0 instead of the video file name
        cap = cv2.VideoCapture(self.video_address)
        fps = None
        new_detected=[]
        # Check if camera opened successfully
        if (cap.isOpened()== False): 
            print("Error opening video stream or file")
         
        # Read until video is completed
        while(cap.isOpened() or shouldrun):
            # Capture frame-by-frame
            ret, frame = cap.read()
            if ret == True:
                if not self.detector.isready():
                    continue
                if not fps:
                    fps = FPS().start()
                elif fps.elapsed()>60:
                    fps = FPS().start()
                #feed the detector and wait for true result
                self.detector.send_frame(frame)
                result=self.detector.get_result()
                
                #Uncomment this if want to bypass the detector
                #result=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                if not isinstance(result, np.ndarray):
                    continue

                # Display the resulting frame
                convertToQtFormat = QtGui.QImage(result.data, result.shape[1], result.shape[0], QtGui.QImage.Format_RGB888)
                p = convertToQtFormat.scaled(1260, 720, QtCore.Qt.KeepAspectRatio)
                self.emit(QtCore.SIGNAL('newImage(QImage)'), p)
                fps.update()
                self.emit(QtCore.SIGNAL('newFPS(int)'), int(fps.fps()))

                passobject = self.detector.get_passingobject()
                passobject = []
                if len(new_detected)<len(passobject):
                    for objectID in passobject.keys():
                        if not objectID in new_detected:
                            new_detected.append(objectID)
                            #image parsing to base64
                            image = self.image_resize(passobject[objectID]['image'], height=300)
                            retval, buffer = cv2.imencode('.png', image)
                            image_base64 = base64.b64encode(buffer)
                            self.newdetected.emit(image_base64)

         
                # Press Q on keyboard to  exit
                if not shouldrun:
                    fps.stop()
                    self.detector.exit_detection()
                    break
         
            # restart stream
            else: 
                print "ret is false"
                if fps:
                    fps.stop()
                time.sleep(3)
                cap.release()
                cap = cv2.VideoCapture(self.video_address)
                if (cap.isOpened()== True) and fps: 
                    fps.start()
         
        # When everything done, release the video capture object
        cap.release()
         
        # Closes all the frames
        cv2.destroyAllWindows()
        
class loraThread(QtCore.QThread):
    llh_signal = QtCore.pyqtSignal(str,str,str)
    sensor_signal = QtCore.pyqtSignal(str,str,str)

    def __init__(self,device_address):
        super(loraThread,self).__init__()
        self.device_address = device_address

    def run(self):
        serial_found=False
        while shouldrun :
            msg=""
            try:
                if not serial_found:
                    ard = serial.Serial(self.device_address,9600,timeout=5)
                    serial_found=True
                else:
                    msg = ard.readline()
            except:
                serial_found=False
                print("Cannot found LoRa Server in address : "+self.device_address)
                sleeping=10
                print("wait for %s second for reconnect with LoRa"%str(sleeping))
                time.sleep(sleeping)
                continue
            
            msg = msg.replace(" ", "")
            msg = msg.replace('"', "")
            data = msg.split()
            
            if len(data)>0:
                if "llh:" in data[0]:
                    llh = data[0].split("llh:")
                    llh = llh[1].split(",")
                    if len(llh) != 3:
                        continue
                    gmt = llh[0]
                    latitude = llh[1]
                    longitude = llh[2]
                    self.llh_signal.emit(gmt,latitude,longitude)
                if "sensors:" in data[0]:
                    sensor = data[0].split("sensors:")
                    sensor = sensor[1].split(",")
                    if len(sensor) != 3:
                        continue
                    temperature = sensor[0]
                    pressure = sensor[1]
                    altitude = sensor[2]
                    self.sensor_signal.emit(temperature,pressure,altitude)
   
def validate(randomid):
        if not randomid:
            return False
        url = server+"/validate"
        
        payload = "{\n\t\"randomid\":\"%s\"\n}"%(str(randomid))
        headers = {
            'Content-Type': "application/json",
            'cache-control': "no-cache"
            }

        response = requests.request("POST", url, data=payload, headers=headers)
        data = response.json()
        if 'registered' in data:
            return True
        else :
            return False

if __name__ == "__main__":
    init_db()
    login = Login()
    isvalid = False
    noconnection = False
    try:
        isvalid = validate(randomid)
    except ConnectionError:
        if randomid:
            noconnection = True
    if isvalid or noconnection or login.exec_() == QtGui.QDialog.Accepted:
        init_db()
        shouldrun=True
        window = Main()
        window.show()

        QtCore.QObject.connect( app, QtCore.SIGNAL( 'lastWindowClosed()' ), app, QtCore.SLOT( 'quit()' ) )

        # execute application
        sys.exit( app.exec_() )