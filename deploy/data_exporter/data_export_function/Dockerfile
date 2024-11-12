FROM public.ecr.aws/docker/library/ubuntu:24.04

RUN apt update && \
    apt install -y postgresql-client-16 python3.12 python3-pip curl unzip && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --break-system-packages -r requirements.txt
RUN pip3 install --break-system-packages awslambdaric

COPY . .

ENTRYPOINT ["python3", "-m", "awslambdaric" ]
CMD [ "app.lambda_handler" ]
