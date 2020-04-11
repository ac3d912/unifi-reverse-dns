# Description

Just a little tool to help Unifi users manage the aliases assigned to clients. Performs a reverse lookup of all clients attached to the AP and assigns an alias based upon the hostname returned.

# Installation

## Environment vars

Set applicable environment vars in defaults.env for your situation. All params to the python script may be passed by environment variable, of the same "longname" (e.g. USERNAME).  All parameters may also be read from individual files using "LONGNAME__FILE" (e.g. PASSWORD__FILE=~/password.secret).

## Python

You just need to clone the python API library I used. Maintainer did not include a setup.py, so we just move it around like a local package.

    git clone git@github.com:frehov/Unifi-Python-API.git unifi-python-api
    
    mv unifi-python-api/ubiquiti .
    rm -rf unifi-python-api

    python main.py --help

## Docker

I've included a few options for docker, docker compose, and docker in swarm mode.

    docker build . -t unifi-reverse-dns
    docker run unifi-reverse-dns python main.py --help
    docker run unifi-reverse-dns

## Docker Compose

Edit docker-compose.yaml, or the defaults.env as needed.

    docker-compose up

    # if you daemonize
    docker-compose up -d

## Full Unifi Controller Docker Stack (of ultimate power)

This includes linuxserver's unifi-controller image. See their documentation on getting this setup [https://hub.docker.com/r/linuxserver/unifi-controller]. It also has options for configuring traefik.

You will want to edit the swarm file to point it to your own registry. You can remove the references to traefik as well (including the network), if you are not using that.

    # Create the password secret
    echo mypassword | docker secret create unifi-password -

    docker-compose -f docker-compose-swarm.yaml build
    docker stack deploy unifi-reverse-dns --compose-file docker-compose-swarm.yaml
    # Or, because you use portainer to manage your swarm, just copy/paste the compose file into a new stack!

I personally use and prefer this method because I already run a swarm on the internal network, complete with traefik as a gateway, but of course, YMMV.

## Troubleshooting

    docker service logs unifi-reverse-dns_unifi-reverse-dns
