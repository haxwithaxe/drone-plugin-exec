FROM python:3.11-alpine

RUN mkdir -p /drone-plugin-exec
COPY ./dist/drone_plugin_exec-*.tar.gz /drone-plugin-exec/drone_plugin_exec.tar.gz
RUN pip install /drone-plugin-exec/drone_plugin_exec.tar.gz
RUN rm -f /drone-plugin-exec/drone_plugin_exec.tar.gz

ENTRYPOINT ["/usr/local/bin/drone-plugin-exec-plugin"]
