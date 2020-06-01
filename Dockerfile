ARG MR_VERSION
ARG CUDA_VERSION=9.0
ARG OS_VERSION=7
FROM alicevision/meshroom-deps:${MR_VERSION}-centos${OS_VERSION}-cuda${CUDA_VERSION}
LABEL maintainer="AliceVision Team alicevision-team@googlegroups.com"

# Execute with nvidia docker (https://github.com/nvidia/nvidia-docker/wiki/Installation-(version-2.0))
# docker run -it --runtime=nvidia meshroom

ENV MESHROOM_DEV=/opt/Meshroom \
    MESHROOM_BUILD=/tmp/Meshroom_build \
    MESHROOM_BUNDLE=/opt/Meshroom_bundle \
    QT_DIR=/opt/Qt5.14.1/5.14.1/gcc_64 \
    PATH="${PATH}:${MESHROOM_BUNDLE}"

COPY . "${MESHROOM_DEV}"

WORKDIR ${MESHROOM_DEV}

RUN source scl_source enable rh-python36 && python setup.py install_exe -d "${MESHROOM_BUNDLE}" && \
    find ${MESHROOM_BUNDLE} -name "*Qt5Web*" -delete && \
    find ${MESHROOM_BUNDLE} -name "*Qt5Designer*" -delete && \
    rm -rf ${MESHROOM_BUNDLE}/lib/PySide2/typesystems/ ${MESHROOM_BUNDLE}/lib/PySide2/examples/ ${MESHROOM_BUNDLE}/lib/PySide2/include/ ${MESHROOM_BUNDLE}/lib/PySide2/Qt/translations/ ${MESHROOM_BUNDLE}/lib/PySide2/Qt/resources/ && \
    rm ${MESHROOM_BUNDLE}/lib/PySide2/QtWeb* && \
    rm ${MESHROOM_BUNDLE}/lib/PySide2/pyside2-lupdate ${MESHROOM_BUNDLE}/lib/PySide2/rcc ${MESHROOM_BUNDLE}/lib/PySide2/designer

WORKDIR ${MESHROOM_BUILD}

# Build Meshroom plugins
RUN cmake "${MESHROOM_DEV}" -DALICEVISION_ROOT="${AV_INSTALL}" -DQT_DIR="${QT_DIR}" -DCMAKE_INSTALL_PREFIX="${MESHROOM_BUNDLE}/qtPlugins"
# RUN make -j8 qtOIIO
# RUN make -j8 qmlAlembic
# RUN make -j8 qtAliceVision
RUN make -j8 && cd /tmp && rm -rf ${MESHROOM_BUILD}

RUN mv "${AV_BUNDLE}" "${MESHROOM_BUNDLE}/aliceVision"
RUN rm -rf ${MESHROOM_BUNDLE}/aliceVision/share/doc ${MESHROOM_BUNDLE}/aliceVision/share/eigen3 ${MESHROOM_BUNDLE}/aliceVision/share/fonts ${MESHROOM_BUNDLE}/aliceVision/share/lemon ${MESHROOM_BUNDLE}/aliceVision/share/libraw ${MESHROOM_BUNDLE}/aliceVision/share/man/ aliceVision/share/pkgconfig


