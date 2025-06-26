# build.py
import os
import shutil
import subprocess
import sys

def clean():
    shutil.rmtree('build', ignore_errors=True)
    shutil.rmtree('dist', ignore_errors=True)
    for d in os.listdir('.'):
        if d.endswith('.egg-info'):
            shutil.rmtree(d)

def build():
    print("🔨 Building the package...")
    result = subprocess.run([sys.executable, 'setup.py', 'sdist', 'bdist_wheel'])
    if result.returncode != 0:
        print("❌ Build failed.")
        exit(1)

def install():
    if not os.path.exists('dist'):
        print("❌ No build output found. Did you run build()?") 
        return
    files = os.listdir('dist')
    whl = next((f for f in files if f.endswith('.whl')), None)
    if whl:
        subprocess.run(['pip', 'install', '--upgrade', os.path.join('dist', whl)])
    else:
        print("❌ No .whl file found in dist/")


def release():
    clean()
    build()
    install()

if __name__ == "__main__":
    release()
