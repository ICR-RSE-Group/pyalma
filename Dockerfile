FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y openssh-server && \
    mkdir /var/run/sshd && \
    echo 'root:password' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd && \
    echo "export VISIBLE=now" >> /etc/profile

# Creating two users
RUN useradd -m testuser1 && echo "testuser1:password1" | chpasswd && \
    useradd -m restricted && echo "restricted:password2" | chpasswd && \
    usermod -s /usr/sbin/nologin restricted

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
