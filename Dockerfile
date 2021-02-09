FROM nvcr.io/nvidia/tensorrt:20.09-py3
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt update
RUN apt install -y git cmake wget unzip ffmpeg python3 virtualenv build-essential pkg-config python3-dev python3-pip \
    libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libswresample-dev libavfilter-dev libsm6 libxext6 libxrender-dev

# Install PyAV with bitstream support
RUN git clone https://github.com/PyAV-Org/PyAV.git
RUN cd PyAV && git checkout 44195b6
RUN /bin/bash -c "cd PyAV && source scripts/activate.sh && pip install --upgrade -r tests/requirements.txt && make"
RUN cd PyAV && pip3 install .

# Install VPF
RUN git clone https://github.com/NVIDIA/VideoProcessingFramework.git vpf
ADD Video_Codec_SDK_11.0.10.zip ./vpf
ENV CUDACXX /usr/local/cuda/bin/nvcc
RUN cd vpf && unzip Video_Codec_SDK_11.0.10.zip && \
    mkdir -p build && cd build && \
    cmake .. \
        -DFFMPEG_DIR:PATH="/usr/bin/ffmpeg" \
        -DVIDEO_CODEC_SDK_DIR:PATH="/app/vpf/Video_Codec_SDK_11.0.10" \
        -DGENERATE_PYTHON_BINDINGS:BOOL="1" \
        -DGENERATE_PYTORCH_EXTENSION:BOOL="0" \
        -DPYTHON_LIBRARY=/usr/lib/python3.6/config-3.6m-x86_64-linux-gnu/libpython3.6m.so \
        -DPYTHON_EXECUTABLE="/usr/bin/python3.6" .. \
        -DCMAKE_INSTALL_PREFIX:PATH="/app" && \
    make -j$(nproc) && make install && \
    cd /app && \
    rm -rf vpf && \
    mv bin/*.so . && rm -rf bin
ENV LD_LIBRARY_PATH=/app:${LD_LIBRARY_PATH}

# Add decode script
RUN pip install opencv-python==4.2.0.32
ADD GPUVideoReader.py .
ADD example.py .
