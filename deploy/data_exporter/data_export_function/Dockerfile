FROM public.ecr.aws/docker/library/ubuntu:24.04

RUN apt update && \
    apt install -y postgresql-client-16 python3.12 python3-pip curl unzip python3.12-venv && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python3 -m venv .venv
RUN ./.venv/bin/pip install -r requirements.txt
RUN ./.venv/bin/pip install awslambdaric

COPY . .

ENTRYPOINT [".venv/bin/python", "-m", "awslambdaric" ]
CMD [ "app.lambda_handler" ]
