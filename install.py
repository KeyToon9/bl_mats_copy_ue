# Thanks to DECALMACHINE

import bpy
import os, sys, site, platform
import subprocess

def get_python_path():
    pythonbinpath = None
    try:
        # 2.92 and older
        pythonbinpath = bpy.app.binary_path_python
    except AttributeError:
        # 2.93 and later
        import sys
        pythonbinpath = sys.executable

    if platform.system() == "Windows":
        pythonlibpath = os.path.join(os.path.dirname(os.path.dirname(pythonbinpath)), "lib")

    else:
        pythonlibpath = os.path.join(os.path.dirname(os.path.dirname(pythonbinpath)), "lib", os.path.basename(pythonbinpath)[:-1])
    
    ensurepippath = os.path.join(pythonlibpath, "ensurepip")
    usersitepackagespath = site.getusersitepackages()

    return pythonbinpath, ensurepippath, usersitepackagespath

def install_pip(pythonbinpath, ensurepippath, log, mode='USER'):
    if mode == 'USER':
        cmd = [pythonbinpath, ensurepippath, "--upgrade", "--user"]

    elif mode == 'ADMIN':
        cmd = [pythonbinpath, ensurepippath, "--upgrade"]

    pip = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    pipout = [out.strip() for out in pip.stdout.decode('utf-8').split("\n") if out]
    piperr = [err.strip() for err in pip.stderr.decode('utf-8').split("\n") if err]

    log += pipout
    log += piperr

    if pip.returncode == 0:
        for out in pipout + piperr:
            print(" »", out)

        print("Sucessfully installed pip!\n")
        return True

    else:
        for out in pipout + piperr:
            print(" »", out)

        print("Failed to install pip!\n")
        return False, pipout + piperr

def update_pip(pythonbinpath, log, mode='USER'):
    if mode == 'USER':
        cmd = [pythonbinpath, "-m", "pip", "install", "--upgrade", "--user", "pip"]

    elif mode == 'ADMIN':
        cmd = [pythonbinpath, "-m", "pip", "install", "--upgrade", "pip"]

    update = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    updateout = [out.strip() for out in update.stdout.decode('utf-8').split("\n") if out]
    updateerr = [err.strip() for err in update.stderr.decode('utf-8').split("\n") if err]

    log += updateout
    log += updateerr

    if update.returncode == 0:
        for out in updateout + updateerr:
            print(" »", out)

        print("Sucessfully updated pip!\n")
        return True
    else:
        for out in updateout + updateerr:
            print(" »", out)

        print("Failed to update pip!\n")
        return False

def install_pyperclip(pythonbinpath, log, version=None, mode='USER'):
    if mode == 'USER':
        if version:
            cmd = [pythonbinpath, "-m", "pip", "install", "--upgrade", "--user", "pyperclip==%s" % (version)]
        else:
            cmd = [pythonbinpath, "-m", "pip", "install", "--upgrade", "--user", "pyperclip"]

    else:
        if version:
            cmd = [pythonbinpath, "-m", "pip", "install", "--upgrade", "pyperclip==%s" % (version)]
        else:
            cmd = [pythonbinpath, "-m", "pip", "install", "--upgrade", "pyperclip"]

    pyperclip = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    pyperclipout = [out.strip() for out in pyperclip.stdout.decode('utf-8').split("\n") if out]
    pypercliperr = [err.strip() for err in pyperclip.stderr.decode('utf-8').split("\n") if err]

    log += pyperclipout
    log += pypercliperr

    if pyperclip.returncode == 0:
        for out in pyperclipout + pypercliperr:
            print(" »", out)

        print("Sucessfully installed pyperclip!\n")
        return True
    else:
        for out in pyperclipout + pypercliperr:
            print(" »", out)

        print("Failed to install pyperclip!\n")
        return False

def update_sys_path(usersitepackagespath, log):
    if usersitepackagespath in sys.path:
        print("\nFound %s in sys.path." % (usersitepackagespath))
        log.append("\nFound %s in sys.path." % (usersitepackagespath))

    else:
        sys.path.append(usersitepackagespath)

        print("\nAdded %s to sys.path" % (usersitepackagespath))
        log.append("\nAdded %s to sys.path" % (usersitepackagespath))

def test_import_pyperclip(installed, log, usersitepackagespath=None):
    if installed:
        if usersitepackagespath:
            update_sys_path(usersitepackagespath, log)

        bpy.utils.refresh_script_paths()

        # try to import Image - if it does, PIL is ready to go
        try:
            import pyperclip

            print("Successfully imported pyperclip module.")
            log.append("Successfully imported pyperclip module.")

            return True, False

        # if it fails, a restart may be required, or an Admin installation may required
        except:
            print("Failed to import pyperclip module. Restart is required.")
            log.append("Failed to import pyperclip module. Restart is required.")

            return False, True

    else:
        return False, False