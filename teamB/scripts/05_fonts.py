"""フォントをこの映像で使う文字だけに絞って woff2 にする（書き出しを速く・軽くするため。ライセンスは OFL 1.1 で改変・同梱可）。
文字は teamB/comp/ の json と html（生成物を含む）から集める。使い方: python3 teamB/scripts/05_fonts.py"""
import pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parent.parent
F = ROOT / "comp/assets/fonts"
chars = set(chr(c) for c in range(0x20, 0x7f)) | set("　、。・ー―“”「」？！（）：〜…")
for p in list((ROOT / "comp").glob("*.json")) + list((ROOT / "comp/src").glob("*.html")):
    chars |= set(p.read_text())
txt = "".join(sorted(c for c in chars if c >= " "))
(F / "subset_chars.txt").write_text(txt)
for name in ["BIZUDPGothic-Bold", "BIZUDPGothic-Regular", "BIZUDGothic-Bold", "ShipporiMinchoB1-ExtraBold"]:
    subprocess.run(["pyftsubset", str(F / f"{name}.ttf"), f"--text-file={F / 'subset_chars.txt'}",
                    "--flavor=woff2", "--layout-features=*", f"--output-file={F / (name + '.sub.woff2')}"], check=True)
print(len(txt), "chars")
