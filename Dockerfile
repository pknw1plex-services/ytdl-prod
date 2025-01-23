FROM caddy:latest
ADD config /var/www
ENTRYPOINT ["caddy", "run", "--config=/var/www/Caddyfile", "--watch" ]
