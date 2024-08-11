#!/bin/bash

docker run --rm -v certs:/etc/letsencrypt certbot/certbot renew
