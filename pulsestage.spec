# Reproducible onedir desktop bundle; no separately installed browser/runtime.
from pathlib import Path
import importlib.metadata as metadata
project_root = Path(SPECPATH)
data = [(str(project_root/'src/ui'), 'src/ui'), (str(project_root/'pulsestage.ico'), '.')]
for filename in ('PULSESTAGE-USER-GUIDE.html','PULSESTAGE-USER-GUIDE.md','PULSESTAGE-DESKTOP.md','THIRD-PARTY-NOTICES.txt'):
    path=project_root/'docs'/filename
    if path.exists(): data.append((str(path), 'docs'))
for package in ('PySide6','PySide6_Essentials','PySide6_Addons','shiboken6'):
    distribution=metadata.distribution(package)
    for file in distribution.files or []:
        if '/licenses/' in str(file).lower() or 'license' in Path(file).name.lower():
            path=Path(distribution.locate_file(file))
            if path.is_file(): data.append((str(path), 'licenses/'+package+'/'+str(Path(file).parent)))
a=Analysis([str(project_root/'src/launcher/desktop_app.py')],pathex=[str(project_root)],
    datas=data, binaries=[], hiddenimports=['PySide6.QtWebEngineWidgets','PySide6.QtWebChannel'],
    excludes=['tkinter','matplotlib','scipy','pandas'], noarchive=False)
# Qt uses Windows' own unversioned ICU API. Never shadow it with a different
# ICU build discovered in unrelated tools on a developer's PATH.
a.binaries = [item for item in a.binaries if Path(item[0]).name.lower() not in ('icuuc.dll','icuin.dll','icudt.dll')]
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='PulseStage',console=False,
        icon=str(project_root/'pulsestage.ico'),upx=False,version=str(project_root/'windows-version.txt'))
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='PulseStage')
