FROM nvidia/cuda:12.2.0-base-ubuntu22.04
WORKDIR /home/app
RUN apt update
RUN apt install -y python3
RUN apt install -y python3-pip	
RUN pip install deepface
COPY main.py main.py
RUN mkdir cnic
RUN mkdir selfie
CMD ["python3","main.py"]