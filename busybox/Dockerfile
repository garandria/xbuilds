FROM debian:bullseye

# - Minimal requirements to build a Linux kernel
#     https://docs.kernel.org/process/changes.html#current-minimal-requirements
# - TuxML dependencies
#     https://github.com/TuxML/tuxml

RUN apt-get update -y && apt-get install -y \
    gcc-10 gcc-10-plugin-dev g++ make binutils flex bison dwarves util-linux kmod \
    e2fsprogs jfsutils u-boot-tools reiserfsprogs xfsprogs squashfs-tools \
    btrfs-progs pcmciautils quota rsync xz-utils ppp libnfs-utils procps udev \
    grub-common iptables tar openssl libelf-dev lzop libssl-dev \
    bsdmainutils ccache bc sphinx-common sphinx-doc cpio lz4 liblz4-tool \
    pkg-config zstd git curl time python3 libc6-dev-i386 libc6-i386 \
    libsepol1-dev libselinux1-dev electric-fence libpam0g-dev libdmalloc-dev
# grub

RUN cd / && curl -O https://raw.githubusercontent.com/garandria/LBwCcache/master/gcc-10-plugin-dev-workaround-980609.patch && patch -p1 < gcc-10-plugin-dev-workaround-980609.patch

WORKDIR /srv/local/grandria
