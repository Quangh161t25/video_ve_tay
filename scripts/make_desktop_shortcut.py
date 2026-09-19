import os
from pathlib import Path
import subprocess

target = Path(__file__).resolve().parent.parent / "CHAY_SERVER.bat"
desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
lnk = desktop / "Chay Server Ve Tay.lnk"

vbs_content = f'''Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{str(lnk)}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{str(target)}"
oLink.WorkingDirectory = "{str(target.parent)}"
oLink.IconLocation = "shell32.dll,13"
oLink.Save
'''

vbs_path = Path(__file__).resolve().parent / "temp_make_lnk.vbs"
vbs_path.write_text(vbs_content, encoding="utf-8")
subprocess.run(["cscript", "//nologo", str(vbs_path)])
if vbs_path.exists():
    vbs_path.unlink()

print("LNK created successfully:", lnk.exists())
