import numpy as np
import io

import PyNvCodec as nvc

import av
from av.bitstream import BitStreamFilter, BitStreamFilterContext
bsfc = BitStreamFilterContext('h264_mp4toannexb')

class GPUVideoReader:
    def __init__(self, stream, gpuID=0):
        try:
            self._open = False
            self._stream = stream
            self._gpuID = gpuID
            self._num_frame = 0

            # Open container and first receivable video stream
            # rtsp tcp transport here is optional - check if you need it
            self._input_container = av.open(self._stream, options={'rtsp_transport':'tcp'})
            self._in_stream = self._input_container.streams.video[0]
            self._width, self._height = self._in_stream.codec_context.width, self._in_stream.codec_context.height
            self._framerate = self._in_stream.codec_context.framerate

            # Initialise packet buffer
            self._byte_io = io.BytesIO()
            self._byte_io.name = 'muxed.h264'
            self._out_container = av.open(self._byte_io, 'wb')
            self._out_stream = self._out_container.add_stream(template=self._in_stream)

            # Initialise hardware decoder and color conversion 
            self._nvDec = nvc.PyNvDecoder(self._width, self._height, nvc.PixelFormat.NV12, nvc.CudaVideoCodec.H264, self._gpuID)
            self._nvCvt = nvc.PySurfaceConverter(self._width, self._height, self._nvDec.Format(), nvc.PixelFormat.BGR, self._gpuID)
            self._nvDwn = nvc.PySurfaceDownloader(self._width, self._height, self._nvCvt.Format(), self._gpuID)
            
            self._open = True
            self._rawSurface = None
        except Exception as e:
            print(getattr(e, 'message', str(e)))

    def isOpened(self):
        return self._open
    
    def release(self):
        self._open = False
        self._nvDec = None
        self._nvCvt = None
        self._nvDwn = None
        self._rawSurface = None
        self._input_container.close()
        self._out_container.close()
        self._byte_io.close()

    def grab(self):
        if not self._open:
            return

        for packet in self._input_container.demux(self._in_stream):
            print("IN_PACKET")
            if packet.dts is None:
                print("EMPTY_PACKET")
                continue

            for out_packet in bsfc(packet):
                print("OUT_PACKET")
                self._out_container.mux_one(out_packet)
                self._byte_io.flush()
                enc_packet = np.frombuffer(buffer=self._byte_io.getvalue(), dtype=np.uint8)
                self._rawSurface = self._nvDec.DecodeSurfaceFromPacket(enc_packet)
                self._byte_io.seek(0)
                self._byte_io.truncate()
                if not self._rawSurface.Empty():
                    print("RECEIVED_SURFACE")
                    return

        # Probably stream ended here, return emtpy surface to indicate this
        self._rawSurface = None

    def retrieve(self):
        if not self._rawSurface or self._rawSurface.Empty():
            return 0, None
        try:
            cvtSurface = self._nvCvt.Execute(self._rawSurface)
            if (cvtSurface.Empty()):
                return 0, None

            rawFrame = np.ndarray(shape=(cvtSurface.HostSize()), dtype=np.uint8)
            success = self._nvDwn.DownloadSingleSurface(cvtSurface, rawFrame)
            if not (success):
                return 0, None

            self._num_frame += 1
            return 1, rawFrame.reshape(self._height, self._width, 3)
            
        except Exception as e:
            print(getattr(e, 'message', str(e)))
        return 0, None
    
    def read(self):
        self.grab()
        return self.retrieve()

    def framerate(self):
        if not self._open:
            return 0
        return self._framerate
    
    def width(self):
        if not self._open:
            return 0
        return self._width

    def height(self):
        if not self._open:
            return 0
        return self._height
