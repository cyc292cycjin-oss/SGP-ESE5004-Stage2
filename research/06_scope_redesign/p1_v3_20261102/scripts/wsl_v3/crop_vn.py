from PIL import Image
from pathlib import Path
S=Path("/mnt/c/Users/20122/AppData/Local/Temp/claude/D--ResearchWorkspaces/3b84a8d8-c3d9-4930-9986-da94fd4c6e0e/scratchpad/apec_img")
im=Image.open(S/"p161_0_Image20.png"); print(im.size)
top,bot=478,760
a=im.crop((0,top,1160,bot)).resize((2320,(bot-top)*2),Image.LANCZOS); a.save(S/"vn_left.png")
b=im.crop((1040,top,2175,bot)).resize((2270,(bot-top)*2),Image.LANCZOS); b.save(S/"vn_right.png")
