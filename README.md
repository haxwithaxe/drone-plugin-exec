# drone-plugin-exec

Drone plugin to execute commands in a configured environment on the host the container is running on.
The target side clones the repo and checks out the commit given by Drone, runs the command, then cleans up after itself.

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
* `target_address` (required) - The IP address or unix socket uri of the target side.
* `target_port` (required) - The port configured for the target side. Not required when using a unix socket.
* `target_pubkey` (required) - The target side public key string.
* `checkout` - If `true` then the repo is checked out. Defaults to `true`.
* `log_level` - The plugin side log level. Defaults to `INFO`.
* `shell` - The program to use to run the script. Defaults to ``/bin/bash``.
* `submodules` - If `true` all git submodules are updated. Defaults to `false`.
* `teardown` - When to teardown the runtime environment. Defaults to ``on-success``.
    * ``always`` - Always teardown after execution.
    * ``on-success`` - Only teardown after successful execution.
    * ``never`` - Never teardown. Always leave the temporary environment in place.
* `umask` - Set the umask for the script execution. Defaults to unset.
* `user` - Set the user to execute the script as. Defaults to unset (whoever the target is running as).


## Target Configuration

The target config is a toml file.

* `address` (required) - The address to listen on. This can be an IP or unix socket uri. Not required if using `docker_network`.
* `port` (required) - The port to listen on. Not required if using a unix socket.
* `target_privkey_path` (required) - The path to the target side private key file.
* `plugin_pubkey` (required) - The plugin side public key.
* `docker_network` - The docker network to attach to.
* `docker_uri` - The docker API uri if not the default. Defaults to whatever is set in the environment variables or the local socket.
* `tmp_path_root` - The directory to create temporary directories in. Defaults to ``/tmp/drone-plugin-exec-target``.


## Setup

## On The Target

### Install the target

```sh
sudo PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/usr/local/bin pipx install drone-plugin-exec
```

### Generate the key pairs

```sh
sudo mkdir -p /usr/local/etc/drone-plugin-exec/
sudo drone-plugin-exec-genkeypair --output /usr/local/etc/drone-plugin-exec/target_key
```

#### Generate the plugin key pair

This only has to happen once and doesn't necessarily need to happen on the target but it's convenient to do on the first target.

```sh
drone-plugin-exec-genkeypair --output plugin_key
```

##### Upload the keys as secrets

```sh
drone secret add --repository <your username>/<your repo> --name plugin_exec_privkey --data @plugin_key
```

Or

```sh
drone orgsecret add <your orginization> plugin_exec_privkey @plugin_key
```

Optionally shred the plugin private key once it's been added as a secret.

```sh
shred -ux plugin_key
```

### Configure the target

``/usr/local/etc/drone-plugin-exec/target.toml``

```toml
plugin_pubkey = 'base64:<your base64 encoded plugin public key>'
target_privkey_path = '/usr/local/etc/drone-plugin-exec/target_key'
tmp_path_root = '/tmp/drone-exec-plugin-test-temp'
address = 'unix:///var/run/drone-plugin-exec.sock'
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
ExecStart=/usr/local/bin/drone-plugin-exec-target --config /usr/local/etc/drone-plugin-exec/target.toml

[Install]
WantedBy=multi-user.target
```

```sh
sudo systemctl enable drone-plugin-exec-target.service
sudo systemctl start drone-plugin-exec-target.service
```


## Hello World

Below are example configs for a target and a plugin.

### Target

``/usr/local/etc/drone-plugin-exec/target.toml``

```toml
plugin_pubkey = 'base64:<your base64 encoded plugin public key>'
target_privkey_path = '/usr/local/etc/drone-plugin-exec/target_key'
tmp_path_root = '/tmp/drone-exec-plugin-test-temp'
address = 'unix:///var/run/drone-plugin-exec.sock'
```

### Plugin

This uses the ``node`` option to limit execution to nodes with a target daemon labeled with ``drone-plugin-exec-target=true``.

``.drone.yml``

```yaml
---
kind: pipeline
name: Example exec
type: docker

node:
  drone-plugin-exec-target: true

steps:
  - name: hello world
    image: haxwithaxe/drone-plugin-exec:latest
    volumes:
      - /var/run/drone-plugin-exec.sock:/var/run/drone-plugin-exec.sock
    settings:
      checkout: true
      log_level: INFO
      privkey:
        from_secret: plugin_exec_privkey
      repo_type: http
      script: whoami
      address: /var/run/drone-plugin-exec.sock
      target_pubkey: base64:<base64 encoded target public key>
      teardown: on-success
```
