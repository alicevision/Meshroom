ARG CUDA_TAG=7.0
ARG OS_TAG=7
FROM alicevision:centos${OS_TAG}-cuda${CUDA_TAG}
LABEL maintainer="AliceVision Team alicevision-team@googlegroups.com"

# Execute with nvidia docker (https://github.com/nvidia/nvidia-docker/wiki/Installation-(version-2.0))
# docker run -it --runtime=nvidia meshroom

# Install all compilation tools
# - file and openssl are needed for cmake
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
        xcb-util-image

ENV MESHROOM_DEV=/opt/Meshroom \
    MESHROOM_BUILD=/tmp/Meshroom_build \
    MESHROOM_BUNDLE=/opt/Meshroom_bundle \
    QT_DIR=/opt/qt/5.11.0/gcc_64 \
    PATH="${PATH}:${MESHROOM_BUNDLE}"

COPY . "${MESHROOM_DEV}"

WORKDIR /tmp/qt
RUN curl -LO http://download.qt.io/official_releases/online_installers/qt-unified-linux-x64-online.run
RUN chmod u+x qt-unified-linux-x64-online.run
RUN ./qt-unified-linux-x64-online.run --verbose --platform minimal --script "${MESHROOM_DEV}/docker/qt-installer-noninteractive.qs"

WORKDIR ${MESHROOM_BUILD}
RUN rm -rf "${AV_BUNDLE}/lib" && ln -s "${AV_BUNDLE}/lib64" "${AV_BUNDLE}/lib"
RUN cmake "${MESHROOM_DEV}" -DALICEVISION_ROOT="${AV_INSTALL}" -DQT_DIR="${QT_DIR}" -DCMAKE_INSTALL_PREFIX="${MESHROOM_BUNDLE}"
RUN make -j8

