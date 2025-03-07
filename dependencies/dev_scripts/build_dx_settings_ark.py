# build_ark.py
from pathlib import Path
from subprocess import CalledProcessError
from sys import platform
import subprocess
from pathlib import Path
from check_git_updated import check_git_updated
from pull_repo import pull_repo

def rm_tree(pth):
    pth = Path(pth)
    for child in pth.glob('*'):
        if child.is_file():
            child.unlink()
        else:
            rm_tree(child)
    pth.rmdir()

def make_executable_binaries():
    cmd_chmod_arkhelper_linux = "chmod +x dependencies/linux//arkhelper".split()
    subprocess.check_output(cmd_chmod_arkhelper_linux, shell=(platform == "win32"), cwd="..")
    cmd_chmod_dtab_linux = "chmod +x dependencies/linux//dtab".split()
    subprocess.check_output(cmd_chmod_dtab_linux, shell=(platform == "win32"), cwd="..")

# darwin: mac

# if xbox is true, build the Xbox ARK
# else, build the PS3 ARK
def build_dxsl_ark():
    # directories used in this script
    cwd = Path(__file__).parent # current working directory (dev_scripts)
    root_dir = cwd.parents[1] # root directory of the repo
    # print(f"root dir: {root_dir}")

    files_to_remove = "*.milo_ps3"

    # clone/pull dx_settings_loader_path
    dx_settings_loader_path = pull_repo(repo_url="https://github.com/hmxmilohax/dx-settings-loader.git", repo_path=cwd)
    # print(f"DX path: {dx_settings_loader_path}")
    print("Building DX Settings Loader...")

    ark_location = dx_settings_loader_path.joinpath("_ark")
    build_location = dx_settings_loader_path.joinpath("_build/xbox/gen")

    relative_ark_location = f"{str(ark_location).replace(str(root_dir),'')}"[1:]
    relative_build_location = f"{str(build_location).replace(str(root_dir),'')}"[1:]

    # build the binaries if on linux/other OS
    if platform != "win32" and platform != "darwin":
        make_executable_binaries()
        
    patch_hdr_version = "dxsl_xbox"

    # pull the latest changes from the Rock Band 3 Deluxe repo if necessary
    if not check_git_updated(repo_url="https://github.com/hmxmilohax/dx-settings-loader", repo_root_path=dx_settings_loader_path):
        cmd_pull = "git pull https://github.com/hmxmilohax/dx-settings-loader main".split()
        subprocess.run(cmd_pull, shell=(platform == "win32"))

    # temporarily move other console's files out of the ark to reduce overall size
    for f in ark_location.rglob(files_to_remove):
        temp_path = str(f).replace(f"{str(root_dir)}\\", "").replace(f"{str(root_dir)}/","")
        # print(temp_path)
        the_new_filename = root_dir.joinpath("_tmp").joinpath(temp_path)
        the_new_filename.parent.mkdir(parents=True, exist_ok=True)
        #print(f"moving file {temp_path} to {the_new_filename}")
        f.rename(the_new_filename)
    
    # build the ark
    failed = False
    try:
        if platform == "win32":
            cmd_build = f"dependencies\windows\\arkhelper.exe dir2ark {relative_ark_location} {relative_build_location} -n {patch_hdr_version} -e -v 5".split()
        elif platform == "darwin":
            cmd_build = f"dependencies/macos/arkhelper dir2ark {relative_ark_location} {relative_build_location} -n {patch_hdr_version} -e -v 5".split()
        else:
            cmd_build = f"dependencies/linux/arkhelper dir2ark {relative_ark_location} {relative_build_location} -n {patch_hdr_version} -e -v 5".split()
        subprocess.check_output(cmd_build, shell=(platform == "win32"), cwd="..")
    except CalledProcessError as e:
        print(e.output)
        failed = True

    if not failed:
        print("Successfully built DX Settings Loader ARK.")
        print("Copying DX Settings Loader to final build path.")
        for dxsl_file_path in ["_build/xbox/dx-settings-loader.xex", "_build/xbox/gen/dxsl_xbox.hdr", "_build/xbox/gen/dxsl_xbox_0.ark"]:
            root_dir.joinpath(dxsl_file_path).write_bytes(dx_settings_loader_path.joinpath(dxsl_file_path).read_bytes())
        return True
    else:
        print("Error building ARK. Check your modifications or run git_reset.py to rebase your repo.")
        return False