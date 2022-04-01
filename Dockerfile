FROM ubuntu:bionic

# Install dependencies and Python (>= C++14)
RUN apt-get update && apt-get install lzip git make sudo -y
RUN sudo apt-get install software-properties-common -y
RUN sudo add-apt-repository -y ppa:ubuntu-toolchain-r/test
RUN sudo apt-get update
RUN sudo apt-get install gcc-6 g++-6 python3.8 python3.8-dev python3.8-distutils build-essential libssl-dev libffi-dev curl -y
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3.8 get-pip.py
RUN echo 'export PATH=$PATH:$HOME/.local/bin' >> ~/.bashrc
RUN . ~/.bashrc

# Install Pyfhel
RUN pip3 install Pyfhel

CMD /bin/sh

