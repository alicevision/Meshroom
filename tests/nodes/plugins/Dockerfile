FROM python:3
RUN python -m pip install --no-cache-dir numpy
RUN python -m pip install --no-cache-dir psutil
#overwrides entry point otherwise will directly execute python
ENTRYPOINT [ "/bin/bash", "-l", "-c" ]