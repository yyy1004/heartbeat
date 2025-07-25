pyinstaller --noconfirm --windowed --onedir main.py
--onefile 会把所有资源打到一个自解包段，杀软常会拦截

 pyinstaller --noconfirm --windowed --onedir --hidden-import=ssl  --hidden-import=_ssl  main.py