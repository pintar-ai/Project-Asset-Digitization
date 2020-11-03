# --------------------------------------------------------
# Fast R-CNN
# Copyright (c) 2015 Microsoft
# Licensed under The MIT License [see LICENSE for details]
# Written by Ross Girshick
# Edited by GMNX
# --------------------------------------------------------

"""Set up paths for Fast R-CNN."""

import os
import sys

def add_path(path):
    if path not in sys.path:
        sys.path.insert(0, path)

this_dir = os.path.dirname(__file__)

faster_rcnn_path = "/media/ibrahim/Data/faster-rcnn"
if not os.path.isdir(faster_rcnn_path):
        faster_rcnn_path = "/opt/py-faster-rcnn" #docker mode

# Add caffe to PYTHONPATH
caffe_path = faster_rcnn_path+"/caffe-fast-rcnn/python/"
add_path(caffe_path)

# Add lib to PYTHONPATH
lib_path = faster_rcnn_path+"/lib/"
add_path(lib_path)
