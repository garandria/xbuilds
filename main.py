import os
import subprocess
import shutil
import argparse

CCACHE_STATS = "/srv/local/grandria/ccache-stats.txt"
TIME_OUTPUT_FILE = "time"
BUILD_STDOUT = "stdout"
BUILD_STDERR = "stderr"
BUILD_EXIT_STATUS = "exit_status"
DUMMY_EMAIL = "tux@tux.com"
DUMMY_NAME = "Tux"

# --------------------------------------------------------------------------

def call_cmd(cmd, cwd='.'):
    return subprocess.run(cmd,
                          capture_output=True,
                          shell=True,
                          cwd=cwd)

# --------------------------------------------------------------------------

def ccache_clean():
    cmd = "ccache -cCz"
    return call_cmd(cmd).returncode

def ccache_set_size(size, unit):
    cmd = f"ccache -M {size}{unit}"
    return call_cmd(cmd).returncode

def ccache_stats(head, output):
    cmds = [f"echo '======= {head} =======' >> {output}",
           f"ccache -s >> {output}"]
    cmd = "; ".join(cmds)
    return call_cmd(cmd).returncode

def ccache_set_dir(path):
    return call_cmd(f"ccache --set-config cache_dir={path}")


# --------------------------------------------------------------------------

def build(jobs=None, config=None, with_time=True, ccache=False):
    cmd = []

    if with_time:
        cmd = ["/usr/bin/time", "-p", "-o", TIME_OUTPUT_FILE, "--format=%e"]

    if jobs is None:
        jobs = int(subprocess.check_output("nproc"))+1

    if config is not None:
        if not os.path.isfile(config):
            raise FileNotFoundError(f"No such configuration {config}")
        if os.path.isfile(".config"):
            shutil.move(".config", ".config.old")
        shutil.copy(config, ".config")

    cmd.append("make")
    if ccache:
        cmd.append('CC="ccache gcc"')
    cmd.append(f"-j{jobs}")

    cmd = " ".join(cmd)
    ret = call_cmd(cmd)
    with open(BUILD_EXIT_STATUS, 'w') as status:
        status.write(str(ret.returncode))
    if ret.stdout:
        with open(BUILD_STDOUT, 'wb') as out:
            out.write(ret.stdout)
    if ret.stderr:
        with open(BUILD_STDERR, 'wb') as err:
            err.write(ret.stderr)
    return ret.returncode

# --------------------------------------------------------------------------

def build_status():
    pass

def build_is_ok():
    with open(BULID_EXIT_STATUS, 'r') as status:
        lines = status.readlines()
    return int(lines[-1]) == 0
    # return not os.path.isfile(BUILD_STDERR)

def get_build_time():
    if not os.path.isfile(TIME_OUTPUT_FILE):
        return 0
    with open(TIME_OUTPUT_FILE, 'r') as time:
        lines = time.readlines()
    return float(lines[-1])

# --------------------------------------------------------------------------

def git_init(directory="."):
    cmd = f"git init {directory}"
    return call_cmd(cmd)

def git_add_all():
    cmd = "git add -f *"
    return call_cmd(cmd)

def git_commit(msg):
    cmd = f"git commit -m \"{msg}\""
    return call_cmd(cmd)

def git_branch_list():
    cmd = "git branch -a"
    ret = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        shell=True,
        check=True)
    raw = ret.stdout.decode().split()
    return [b for b in raw if b not in {'', '*'}]

def git_branch_exists(name):
    return name in git_branch_list()

def git_create_branch(name):
    cmd = f"git checkout -b {name}"
    return call_cmd(cmd)

def git_checkout(name):
    cmd = f"git checkout '{name}'"
    return call_cmd(cmd)

def git_config(prefix, field, val):
    cmd = f"git config {prefix}.{field} \"{val}\""
    return call_cmd(cmd)

# --------------------------------------------------------------------------

def debug(msg, end="\n"):
    print(msg, end=end, flush=True)

# --------------------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(description='Linux Builds')
    parser.add_argument("--src",
                        type=str,
                        required=True,
                        dest="linux_src",
                        help="Path to the Linux Kernel's source directory")
    parser.add_argument("--configs",
                        type=str,
                        dest="configurations",
                        required=True,
                        help="Path to the folder that contains configurations")
    parser.add_argument("--incremental",
                        action="store_true",
                        default=False,
                        help="Incremental build")
    parser.add_argument("--ccache",
                        action="store_true",
                        default=False,
                        help="Enable ccache")
    parser.add_argument("--keep-cache",
                        dest="keep_cache",
                        action="store_true",
                        default=False,
                        help="Enable ccache")
    parser.add_argument("--target",
                        type=str,
                        required=True,
                        help="Name of the generated binary")

    args = parser.parse_args()

    if not os.path.isdir(args.linux_src):
        raise FileNotFoundError(f"No such directory: {args.linux_src}")

    if not os.path.isdir(args.configurations):
        raise FileNotFoundError(f"No such directory: {args.configurations}")

    linux = args.linux_src
    conf_set = args.configurations
    if args.linux_src.endswith('/'):
        linux = args.linux_src[:-1]
    if args.configurations.endswith('/'):
        conf_set = args.configurations[:-1]

    ccache_cachedir = "/srv/local/grandria/cache"

    if args.ccache:
        debug("* Ccache")
        debug("  - Setting cache directory")
        ccache_set_dir(ccache_cachedir)
        debug("  - Setting cache size")
        ccache_set_size(1, 'T')
        debug("  - Cleaning cache")
        if not args.keep_cache:
            ccache_clean()

    if args.ccache:
        ccache_stats("Initialization", CCACHE_STATS)

    debug(f"* Moving to {linux}")
    os.chdir(linux)


    debug("* Setting git")
    if os.path.isdir(".git"):
        debug("  - Already a git repo")
    else:
        debug("  - Initialization")
        git_init()
        debug("  - Configuration")
        git_config("user", "email", DUMMY_EMAIL)
        git_config("user", "name", DUMMY_NAME)
        debug("  - Adding everything")
        git_add_all()
        debug("  - Committing source")
        git_commit("source")

    debug("* Builds")
    confs = os.listdir(conf_set)
    confs.sort()
    for c in confs:
        if not args.incremental:
            git_checkout("master")
        debug(f"  - {c},", end="")
        git_create_branch(c)
        if args.incremental:
            for to_delete in {BUILD_STDOUT, BUILD_STDERR, BUILD_EXIT_STATUS}:
                if os.path.isfile(to_delete):
                    os.remove(to_delete)
        c_path = '/'.join([conf_set, c])
        status = build(jobs=None, config=c_path, with_time=True, ccache=args.ccache)
        time = get_build_time()
        binary_size = 0
        if os.path.isfile(args.target):
            binary_size = os.path.getsize(args.target)
        debug(f"{time}s, ok={status==0}, size={binary_size}")
        git_add_all()
        git_commit("Clean build")
        if args.ccache:
            ccache_stats(c, CCACHE_STATS)


if __name__ == "__main__":
    main()
