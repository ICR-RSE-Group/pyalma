FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y openssh-server && \
    mkdir /var/run/sshd && \
    echo 'root:password' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd

# RUN echo "Match Group *,!root,!SCIENCOM" >> /etc/ssh/sshd_config && \
#     echo "    X11Forwarding no" >> /etc/ssh/sshd_config && \
#     echo "    AllowTcpForwarding no" >> /etc/ssh/sshd_config && \
#     echo "    ForceCommand internal-sftp" >> /etc/ssh/sshd_config

#remove condition on group
RUN echo "Match User restricted" >> /etc/ssh/sshd_config && \
    echo "    ForceCommand internal-sftp" >> /etc/ssh/sshd_config


RUN useradd -m testuser1 && echo "testuser1:password1" | chpasswd && \
    useradd -m restricted && echo "restricted:password2" | chpasswd

RUN chown root:root /home/restricted && \
    chmod 755 /home/restricted


EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
