# NVENC H.264 Video Reader
Nvidia NVENC accelerated video decoder in python using PyAV and Video Processing Framework (VPF)

This repository implements a hardware accelerated h264 video stream reader. WORK IN PROGRESS.

## Build

```bash
git clone git@github.com:isarsoft/nvenc-h264-video-reader.git
cd nvenc-h264-video-reader
docker build . -t nvenc-videoreader
```

## Run

```bash
# Allow connections to x server
xhost +

# Open a bash in container
docker run -it --rm -v $(pwd):/app/home -e DISPLAY=$DISPLAY -e QT_X11_NO_MITSHM=1 \
    -v /tmp/.X11-unix:/tmp/.X11-unix pyav-build /bin/bash

# In container at this point
python example.py
```