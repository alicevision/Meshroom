ARG CUDA_TAG=7.0
ARG OS_TAG=7
FROM alicevision:centos${OS_TAG}-cuda${CUDA_TAG}
LABEL maintainer="AliceVision Team alicevision-team@googlegroups.com"

# Execute with nvidia docker (https://github.com/nvidia/nvidia-docker/wiki/Installation-(version-2.0))
# docker run -it --runtime=nvidia meshroom

ENV MESHROOM_DEV=/opt/Meshroom \
    MESHROOM_BUILD=/tmp/Meshroom_build \
    MESHROOM_BUNDLE=/opt/Meshroom_bundle \
    QT_DIR=/opt/qt/5.11.1/gcc_64 \
    PATH="${PATH}:${MESHROOM_BUNDLE}"

COPY . "${MESHROOM_DEV}"

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
        xcb-util-image

# Install Python3
RUN yum install -y centos-release-scl
RUN yum install -y rh-python36

# Install Meshroom requirements and freeze bundle
RUN source scl_source enable rh-python36 && cd "${MESHROOM_DEV}" && pip install -r dev_requirements.txt -r requirements.txt && python setup.py install_exe -d "${MESHROOM_BUNDLE}"

# Install Qt (to build plugins)
WORKDIR /tmp/qt
RUN curl -LO http://download.qt.io/official_releases/online_installers/qt-unified-linux-x64-online.run
RUN chmod u+x qt-unified-linux-x64-online.run
RUN ./qt-unified-linux-x64-online.run --verbose --platform minimal --script "${MESHROOM_DEV}/docker/qt-installer-noninteractive.qs"

WORKDIR ${MESHROOM_BUILD}
# Temporary workaround for qmlAlembic build
RUN rm -rf "${AV_INSTALL}/lib" && ln -s "${AV_INSTALL}/lib64" "${AV_INSTALL}/lib"

# Build Meshroom plugins
RUN cmake "${MESHROOM_DEV}" -DALICEVISION_ROOT="${AV_INSTALL}" -DQT_DIR="${QT_DIR}" -DCMAKE_INSTALL_PREFIX="${MESHROOM_BUNDLE}/qtPlugins"
RUN make -j8

RUN mv "${AV_BUNDLE}" "${MESHROOM_BUNDLE}/aliceVision"

