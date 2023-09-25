FROM python:3.11-alpine

RUN mkdir -p /drone-exec-plugin
COPY ./dist/drone_exec_plugin-*.tar.gz /drone_exec_plugin/drone_exec_plugin.tar.gz
RUN pip install /drone_exec_plugin/drone_exec_plugin.tar.gz
RUN rm -f /drone_exec_plugin/drone_exec_plugin.tar.gz

ENTRYPOINT ["/usr/local/bin/drone-exec-plugin-plugin"]
