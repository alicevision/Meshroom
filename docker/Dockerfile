# syntax=docker/dockerfile:1.4
# vim: ft=dockerfile

ARG DEPS_IMAGE

# Only what the build needs, so that unrelated changes in the build context do not
# invalidate the cache. Bind-mounted below, never part of an image layer.
FROM scratch AS sources
COPY *.txt *.md *.py /
COPY docs /docs
COPY meshroom /meshroom
COPY tests /tests
COPY bin /bin

FROM ${DEPS_IMAGE}
LABEL maintainer="AliceVision Team alicevision-team@googlegroups.com"

# Execute with nvidia docker (https://github.com/nvidia/nvidia-docker/wiki/Installation-(version-2.0))
# docker run -it --runtime nvidia -p 2222:22 --name meshroom -v</path/to/your/data>:/data alicevision/meshroom:develop-av2.2.8.develop-ubuntu20.04-cuda11.0
# ssh -p 2222 -X root@<docker host> /opt/Meshroom_bundle/Meshroom # Password is 'meshroom'

ENV MESHROOM_DEV=/opt/Meshroom \
    MESHROOM_BUILD=/tmp/Meshroom_build \
    MESHROOM_BUNDLE=/opt/Meshroom_bundle \
    AV_INSTALL=/opt/AliceVision_install
ENV PATH="${PATH}:${MESHROOM_BUNDLE}"

WORKDIR ${MESHROOM_DEV}

# Generate the exe for Meshroom and clean-up the bundle folder.
# The sources are bind-mounted (rw: build-time writes are discarded); target = ${MESHROOM_DEV}.
RUN --mount=type=bind,from=sources,target=/opt/Meshroom,rw \
    python3.11 setup.py install_exe -d "${MESHROOM_BUNDLE}" && \
        find ${MESHROOM_BUNDLE} -name "*Qt6Web*" -delete && \
        find ${MESHROOM_BUNDLE} -name "*Qt6Designer*" -delete && \
        rm -rf ${MESHROOM_BUNDLE}/lib/PySide6/typesystems/ \
                ${MESHROOM_BUNDLE}/lib/PySide6/examples/ \
                ${MESHROOM_BUNDLE}/lib/PySide6/include/ \
                ${MESHROOM_BUNDLE}/lib/PySide6/Qt/translations/ \
                ${MESHROOM_BUNDLE}/lib/PySide6/Qt/resources/ \
                ${MESHROOM_BUNDLE}/lib/PySide6/QtWeb* \
                ${MESHROOM_BUNDLE}/lib/PySide6/rcc \
                ${MESHROOM_BUNDLE}/lib/PySide6/designer

WORKDIR ${MESHROOM_BUILD}

# Move the bundled installation of AliceVision into Meshroom's bundle
RUN mkdir ${MESHROOM_BUNDLE}/aliceVision && \
    mv /opt/AliceVision_bundle/* ${MESHROOM_BUNDLE}/aliceVision

# AliceVision models and data, downloaded by docker/download-models.sh
COPY dl/aliceVision/ ${MESHROOM_BUNDLE}/aliceVision/share/aliceVision/
# Meshroom sets the ALICEVISION_* variables from its bundle (setupEnvironment() in
# meshroom/__init__.py) but never overrides existing ones: drop those exported by
# the AliceVision image, which point outside of the bundle
RUN rm -f /etc/profile.d/alicevision.sh

# Build Meshroom plugins. Configure, build and clean up in a single RUN so that the
# build tree never ends up in an image layer.
RUN --mount=type=bind,from=sources,target=/opt/Meshroom,rw \
    cmake "${MESHROOM_DEV}" -DALICEVISION_ROOT="${AV_INSTALL}" -DCMAKE_INSTALL_PREFIX="${MESHROOM_BUNDLE}/qtPlugins" && \
    make "-j$(nproc)" QtAliceVision && \
    make "-j$(nproc)" && \
	rm -rf "${MESHROOM_BUILD}" \
		${MESHROOM_BUNDLE}/aliceVision/share/doc \
		${MESHROOM_BUNDLE}/aliceVision/share/eigen3 \
		${MESHROOM_BUNDLE}/aliceVision/share/fonts \
		${MESHROOM_BUNDLE}/aliceVision/share/lemon \
		${MESHROOM_BUNDLE}/aliceVision/share/libraw \
		${MESHROOM_BUNDLE}/aliceVision/share/man/ \
		${MESHROOM_BUNDLE}/aliceVision/share/pkgconfig

# PySide6: copy missing libQt63DQuickScene3D.so along with its dependencies to avoid runtime issues
RUN cp ${QT_DIR}/lib/libQt63DQuickScene3D.so.${QT_VERSION} ${MESHROOM_BUNDLE}/lib/PySide6/Qt/lib/libQt63DQuickScene3D.so.6

# Copy the system libraries listed by the deps image (BUNDLE_EXTRA_LIBS) into the bundle
RUN for lib in ${BUNDLE_EXTRA_LIBS:-}; do cp -L "$lib" "${MESHROOM_BUNDLE}/lib/"; done

WORKDIR /root

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]

