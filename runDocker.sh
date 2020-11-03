#!/bin/bash
if [ $(dpkg-query -W -f='${Status}' nvidia-docker2 2>/dev/null | grep -c "ok installed") -eq 0 ]; then
	echo "Package  is NOT installed!"
	if [ $EUID != 0 ]; then
		distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
		sudo -- sh -c "wget https://nvidia.github.io/nvidia-docker/gpgkey -O nvidia.key \
		&& apt-key add nvidia.key \
		&& rm nvidia.key \
		&& wget https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list -O /etc/apt/sources.list.d/nvidia-docker.list \
		&& apt-get -y update \
		&& apt install -y nvidia-docker2 \
		&& usermod -a -G docker $USER"
		read -p "Need reboot, do you want to reboot now? (y/n)" -n 1 -r
		if [[ $REPLY =~ ^[Yy]$ ]]
		then
			echo "rebooting"
			reboot
		fi
		exit
	fi
else
	echo "Package  is installed!"
fi

if [ $EUID == 0 ]; then
	echo "need to run as normal user"
	exit
fi
xhost +local:docker
XSOCK=/tmp/.X11-unix
XAUTH=/tmp/.docker.xauth
db=~/.config/cairo/app_db.sqlite
if [ ! -f "$db" ]
then
    install -D /dev/null $db
fi
conf=~/.config/cairo/asset-digitization.conf
if [ ! -f "$conf" ]
then
    install -D /dev/null $conf
fi
#--device=/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f $XAUTH nmerge -
docker run --runtime=nvidia -it --rm -p 1935:1935 -e DISPLAY=$DISPLAY -v $XSOCK:$XSOCK -v $XAUTH:$XAUTH -e XAUTHORITY=$XAUTH -e QT_X11_NO_MITSHM=1 -v $db:/workspace/app_db.sqlite -v $conf:/root/.config/cairo/asset-digitization.conf mjiit/streetlight:turing
xhost -local:docker
