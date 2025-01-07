FROM prom/alertmanager:main

COPY config.yml /etc/alertmanager/config.yml

CMD [ "--config.file=/etc/alertmanager/config.yml", \
        "--storage.path=/alertmanager" ]