FROM nvidia/cuda:10.1-cudnn7-devel-ubuntu18.04

MAINTAINER GMNX <azzam.cyber@gmail.com>

# Install dependent packages
RUN apt-get -y update
RUN apt-get install -y \
	python-pip \
        build-essential \
        cmake \
        git \
	nano \
	yasm \
        wget \
        unzip \
        libglew-dev \
    	libtiff5-dev \
    	zlib1g-dev \
    	libjpeg-dev \
    	libpng-dev \
    	libpostproc-dev \
    	libswscale-dev \
    	libeigen3-dev \
    	libtbb-dev \
    	libgtk2.0-dev \
    	pkg-config \
	python-dev \
	python-numpy \
	python-py \
	python-pytest \
	python3-dev \
	python3-numpy \
	python3-py \
	python3-pytest
RUN pip install --upgrade pip
RUN wget http://ftp.fau.de/trinity/trinity-builddeps-r14.0.0/ubuntu/pool/main/j/jasper/libjasper1_1.900.1-debian1-2.5ubuntu18.04.0+5_amd64.deb && dpkg -i libjasper1_1.900.1-debian1-2.5ubuntu18.04.0+5_amd64.deb
RUN wget http://ftp.fau.de/trinity/trinity-builddeps-r14.0.0/ubuntu/pool/main/j/jasper/libjasper-dev_1.900.1-debian1-2.5ubuntu18.04.0+5_amd64.deb && dpkg -i libjasper-dev_1.900.1-debian1-2.5ubuntu18.04.0+5_amd64.deb

# Compile and install nvidia codec header
RUN git clone https://github.com/FFmpeg/nv-codec-headers /root/nv-codec-headers && \
  cd /root/nv-codec-headers &&\
  make -j8 && \
  make install -j8 && \
  cd /root && rm -rf nv-codec-headers

# Compile and install ffmpeg from source
RUN git clone https://github.com/FFmpeg/FFmpeg /root/ffmpeg
RUN apt-get install -y \
	libavis-dev \
	libgnutls28-dev \
	libladspa-ocaml-dev \
	libass-dev \
	libbluray-dev \
	libbs2b-dev \
	libcaca-dev \
	libcdio-paranoia-dev \
	flite1-dev \
	libfontconfig1-dev \
	libfreetype6-dev \
	libfribidi-dev \
	libgme-dev \
	libgsm1-dev \
	libmp3lame-dev \
	libopenjp2-7-dev \
	libopenmpt-dev \
	libopus-ocaml-dev \
	libpulse-dev \
	librubberband-dev \
	librsvg2-dev \
	libshine-ocaml-dev \
	libsnappy-dev \
	libsoxr-dev \
	libspeex-dev \
	libssh-dev \
	libtheora-ocaml-dev \
	libtwolame-dev \
	libvorbis-ocaml-dev \
	libvpx-dev \
	libwavpack-dev \
	libwebp-dev \
	libx265-dev \
	libxml2-dev \
	libxvidcore-dev \
	libzmq3-dev \
	libzvbi-dev \
	libomxil-bellagio-dev \
	libopenal-dev \
	libglu1-mesa-dev \
	libsdl2-dev \
	libdc1394-22-dev \
	libdrm-dev \
	libavc1394-dev \
	libiec61883-dev \
	libchromaprint-dev \
	libfrei0r-ocaml-dev \
	libx264-dev 
RUN cd /root/ffmpeg && ./configure --prefix=/usr --extra-version=GMNX --toolchain=hardened --libdir=/usr/lib/x86_64-linux-gnu --incdir=/usr/include/x86_64-linux-gnu --enable-gpl --disable-stripping --enable-avisynth --enable-gnutls --enable-ladspa --enable-libass --enable-libbluray --enable-libbs2b --enable-libcaca --enable-libcdio --enable-libflite --enable-libfontconfig --enable-libfreetype --enable-libfribidi --enable-libgme --enable-libgsm --enable-libmp3lame --enable-libopenjpeg --enable-libopenmpt --enable-libopus --enable-libpulse --enable-librubberband --enable-librsvg --enable-libshine --enable-libsnappy --enable-libsoxr --enable-libspeex --enable-libssh --enable-libtheora --enable-libtwolame --enable-libvorbis --enable-libvpx --enable-libwavpack --enable-libwebp --enable-libx265 --enable-libxml2 --enable-libxvid --enable-libzmq --enable-libzvbi --enable-omx --enable-openal --enable-opengl --enable-sdl2 --enable-libdc1394 --enable-libdrm --enable-libiec61883 --enable-chromaprint --enable-frei0r --enable-libx264 --enable-nonfree --enable-pic --enable-shared --disable-static --enable-nvenc --enable-cuda --enable-cuvid --enable-libnpp --extra-cflags=-I/usr/local/cuda/include --extra-cflags=-I/usr/local/include --extra-ldflags=-L/usr/local/cuda/lib64
RUN cd /root/ffmpeg && \
	make -j10 && \
 	make install -j8 && \
  	cd /root && rm -rf ffmpeg

