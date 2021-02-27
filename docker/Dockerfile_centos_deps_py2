ARG AV_VERSION
ARG CUDA_VERSION
ARG CENTOS_VERSION=7
FROM alicevision/alicevision:${AV_VERSION}-centos${CENTOS_VERSION}-cuda${CUDA_VERSION}
LABEL maintainer="AliceVision Team alicevision-team@googlegroups.com"

# Execute with nvidia docker (https://github.com/nvidia/nvidia-docker/wiki/Installation-(version-2.0))
# docker run -it --runtime=nvidia meshroom

ENV MESHROOM_DEV=/opt/Meshroom \
    MESHROOM_BUILD=/tmp/Meshroom_build \
    MESHROOM_BUNDLE=/opt/Meshroom_bundle \
    QT_DIR=/opt/Qt5.14.1/5.14.1/gcc_64 \
    QT_CI_LOGIN=alicevisionjunk@gmail.com \
    QT_CI_PASSWORD=azerty1.

WORKDIR ${MESHROOM_BUNDLE}
RUN mv "${AV_BUNDLE}" "${MESHROOM_BUNDLE}/aliceVision" && \
    rm -rf ${MESHROOM_BUNDLE}/aliceVision/share/doc \
           ${MESHROOM_BUNDLE}/aliceVision/share/eigen3 \
           ${MESHROOM_BUNDLE}/aliceVision/share/fonts \
           ${MESHROOM_BUNDLE}/aliceVision/share/lemon \
           ${MESHROOM_BUNDLE}/aliceVision/share/libraw \
           ${MESHROOM_BUNDLE}/aliceVision/share/man \
           ${MESHROOM_BUNDLE}/aliceVision/share/pkgconfig

# Install libs needed by Qt
RUN yum install -y \
        flex \
        fontconfig \
        freetype \
        glib2 \
        libICE \
        libX11 \
        libxcb \
        libXext \
        libXi \
        libXrender \
        libSM \
        libXt-devel \
        libGLU-devel \
        mesa-libOSMesa-devel \
        mesa-libGL-devel \
        mesa-libGLU-devel \
        xcb-util-keysyms \
        xcb-util-image \
        libxkbcommon-x11

# Install Python2
RUN yum install -y python27-python-devel python-devel && \
    curl https://bootstrap.pypa.io/2.7/get-pip.py -o /tmp/get-pip.py && \
    python /tmp/get-pip.py && \
    pip install --upgrade pip

COPY ./*requirements.txt ${MESHROOM_DEV}/

# Install Meshroom requirements and freeze bundle
WORKDIR "${MESHROOM_DEV}"
RUN pip install -r dev_requirements.txt -r requirements.txt

# Install Qt (to build plugins)
WORKDIR /tmp/qt
COPY dl/qt.run /tmp/qt
COPY ./docker/qt-installer-noninteractive.qs ${MESHROOM_DEV}/docker/
RUN chmod +x qt.run && \
    ./qt.run --verbose --platform minimal --script "${MESHROOM_DEV}/docker/qt-installer-noninteractive.qs" && \
    rm qt.run

