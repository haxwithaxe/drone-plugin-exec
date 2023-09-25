# drone-exec

Drone plugin to execute commands on the host the container is running on.

## Build

### Python

```sh
	python3 -m venv buildvenv
	source buildvenv/bin/activate
	pip install build twine
	python3 -m build
```

### Docker

Build the docker image with the following commands:

```sh
docker build . -t local/drone-plugin-exec
```

## Plugin Configuration
* `privkey` (required) - The plugin side private key.
* `script` (required) - A string with commands to run. This can be multiple lines.
* `target_address` (required) - "<docker0 ip address>" \
* `target_port` (required) - "<port configured for the target>" \
* `target_pubkey` (required) - "<target public key>" \
* `checkout` - If `true` then the repo is checked out. Defaults to `true`.
* `log_level` - The plugin side log level. Defaults to `INFO`.
* `shell` - The program to use to run the script. Defaults to ``/bin/bash``.
* `submodules` - If `true` all git submodules are updated. Defaults to `false`.
* `teardown` - When to teardown the runtime environment. Defaults to ``on-success``.
	* ``always`` - Always teardown after execution.
	* ``on-success`` - Only teardown after successful execution.
	* ``never`` - Never teardown. Always leave the temporary environment in place.
* `umask` - Defaults to unset.
* `user` - Defaults to unset.

## Target Configuration
The target config is a toml file.
* `address` (required) - The address to listen on.
* `port` (required) - The port to listen on.
* `target_privkey_path` (required) - The path to the target side private key file.
* `plugin_pubkey` (required) - The plugin side public key.
* `docker_network` - The docker network to attach to.
* `docker_uri` - The docker API uri if not the default. Defaults to whatever is set in the environment variables or the local socket.
* `tmp_path_root` - The directory to create temporary directories in. Defaults to ``/tmp/drone-plugin-exec-target``

## Setup

## On The Target

### Install the target
```sh
sudo PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/usr/local/bin pipx install drone-plugin-exec
```

### Generate the key pairs
```sh
drone-plugin-exec-genkeypair --output target_key
drone-plugin-exec-genkeypair --output plugin_key
```

### Upload the keys as secrets
```sh
drone secret add --repository <your username>/<your repo> --name plugin_exec_privkey --data @plugin_key
```

Or

```sh
drone orgsecret add <your orginization> plugin_exec_privkey @plugin_key
```

### Run the target daemon

#### Directly
```sh
drone-plugin-exec-target --config <path to the config>
```

#### Systemd
``/usr/local/lib/systemd/system/drone-plugin-exec-target.service``
```systemd
[Unit]
Description=Drone Plugin Exec Daemon
After=network.target,docker.service

[Service]
Type=exec
ExecStart=/usr/local/bin/drone-plugin-exec-target --config /usr/local/etc/drone-plugin-exec-target.toml

[Install]
WantedBy=multi-user.target
```

```sh
sudo systemctl enable drone-plugin-exec-target.service
sudo systemctl start drone-plugin-exec-target.service
```

## Plugin Hello World
``.drone.yml``
```yaml
---
kind: pipeline
name: hello
type: docker

steps:
  - name: world
    image: haxwithaxe/drone-plugin-exec:latest
    settings:
      checkout: true
      log_level: INFO
      privkey:
		from_secret: plugin_exec_privkey
      repo_type: http
      script: whoami
	  docker_network: bridge
      target_pubkey: <base64 encoded public key>
      teardown: on-success
```


