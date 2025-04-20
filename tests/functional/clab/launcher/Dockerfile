FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -yq && \
    apt-get install -yq \
        --no-install-recommends \
        ca-certificates \
        build-essential \
        curl

RUN curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc && \
    chmod a+r /etc/apt/keyrings/docker.asc

RUN echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null

RUN echo "deb [trusted=yes] https://netdevops.fury.site/apt/ /" | \
    tee -a /etc/apt/sources.list.d/netdevops.list

RUN apt-get update -yq && \
    apt-get install -yq \
        --no-install-recommends \
        docker-ce \
        docker-ce-cli \
        containerlab=0.66.0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /launcher

COPY main.py .

CMD ["/launcher/main.py"]
