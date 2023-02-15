#!/bin/bash

# --------------------------------------------------------------------------
# The code in `randconfig()` is a part of Busybox's scripts/randomtest script.
# https://git.busybox.net/busybox/tree/scripts/randomtest?h=1_36_stable
# We isolated the part for GLIBC for our use-case

randconfig ()
{
    # Generate random config
    make randconfig >/dev/null || { echo "randconfig error"; exit 1; }

    # Tweak resulting config
    cat .config \
        | grep -v CONFIG_DEBUG_PESSIMIZE \
        | grep -v CONFIG_WERROR \
        | grep -v CONFIG_CROSS_COMPILER_PREFIX \
        | grep -v CONFIG_SELINUX \
        | grep -v CONFIG_EFENCE \
        | grep -v CONFIG_DMALLOC \
               \
        | grep -v CONFIG_RFKILL \
               >.config.new
    mv .config.new .config
    echo '# CONFIG_DEBUG_PESSIMIZE is not set' >>.config
    echo '# CONFIG_WERROR is not set' >>.config
    echo "CONFIG_CROSS_COMPILER_PREFIX=\"${CROSS_COMPILER_PREFIX}\"" >>.config
    echo '# CONFIG_SELINUX is not set' >>.config
    echo '# CONFIG_EFENCE is not set' >>.config
    echo '# CONFIG_DMALLOC is not set' >>.config
    echo '# CONFIG_RFKILL is not set' >>.config

    # If glibc, don't build static
	cat .config \
	    | grep -v CONFIG_STATIC \
	    | grep -v CONFIG_FEATURE_LIBBUSYBOX_STATIC \
	           \
	    | grep -v CONFIG_FEATURE_2_4_MODULES \
	    | grep -v CONFIG_FEATURE_USE_BSS_TAIL \
	    | grep -v CONFIG_DEBUG_SANITIZE \
	    | grep -v CONFIG_FEATURE_MOUNT_NFS \
	    | grep -v CONFIG_FEATURE_INETD_RPC \
	           >.config.new
	mv .config.new .config
	echo '# CONFIG_STATIC is not set' >>.config
	echo '# CONFIG_FEATURE_LIBBUSYBOX_STATIC is not set' >>.config
	# newer glibc (at least 2.23) no longer supply query_module() ABI.
	# People who target 2.4 kernels would likely use older glibc (and older bbox).
	echo '# CONFIG_FEATURE_2_4_MODULES is not set' >>.config
	echo '# CONFIG_FEATURE_USE_BSS_TAIL is not set' >>.config
	echo '# CONFIG_DEBUG_SANITIZE is not set' >>.config
	# 2018: current glibc versions no longer include rpc/rpc.h
	echo '# CONFIG_FEATURE_MOUNT_NFS is not set' >>.config
	echo '# CONFIG_FEATURE_INETD_RPC is not set' >>.config

    # If STATIC, remove some things.
    # PAM with static linking is probably pointless
    # (but I need to try - now I don't have libpam.a on my system, only libpam.so)
    if grep -q "^CONFIG_STATIC=y" .config; then
	    cat .config \
	        | grep -v CONFIG_PAM \
	               >.config.new
	    mv .config.new .config
	    echo '# CONFIG_PAM is not set' >>.config
    fi

    # Regenerate .config with default answers for yanked-off options
    # (most of default answers are "no").
    { yes "" | make oldconfig >/dev/null; } || { echo "oldconfig error"; exit 1; }
}

# --------------------------------------------------------------------------
# --------------------------------------------------------------------------

DB_FILE=.db
CONFIG=.config
OUT_DIR=randconfig_generated
NB_CONFIGS=$1

touch $DB_FILE
mkdir -p $OUT_DIR

i=1
while [[ $i -le $NB_CONFIGS ]] ;
do
    randconfig
    CKSUM=$(sed '4d' $CONFIG | cksum)
    if [[ ! $(grep "$CKSUM" $DB_FILE) ]] ; then
        echo "$CKSUM" >> $DB_FILE
        ii=$(printf "%04d" $i)
        mv $CONFIG $OUT_DIR/${ii}_randconfig
        i=$[$i+1]
    fi
done


rm $DB_FILE
