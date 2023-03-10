import os
import subprocess
import shutil
import argparse

TIME_OUTPUT_FILE = "time"
BUILD_STDOUT = "stdout"
BUILD_STDERR = "stderr"
BUILD_EXIT_STATUS = "exit_status"
DUMMY_EMAIL = "tux@tux.com"
DUMMY_NAME = "Tux"
TRACEFILES = "tracefiles"

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

def ccache_enable_debug():
    cmd = "ccache --set-config debug=true"
    return call_cmd(cmd).returncode

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

def build_is_ok(target):
    cmd = f"egrep '((: fatal)|(gcc:)|(collect2:)) error:' {BUILD_STDERR}"
    return os.path.isfile(target) and not call_cmd(cmd).returncode == 0

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
    cmd = "git add -fA"
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

def git_clone(src, dst):
    cmd = f"git clone --no-hardlinks {src}"
    return call_cmd(cmd, cwd=dst)

def git_pull(from_repo):
    cmd = "git pull"
    return call_cmd(cmd, cwd=from_repo)

# --------------------------------------------------------------------------

def debug(msg, end="\n"):
    print(msg, end=end, flush=True)

# --------------------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(description="eXtrem Builds [xbuilds]")
    parser.add_argument("--src",
                        type=str,
                        required=True,
                        help="Path to the project's source directory")
    parser.add_argument("--configs",
                        type=str,
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
    parser.add_argument("--ccache_dir",
                        type=str,
                        default="../cache",
                        help="Name of ccache's cache directory")
    parser.add_argument("--ccache-stats",
                        dest="ccache_stats_dir",
                        type=str,
                        default="../ccache-stats.txt",
                        help="Path to file to write ccache's stats")
    parser.add_argument("--target",
                        type=str,
                        required=True,
                        help="Name of the generated binary")
    parser.add_argument("--backup",
                        type=str,
                        help="Path to backup directory.")
    parser.add_argument("--results",
                        type=str,
                        default="../results.csv",
                        help="CSV file that contains the results")
    parser.add_argument("--debug",
                        action="store_true",
                        dest="ccache_debug",
                        default=False,
                        help="Enables debug for ccache")
    parser.add_argument("--no-git-backup",
                        action="store_true",
                        dest="no_git_backup",
                        default=False,
                        help="Disable git backup")

    args = parser.parse_args()

    if not os.path.isdir(args.src):
        raise FileNotFoundError(f"No such directory: {args.src}")

    if not os.path.isdir(args.configs):
        raise FileNotFoundError(f"No such directory: {args.configs}")

    source = args.src
    configs = args.configs
    with_ccache = args.ccache
    keep_cache = args.keep_cache
    ccache_cachedir = args.ccache_dir
    backup = args.backup
    results_csv = args.results
    with_incremental = args.incremental
    target_binary = args.target
    ccache_stats_dir = args.ccache_stats_dir
    with_debug = args.ccache_debug
    no_git_backup = args.no_git_backup


    if source.endswith('/'):
        source = configs[:-1]
    if configs.endswith('/'):
        configs = configs[:-1]

    if with_ccache:
        debug("[Ccache] Enabled")
        debug(f"[Ccache] Setting cache directory: {ccache_cachedir}")
        ccache_set_dir(ccache_cachedir)
        debug("[Ccache] Setting cache size: 1To")
        ccache_set_size(1, 'T')
        if not keep_cache:
            debug("[Ccache] Deep clean")
            ccache_clean()

        if with_debug:
            ccache_enable_debug()

        ccache_stats("Initialization", ccache_stats_dir)
    else:
        debug("[Ccache] Disabled")


    debug(f"[fs] Change directory {source}")
    os.chdir(source)

    debug("[git] Setting git")
    if os.path.isdir(".git"):
        debug("[git] Already a git repo")
    else:
        debug("[git] Initialization")
        git_init()
        debug(f"[git] Configuration: user.email={DUMMY_EMAIL}, user.name={DUMMY_NAME}")
        git_config("user", "email", DUMMY_EMAIL)
        git_config("user", "name", DUMMY_NAME)
        debug("[git] Adding everything")
        git_add_all()
        debug("[git] Committing source")
        git_commit("source")

    if backup:
        if backup.endswith('/'):
            backup = backup[:-1]
        if not no_git_backup:
            debug(f"[git] Clone {source} -> {backup}")
            git_clone(source, backup)
        os.makedirs('/'.join([backup, TRACEFILES]), exist_ok=True)


    debug("=== Starting builds ===")

    result_stream = open(results_csv, 'w')
    result_stream.write("config,time(s),success,binary\n")

    confs = os.listdir(configs)
    confs.sort()
    for c in confs:

        if not with_incremental:
            debug("[git] Checkout: master")
            git_checkout("master")

        debug(f"[git] Create branch: {c}")
        git_create_branch(c)

        if with_incremental:
            for to_delete in {BUILD_STDOUT, BUILD_STDERR, BUILD_EXIT_STATUS}:
                if os.path.isfile(to_delete):
                    debug(f"[fs] Removing {to_delete}")
                    os.remove(to_delete)

        c_path = '/'.join([configs, c])
        debug(f"[{c}] Build --", end=" ")
        status = \
            build(jobs=None, config=c_path, with_time=True, ccache=with_ccache)
        time = get_build_time()
        success = build_is_ok(target_binary)
        binary_size = None
        if success:
            binary_size = os.path.getsize(target_binary)
        debug(f"time: {time}s,succes: {success},binary: {binary_size}")
        result_stream.write(f"{c},{time},{success},{binary_size}\n")
        debug("[git] Add all")
        git_add_all()
        debug("[git] Commit: Clean build")
        git_commit("Clean build")

        if with_ccache:
            debug(f"[Ccache] Statistics -> {ccache_stats_dir}")
            ccache_stats(c, ccache_stats_dir)
        if backup:
            if not no_git_backup:
                debug(f"[git] (Backup) git pull from {backup}")
                git_pull(f"{backup}/{source.split('/')[-1]}")
            debug(f"[fs] (Backup) Copying files:", end=" ")
            for to_save in \
                {BUILD_STDOUT, BUILD_STDERR, BUILD_EXIT_STATUS, target_binary}:
                if os.path.isfile(to_save):
                    debug(f"{to_save}", end=" ")
                    new_name = '_'.join([c, to_save])
                    to_save_path = '/'.join([backup, TRACEFILES, new_name])
                    shutil.copy(to_save, to_save_path)
            debug("")

    debug("[fs] End: closing results stream")
    result_stream.close()

    if backup:
        debug(f"[fs] (Backup) Copying {results_csv} -> {backup}")
        shutil.copy(results_csv, backup)
        if with_ccache:
            debug(f"[Ccache/fs] (Backup) Copying {ccache_stats_dir} -> {backup}")
            shutil.copy(ccache_stats_dir, backup)
            debug(f"[Ccache/fs] (Backup) Copying {ccache_cachedir} -> {backup}")
            shutil.copytree(ccache_cachedir, f"{backup}/ccache")


if __name__ == "__main__":
    main()
