ARG AV_VERSION
ARG CUDA_VERSION
ARG UBUNTU_VERSION
FROM alicevision/alicevision:${AV_VERSION}-ubuntu${UBUNTU_VERSION}-cuda${CUDA_VERSION}
LABEL maintainer="AliceVision Team alicevision-team@googlegroups.com"

# Execute with nvidia docker (https://github.com/nvidia/nvidia-docker/wiki/Installation-(version-2.0))
# docker run -it --runtime=nvidia meshroom

ENV MESHROOM_DEV=/opt/Meshroom \
    MESHROOM_BUILD=/tmp/Meshroom_build \
    QT_DIR=/opt/Qt5.14.1/5.14.1/gcc_64 \
    QT_CI_LOGIN=alicevisionjunk@gmail.com \
    QT_CI_PASSWORD=azerty1.

# Workaround for qmlAlembic/qtAliceVision builds: fuse lib/lib64 folders
#RUN ln -s ${AV_INSTALL}/lib ${AV_INSTALL}/lib64

# Install libs needed by Qt
RUN apt-get update && \
	DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends \
        flex \
        fontconfig \
        libfreetype6 \
        libglib2.0-0 \ 
        libice6 \
        libx11-6 \
        libxcb1 \
        libxext6 \
        libxi6 \
        libxrender1 \
        libsm6 \
        libxt-dev \
        libglu-dev \
        libosmesa-dev \
        libgl-dev \
        libglu-dev \
	libqt5charts5-dev \
        libxcb-keysyms1 \
        libxcb-image0 \
        libxkbcommon-x11-0 \
	libz-dev \
	systemd \
	ssh

# Disabled as QTOIIO requires ah least 5.13 (5.12 available in Ubuntu 20.04)
#	qtdeclarative5-dev \
#	qt3d-assimpsceneimport-plugin \
#	qt3d-defaultgeometryloader-plugin \
#	qt3d-gltfsceneio-plugin \
#	qt3d-scene2d-plugin \
#	qt53dextras5 \
#	qt3d5-dev 
	

RUN apt-get install -y --no-install-recommends \
	software-properties-common

# Install Python3
RUN apt install python3-pip -y && pip3 install --upgrade pip

# Install Qt (to build plugins)
WORKDIR /tmp/qt
COPY dl/qt.run /tmp/qt
COPY ./docker/qt-installer-noninteractive.qs ${MESHROOM_DEV}/docker/
RUN chmod +x qt.run && \
    ./qt.run --verbose --platform minimal --script "${MESHROOM_DEV}/docker/qt-installer-noninteractive.qs" && \
    rm qt.run

COPY ./*requirements.txt ./setup.py ${MESHROOM_DEV}/

# Install Meshroom requirements and freeze bundle
WORKDIR "${MESHROOM_DEV}"
RUN pip install -r dev_requirements.txt -r requirements.txt

