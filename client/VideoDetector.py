import PIL.Image
from PIL.ImageQt import ImageQt
from ctypes import *
import math
import random
import numpy as np
import threading
import os
import time
import socket
import datetime
import Queue
from centroidtracker import CentroidTracker
import _init_paths
from fast_rcnn.config import cfg
from fast_rcnn.test import im_detect
from fast_rcnn.nms_wrapper import nms
import caffe, os, sys, cv2
import multiprocessing
import argparse
import glob as glob
import dlib
import copy


class VideoInferencePage:
    def __init__(self):
        self.frame_queue=Queue.Queue(maxsize=30)
        self.detection_result=Queue.Queue(maxsize=30)
        self.ready=False
        self.image=None
        self.frame=None
        self.objects = [None, None, None, None]
        self.isobjectsupdated=False
        self.stopEvent = threading.Event()
        self.thread = threading.Thread(target=self.do_detections)
        self.thread.start()
        self.passobject={}
        print ("~~~ START TO DETECT ~~~")

        self.CLASSES = ('__background__',  # always index 0
                            'pole1', 'pole2', 'pole3', 'label')

        self.NETS = {'vgg16': ('VGG16',
                        'VGG16_faster_rcnn_final.caffemodel'),
                'zf': ('ZF',
                    'zf_faster_rcnn_iter_100000.caffemodel')}

    def parse_args(self):
        """Parse input argument s."""
        parser = argparse.ArgumentParser(description='Faster R-CNN demo')
        parser.add_argument('--gpu', dest='gpu_id', help='GPU device id to use [0]',
                            default=0, type=int)
        parser.add_argument('--cpu', dest='cpu_mode',
                            help='Use CPU mode (overrides --gpu)',
                            action='store_true')
        parser.add_argument('--net', dest='demo_net', help='Network to use [vgg16]', 
                            default='zf')

        args = parser.parse_args()

        return args

    def send_frame(self,frame):
        
        self.frame=frame

    def get_frame(self):
        return self.frame

    def send_result(self,result):
        self.image=result

    def get_result(self):
        return self.image


    def get_inventory(self):
        return self.inventory

    def send_objects(self,objects):
        self.objects=objects

    def get_objects(self):
        self.isobjectsupdated=False
        return self.objects

    def isobjectsdetected(self):
        return self.isobjectsupdated

    def isready(self):
        return self.ready

    def set_passingobject(self, objectID, image, label):
        self.passobject.update({objectID:{'image':image, 'label':label}})

    def get_passingobject(self):
        return self.passobject

    #We are not doing really face recognition
    def doRecognizePerson(self, faceNames, fid, labelNames, label,score):
        #time.sleep(2)
        faceNames[ fid ] = "ID : " + str(fid)
        labelNames[fid]={"label":label,"score":score}


    def do_detections(self):

        cfg.TEST.HAS_RPN = True  # Use RPN for proposals

        args = self.parse_args()

        this_dir = os.path.dirname(__file__)
        prototxt = os.path.join(this_dir, 'streetlight.prototxt')
        caffemodel = os.path.join(this_dir, 'streetlight.caffemodel')

        if not os.path.isfile(caffemodel):
            raise IOError(('{:s} not found.\nDid you run ./data/script/'
                        'fetch_faster_rcnn_models.sh?').format(caffemodel))

        if args.cpu_mode:
            caffe.set_mode_cpu()
        else:
            caffe.set_mode_gpu()
            caffe.set_device(args.gpu_id)
            cfg.GPU_ID = args.gpu_id
        net = caffe.Net(prototxt, caffemodel, caffe.TEST)

        print '\n\nLoaded network {:s}'.format(caffemodel)

        #The color of the rectangle we draw around the face
        rectangleColor = (0,255,0)

        #variables holding the current frame number and the current faceid
        frameCounter = 0
        currentFaceID = 0

        #Variables holding the correlation trackers and the name per faceid
        faceTrackers = {}
        faceNames = {}
        labelNames = {}


        #start here
        #labels = []
        #score1 = []
        self.ready=True
        isdimset=False
        frame=None
        #img = [None, None, None, None]
        #index = 0
        #detected = 0
        counted_id=[]
        upper_id=[]
        count=0

        #detection loop
        #while not self.stopEvent.is_set():
        try:
            while not self.stopEvent.is_set():
                if np.array_equal(frame,self.get_frame()):
                    continue
                else :
                    frame = self.get_frame()
                    
                if not isinstance(frame, np.ndarray):
                    continue
                if not isdimset:
                    width = int(frame.shape[1] * 75 / 100)
                    height = int(frame.shape[0] * 75 / 100)
                    dim = (width, height)
                    isdimset=True

                #Resize the image to 320x240
                #frame = cv2.resize(frame, (1260, 720))
                
                frame_copy = copy.deepcopy(frame)

                span = 20
                vertical_left = int(frame.shape[1]//2)-span
                vertical_right = int(frame.shape[1]//2)+span
                
                #Result image is the image we will show the user, which is a
                #combination of the original image from the webcam and the
                #overlayed rectangle for the largest face

                #STEPS:
                # * Update all trackers and remove the ones that are not 
                #   relevant anymore
                # * Every 10 frames:
                #       + Use face detection on the current frame and look
                #         for faces. 
                #       + For each found face, check if centerpoint is within
                #         existing tracked box. If so, nothing to do
                #       + If centerpoint is NOT in existing tracked box, then
                #         we add a new tracker with a new face-id

                #Increase the framecounter
                frameCounter += 1 
                if ((frameCounter % 10) == 0) or frameCounter==1:
                    scores, boxes = im_detect(net, frame)


                CONF_THRESH = 0.2
                NMS_THRESH = 0.1

                #Update all the trackers and remove the ones for which the update
                #indicated the quality was not good enough
                fidsToDelete = []
                for fid in faceTrackers.keys():
                    trackingQuality = faceTrackers[ fid ].update( frame )

                    #If the tracking quality is good enough, we must delete
                    #this tracker
                    if trackingQuality < 7:
                        fidsToDelete.append( fid )

                for fid in fidsToDelete:
                    print("Removing fid " + str(fid) + " from list of trackers")
                    faceTrackers.pop( fid , None )

                

                #Every 10 frames, we will have to determine which faces
                #are present in the frame
                if (frameCounter % 10) == 0:

                    for cls_ind, cls in enumerate(self.CLASSES[1:]):
                        cls_ind += 1  # because we skipped background
                        cls_boxes = boxes[:, 4 * cls_ind:4 * (cls_ind + 1)]
                        cls_scores = scores[:, cls_ind]
                        dets = np.hstack((cls_boxes,
                                        cls_scores[:, np.newaxis])).astype(np.float32)
                        keep = nms(dets, NMS_THRESH)
                        dets = dets[keep, :]          
                        
                        inds = np.where(dets[:, -1] >= CONF_THRESH)[0]

                        if len(inds) == 0:
                            continue

                        for i in inds:
                            bbox = dets[i, :4]
                            (x, y, w, h) = bbox.astype("int")

                            score = dets[i, -1]
                            #Loop over all faces and check if the area for this
                            #face is the largest so far
                            #We need to convert it to int here because of the
                            #requirement of the dlib tracker. If we omit the cast to
                            #int here, you will get cast errors since the detector
                            #returns numpy.int32 and the tracker requires an int
                            x_bar = int((x + w) / 2.0)
                            y_bar = int((y + h) / 2.0)

                            #Variable holding information which faceid we 
                            #matched with
                            matchedFid = None

                            #Now loop over all the trackers and check if the 
                            #centerpoint of the face is within the box of a 
                            #tracker
                            for fid in faceTrackers.keys():
                                tracked_position = faceTrackers[fid].get_position()

                                t_x = int(tracked_position.left())
                                t_y = int(tracked_position.top())
                                t_w = int(tracked_position.right())
                                t_h = int(tracked_position.bottom())

                                t_x_bar = int((t_x + t_w) / 2.0)
                                t_y_bar = int((t_y + t_h) / 2.0)

                                #check if the centerpoint of the face is within the 
                                #rectangleof a tracker region. Also, the centerpoint
                                #of the tracker region must be within the region 
                                #detected as a face. If both of these conditions hold
                                #we have a match
                                
                                if ( ( t_x <= x_bar   <= t_w) and 
                                    ( t_y <= y_bar   <= t_h) and 
                                    ( x   <= t_x_bar <= w ) and 
                                    ( y   <= t_y_bar <= h )):
                                    matchedFid = fid

                                #labels.append(cls)    

                            #If no matched fid, then we have to create a new tracker
                            if matchedFid is None:

                                print("Creating new tracker " + str(currentFaceID))
                                #Create and store the tracker 
                                tracker = dlib.correlation_tracker()
                                
                                tracker.start_track(frame,
                                                    dlib.rectangle(x, y, w, h))

                                faceTrackers[ currentFaceID ] = tracker

                                #Start a new thread that is used to simulate 
                                #face recognition. This is not yet implemented in this
                                #version :)
                                t = threading.Thread( target = self.doRecognizePerson ,
                                                    args=(faceNames,currentFaceID,labelNames, cls,score))
                                t.start()

                                #Increase the currentFaceID counter
                                currentFaceID += 1

                                #labels.append(cls)
                                #score1.append(score)




                #Now loop over all the trackers we have and draw the rectangle
                #around the detected faces. If we 'know' the name for this person
                #(i.e. the recognition thread is finished), we print the name
                #of the person, otherwise the message indicating we are detecting
                #the name of the person
                for fid in faceTrackers.keys():
                    tracked_position =  faceTrackers[fid].get_position()

                    t_x = int(tracked_position.left())
                    t_y = int(tracked_position.top())
                    t_w = int(tracked_position.right())
                    t_h = int(tracked_position.bottom())
                    x_id = int((t_x + t_w) / 2.0)
                    y_id = int((t_y + t_h) / 2.0)

                    cv2.rectangle(frame, (t_x, t_y), (t_w, t_h), rectangleColor ,2)

                    if fid in faceNames.keys():
                        cv2.putText(frame, faceNames[fid], (x_id-5, y_id-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                        cv2.circle(frame, (x_id, y_id), 3, (0, 0, 0), -1)
                        textLabel = '{:s} {:.3f}'.format(labelNames[fid]["label"], labelNames[fid]["score"])
                        labelonly = str(labelNames[fid]["label"])
                        textOrg = (t_x, t_y-2)
                        cv2.putText(frame, textLabel, textOrg, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                        if x_id > vertical_left and x_id < vertical_right:
                            count = count + 1
                            roi = frame_copy[t_y:t_h, t_x:t_w]
                            #resized_image = cv2.resize(roi, (400, 360)) 
                            #cv2.imwrite("/media/ibrahim/Data/faster-rcnn/tools/img/{}_{}.jpg".format(count, labelNames[fid]["label"]),roi)
                            #object_image = frame
                            self.set_passingobject(faceNames[fid], roi, labelonly)

                            #print "object %s inside the box %s times"%(faceNames[fid],str(count))
                        
                    else:
                        cv2.putText(frame, "Detecting..." , 
                                    (x_id-5, y_id-5), 
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5, (0, 0, 0), 2)
                        cv2.circle(frame, (x_id, y_id), 3, (0, 0, 0), -1)

                #Since we want to show something larger on the screen than the
                #original 320x240, we resize the image again
                #
                #Note that it would also be possible to keep the large version
                #of the baseimage and make the result image a copy of this large
                #base image and use the scaling factor to draw the rectangle
                #at the right coordinates.
                cv2.line(frame, ( vertical_left, 0), (vertical_left, frame.shape[0]), (0, 255, 255), 2)
                cv2.line(frame, ( vertical_right, 0), (vertical_right, frame.shape[0]), (0, 255, 255), 2)
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.send_result(image)

        #To ensure we can also deal with the user pressing Ctrl-C in the console
        #we have to check for the KeyboardInterrupt exception and break out of
        #the main loop
        except KeyboardInterrupt as e:
            pass
            

    def exit_detection(self):
        self.stopEvent.set()