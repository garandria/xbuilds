FROM debian:bullseye

RUN apt-get update -y && apt-get install -y \
    gcc g++ make binutils flex bison dwarves util-linux kmod \
    e2fsprogs jfsutils u-boot-tools reiserfsprogs xfsprogs squashfs-tools \
    btrfs-progs pcmciautils quota rsync xz-utils ppp libnfs-utils procps udev \
    grub-common iptables tar openssl libelf-dev lzop libssl-dev \
    bsdmainutils ccache bc sphinx-common sphinx-doc cpio lz4 liblz4-tool \
    pkg-config zstd git curl time python3 libc6-dev-i386 libc6-i386 \
    bzip2 perl libntirpc-dev libsepol1-dev wget

WORKDIR /srv/local/grandria