ENV NVIDIA_DRIVER_CAPABILITIES video,compute,utility

ARG OPENCV_VERSION=3.4.6
ARG OPENCV_INSTALL_PATH=/opencv/usr

WORKDIR /opt

USER root

## Build opencv
RUN wget https://github.com/opencv/opencv/archive/$OPENCV_VERSION.zip \
    && unzip $OPENCV_VERSION.zip \
    && mkdir opencv-$OPENCV_VERSION/build \
    && rm $OPENCV_VERSION.zip

#Install Dependency
RUN apt-get install -y \
	libv4l-dev \
	libv4l-0 \
	libopenblas-dev \
	libopenblas-base \
	liblapacke-dev \
	liblapack-dev \
	libcurl-ocaml-dev \
	curl

RUN cd opencv-$OPENCV_VERSION/build \
    && sed -i 's/\<Eigen/eigen3\/Eigen/g' ../modules/core/include/opencv2/core/private.hpp \
    && sed -i 's/SET(Open_BLAS_INCLUDE_SEARCH_PATHS/SET(Open_BLAS_INCLUDE_SEARCH_PATHS\n\/usr\/include\/x86_64-linux-gnu/g' ../cmake/OpenCVFindOpenBLAS.cmake \
    && sed -i 's/SET(Open_BLAS_LIB_SEARCH_PATHS/SET(Open_BLAS_LIB_SEARCH_PATHS\n\/usr\/lib\/x86_64-linux-gnu/g' ../cmake/OpenCVFindOpenBLAS.cmake \
    && ln -s /usr/include/x86_64-linux-gnu/cblas.h /usr/include/cblas.h \
    && cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr \
    -DBUILD_PNG=OFF \
    -DBUILD_TIFF=OFF \
    -DBUILD_TBB=OFF \
    -DBUILD_JPEG=OFF \
    -DBUILD_JASPER=OFF \
    -DBUILD_ZLIB=OFF \
    -DBUILD_EXAMPLES=OFF \
    -DBUILD_opencv_java=OFF \
    -DBUILD_opencv_python2=ON \
    -DBUILD_opencv_python3=ON \
    -DWITH_OPENCL=OFF \
    -DWITH_OPENMP=OFF \
    -DWITH_FFMPEG=ON \
    -DWITH_GSTREAMER=OFF \
    -DWITH_GSTREAMER_0_10=OFF \
    -DWITH_LIBV4L=ON \
    -DWITH_CUDA=ON \
    -DWITH_GTK=ON \
    -DWITH_VTK=OFF \
    -DWITH_TBB=ON \
    -DWITH_1394=OFF \
    -DWITH_OPENEXR=OFF \
    -DCUDA_TOOLKIT_ROOT_DIR=/usr/local/cuda-10.1 \
    -DCUDA_ARCH_BIN='5.0 5.2 6.0 6.1 7.0 7.5' \
    -DCUDA_ARCH_PTX="" \
    -DINSTALL_C_EXAMPLES=OFF \
    -DINSTALL_TESTS=OFF \
    -DENABLE_FAST_MATH=OFF \
    -DOpen_BLAS_INCLUDE_SEARCH_PATHS=/usr/include/x86_64-linux-gnu \
    -DOpen_BLAS_LIB_SEARCH_PATHS=/usr/lib/x86_64-linux-gnu \
    ..

RUN cd opencv-$OPENCV_VERSION/build \
    && make -j10 
RUN cd opencv-$OPENCV_VERSION/build \
#    && make test ARGS="--verbose --parallel 3" \
    && make install

#Build Faster-RCNN
RUN pip2 install dask pyserial dlib scikit-image protobuf easydict requests cython pyyaml --user
RUN apt-get -y update && apt-get install -y --no-install-recommends libprotobuf-dev libleveldb-dev libsnappy-dev libhdf5-serial-dev protobuf-compiler libgflags-dev libgoogle-glog-dev liblmdb-dev  libboost-all-dev python-qt4 libnginx-mod-rtmp nginx x11-apps python-setuptools python3-setuptools python3-pip
RUN pip3 install wheel
RUN pip3 install dask pyserial dlib scikit-image protobuf easydict requests cython pyyaml --user
RUN git clone https://github.com/Austriker/py-faster-rcnn.git \
	&& cd py-faster-rcnn \
