# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'MainWindow.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(1530, 738)
        self.video_label = QtGui.QLabel(Form)
        self.video_label.setGeometry(QtCore.QRect(9, 9, 1260, 720))
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.video_label.sizePolicy().hasHeightForWidth())
        self.video_label.setSizePolicy(sizePolicy)
        self.video_label.setMinimumSize(QtCore.QSize(1260, 720))
        self.video_label.setFrameShape(QtGui.QFrame.Box)
        self.video_label.setText(_fromUtf8(""))
        self.video_label.setObjectName(_fromUtf8("video_label"))
        self.formLayoutWidget = QtGui.QWidget(Form)
        self.formLayoutWidget.setGeometry(QtCore.QRect(1304, 9, 221, 241))
        self.formLayoutWidget.setObjectName(_fromUtf8("formLayoutWidget"))
        self.formLayout = QtGui.QFormLayout(self.formLayoutWidget)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.label = QtGui.QLabel(self.formLayoutWidget)
        self.label.setObjectName(_fromUtf8("label"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.label)
        self.fps_label = QtGui.QLabel(self.formLayoutWidget)
        self.fps_label.setObjectName(_fromUtf8("fps_label"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.fps_label)
        self.label_4 = QtGui.QLabel(self.formLayoutWidget)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.label_4)
        self.altitude_label = QtGui.QLabel(self.formLayoutWidget)
        self.altitude_label.setObjectName(_fromUtf8("altitude_label"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.altitude_label)
        self.label_2 = QtGui.QLabel(self.formLayoutWidget)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.label_2)
        self.latitude_label = QtGui.QLabel(self.formLayoutWidget)
        self.latitude_label.setObjectName(_fromUtf8("latitude_label"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.latitude_label)
        self.label_5 = QtGui.QLabel(self.formLayoutWidget)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.label_5)
        self.longitude_label = QtGui.QLabel(self.formLayoutWidget)
        self.longitude_label.setObjectName(_fromUtf8("longitude_label"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.longitude_label)
        self.label_3 = QtGui.QLabel(self.formLayoutWidget)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.LabelRole, self.label_3)
        self.gmt_label = QtGui.QLabel(self.formLayoutWidget)
        self.gmt_label.setObjectName(_fromUtf8("gmt_label"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.gmt_label)
        self.label_14 = QtGui.QLabel(self.formLayoutWidget)
        self.label_14.setText(_fromUtf8(""))
        self.label_14.setObjectName(_fromUtf8("label_14"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.LabelRole, self.label_14)
        self.label_7 = QtGui.QLabel(self.formLayoutWidget)
        self.label_7.setAlignment(QtCore.Qt.AlignCenter)
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.formLayout.setWidget(6, QtGui.QFormLayout.SpanningRole, self.label_7)
        self.label_8 = QtGui.QLabel(self.formLayoutWidget)
        self.label_8.setObjectName(_fromUtf8("label_8"))
        self.formLayout.setWidget(7, QtGui.QFormLayout.LabelRole, self.label_8)
        self.pressure_label = QtGui.QLabel(self.formLayoutWidget)
        self.pressure_label.setObjectName(_fromUtf8("pressure_label"))
        self.formLayout.setWidget(7, QtGui.QFormLayout.FieldRole, self.pressure_label)
        self.label_10 = QtGui.QLabel(self.formLayoutWidget)
        self.label_10.setObjectName(_fromUtf8("label_10"))
        self.formLayout.setWidget(8, QtGui.QFormLayout.LabelRole, self.label_10)
        self.temperature_label = QtGui.QLabel(self.formLayoutWidget)
        self.temperature_label.setObjectName(_fromUtf8("temperature_label"))
        self.formLayout.setWidget(8, QtGui.QFormLayout.FieldRole, self.temperature_label)
        self.sync_label = QtGui.QLabel(Form)
        self.sync_label.setGeometry(QtCore.QRect(1370, 250, 68, 17))
        self.sync_label.setText(_fromUtf8(""))
        self.sync_label.setObjectName(_fromUtf8("sync_label"))

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Asset Digitization", None))
        self.label.setText(_translate("Form", "FPS", None))
        self.fps_label.setText(_translate("Form", "0", None))
        self.label_4.setText(_translate("Form", "Altitude", None))
        self.altitude_label.setText(_translate("Form", "0", None))
        self.label_2.setText(_translate("Form", "Latitude", None))
        self.latitude_label.setText(_translate("Form", "0", None))
        self.label_5.setText(_translate("Form", "Longitude", None))
        self.longitude_label.setText(_translate("Form", "0", None))
        self.label_3.setText(_translate("Form", "GMT", None))
        self.gmt_label.setText(_translate("Form", "0", None))
        self.label_7.setText(_translate("Form", "Sensors", None))
        self.label_8.setText(_translate("Form", "Pressure", None))
        self.pressure_label.setText(_translate("Form", "0", None))
        self.label_10.setText(_translate("Form", "Temperature", None))
        self.temperature_label.setText(_translate("Form", "0", None))

