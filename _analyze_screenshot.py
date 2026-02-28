from PIL import Image
import numpy as np
img = Image.open(r"d:\IstanbulTrafikAlerter\emulator-map-after-fix.png").convert("RGB")
a = np.array(img)
std = a.std(axis=(0,1))
mean = a.mean(axis=(0,1))
# edge density proxy
lum = (0.2126*a[:,:,0] + 0.7152*a[:,:,1] + 0.0722*a[:,:,2]).astype(np.float32)
gx = np.abs(np.diff(lum, axis=1)).mean()
gy = np.abs(np.diff(lum, axis=0)).mean()
# color richness by downsampling and counting unique colors
small = np.array(img.resize((200, 400), Image.Resampling.BILINEAR))
uniq = np.unique(small.reshape(-1,3), axis=0).shape[0]
print({"mean_rgb": mean.round(2).tolist(), "std_rgb": std.round(2).tolist(), "edge_x": round(float(gx),2), "edge_y": round(float(gy),2), "unique_colors_200x400": int(uniq)})
if uniq > 25000 and float(gx) > 8 and float(gy) > 8:
    print("ANALYSIS: Map tiles are visually loaded (high texture/color diversity).")
else:
    print("ANALYSIS: Potential blank/flat map. Needs further check.")