#	&& rm -r caffe-fast-rcnn \ #rbgirshick Austriker --recursive
	&& git clone --branch faster-rcnn-rebased https://github.com/acmiyaguchi/caffe-fast-rcnn.git \
	&& wget https://raw.githubusercontent.com/BVLC/caffe/master/include/caffe/util/cudnn.hpp -O caffe-fast-rcnn/include/caffe/util/cudnn.hpp \
	&& mv caffe-fast-rcnn/Makefile.config.example caffe-fast-rcnn/Makefile.config \
	&& sed -i 's/margin - sqrt(dist_sq/margin - (double)sqrt(dist_sq/g' caffe-fast-rcnn/src/caffe/layers/contrastive_loss_layer.cpp

#Edit Makefile.config
RUN cd py-faster-rcnn \
	&& sed -i 's/# USE_CUDNN/USE_CUDNN/g' caffe-fast-rcnn/Makefile.config \
	&& sed -i 's/# OPENCV_VERSION/OPENCV_VERSION/g' caffe-fast-rcnn/Makefile.config \
	&& sed -i 's/\/usr\/local\/cuda/\/usr\/local\/cuda-10.1/g' caffe-fast-rcnn/Makefile.config \
	&& sed -i '/sm_20/d;/sm_21/d;/sm_30/d;/sm_35/d;/sm_52/d;/sm_60/d;/sm_61/d' caffe-fast-rcnn/Makefile.config \
	&& sed -i 's/\t\t-gencode arch=compute_50,code=sm_50/CUDA_ARCH := -gencode arch=compute_50,code=sm_50/g' caffe-fast-rcnn/Makefile.config \
	&& sed -i 's/code=sm_50 /code=sm_50 -gencode arch=compute_52,code=sm_52 /g' caffe-fast-rcnn/Makefile.config \
	&& sed -i 's/code=sm_52 /code=sm_52 -gencode arch=compute_60,code=sm_60 /g' caffe-fast-rcnn/Makefile.config \
	&& sed -i 's/code=sm_60 /code=sm_60 -gencode arch=compute_61,code=sm_61 /g' caffe-fast-rcnn/Makefile.config \
	&& sed -i 's/code=sm_61 /code=sm_61 -gencode arch=compute_70,code=sm_70 /g' caffe-fast-rcnn/Makefile.config \
	&& sed -i 's/code=sm_70 /code=sm_70 -gencode arch=compute_75,code=sm_75 /g' caffe-fast-rcnn/Makefile.config \
	&& sed -i 's/compute_61,code=compute_61/compute_75,code=compute_75/g' caffe-fast-rcnn/Makefile.config \
	&& sed -i 's/BLAS := atlas/BLAS := open/g' caffe-fast-rcnn/Makefile.config \
	&& sed -i 's/# WITH_PYTHON_LAYER/WITH_PYTHON_LAYER/g' caffe-fast-rcnn/Makefile.config \
	&& sed -i 's/\/usr\/local\/include/\/usr\/local\/include \/usr\/lib\/x86_64-linux-gnu\/hdf5\/serial\/ \/usr\/include\/hdf5\/serial\//g' caffe-fast-rcnn/Makefile.config \
	&& sed -i 's/\/usr\/local\/lib/\/usr\/local\/lib \/usr\/lib\/x86_64-linux-gnu\/hdf5\/serial\//g' caffe-fast-rcnn/Makefile.config \
	&& cat caffe-fast-rcnn/Makefile.config

#Build Cython
RUN cd py-faster-rcnn/lib \
	&& make -j6 python2
#Build Caffe
RUN cd py-faster-rcnn/caffe-fast-rcnn \
	&& make -j6 all
#Build PyCaffe
RUN cd py-faster-rcnn/caffe-fast-rcnn \
	&& make -j6 pycaffe
#Build Test Caffe
RUN cd py-faster-rcnn/caffe-fast-rcnn \
	&& mv src/caffe/test/test_smooth_L1_loss_layer.cpp src/caffe/test/test_smooth_L1_loss_layer.cpp.ori \
	&& make -j6 test

COPY nginx.conf /etc/nginx/nginx.conf

COPY run_nginx.sh /workspace/run_nginx.sh

COPY build_client /workspace/client
#COPY client /workspace/client

COPY client/deb_build/asset-digitization.png /workspace/client/asset-digitization.png

CMD ["/workspace/run_nginx.sh"]
