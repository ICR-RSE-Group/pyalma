FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y openssh-server && \
    mkdir /var/run/sshd && \
    echo 'root:password' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd && \
    echo "export VISIBLE=now" >> /etc/profile

 RUN apt-get update && apt-get install -y bash && \
    ln -s /bin/bash /bin/rbash && \
    useradd -m testuser1 && echo "testuser1:password1" | chpasswd && \
    useradd -m -s /bin/rbash restricted && echo "restricted:password2" | chpasswd && \
    mkdir -p /home/restricted/readonly-bin && \
    chown restricted:restricted /home/restricted/readonly-bin && \
    echo 'export PATH=/home/restricted/readonly-bin' >> /home/restricted/.bash_profile && \
    echo 'echo "Restricted shell: scripting is not allowed."' >> /home/restricted/.bash_profile

# # Creating two users
# RUN useradd -m testuser1 && echo "testuser1:password1" | chpasswd && \
#     useradd -m -s /bin/bash restricted && echo "restricted:password2" | chpasswd 

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
