# -*- coding: utf-8 -*-
"""
九原吉祥门窗服务 · 微信长图海报生成器

用法：python3 promo/make_long_poster.py
产出：
  promo/微信长图.png / .jpg        —— 主图（1080 宽，约 1:3.5 长图）
  promo/微信长图-首屏.jpg           —— 从长图顶部裁 1080×1080，朋友圈/群缩略用
  promo/long.html                  —— 可再编辑的版式源文件

设计要点：
  * 信息分层：首屏就能看到品牌 + 两个电话，滑到底能扫码；电话与二维码各出现两次
  * 字号按「微信里被压到 390px 宽仍可读」反推，正文不小于 28px
  * 长度控制在 1:3.5 左右：太长微信里会缩成细条，反而没人看完
  * 二维码用洋红占位 + PIL 精确回贴，避免无头浏览器超高视口漏渲染，且不被插值糊掉
  * 所有图片内嵌 data URI，截图自包含、无加载时序问题
"""
import base64
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMO = os.path.join(ROOT, "promo")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

WORKS = {
    "w01": "assets/img/works/w01-frame-truck.webp",
    "w02": "assets/img/works/w02-old-opening.webp",
    "w03": "assets/img/works/w03-level.webp",
    "w04": "assets/img/works/w04-drill.webp",
    "w06": "assets/img/works/w06-seal.webp",
    "w07": "assets/img/works/w07-double.webp",
    "w09": "assets/img/works/w09-living.webp",
    "w12": "assets/img/works/w12-dark.webp",
    "w00": "assets/img/works/w00-lead.webp",
}
QRS = {
    "jjs": "assets/img/qr/wx-jijishan.png",
    "lhx": "assets/img/qr/wx-liuhongxia.png",
}


def data_uri(rel, mime):
    with open(os.path.join(ROOT, rel), "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())


HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>九原吉祥门窗服务 · 微信长图</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  html,body{background:#062a45}
  body{width:1080px;font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;-webkit-font-smoothing:antialiased}
  .poster{width:1080px;overflow:hidden;color:#fff}
  .eyebrow{font-size:24px;letter-spacing:4px;font-weight:700;opacity:.72}
  h2{font-size:46px;font-weight:800;letter-spacing:1px;line-height:1.24;margin-top:8px}
  .sub{font-size:28px;line-height:1.55;opacity:.82;margin-top:10px}

  /* ---------- 1 首屏 ---------- */
  .hero{position:relative;padding:44px 64px 36px;background:linear-gradient(168deg,#0c4370 0%,#083453 46%,#062a45 100%);overflow:hidden}
  .hero::before{content:"";position:absolute;width:760px;height:760px;right:-280px;top:-340px;border-radius:50%;background:radial-gradient(circle,rgba(42,139,208,.34),transparent 70%)}
  .hero>*{position:relative}
  .brand{display:flex;align-items:center;gap:18px}
  .mark{width:74px;height:74px;flex:0 0 auto;border-radius:20px;background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.3);display:flex;align-items:center;justify-content:center}
  .mark svg{width:40px;height:40px;stroke:#fff;fill:none;stroke-width:1.7}
  .brand .name{font-size:42px;font-weight:800;letter-spacing:1px}
  .brand .loc{font-size:26px;color:rgba(255,255,255,.68);margin-top:6px;letter-spacing:.5px}
  h1{font-size:72px;line-height:1.22;font-weight:800;letter-spacing:1px;margin-top:28px}
  h1 em{font-style:normal;color:#ffbe8c}
  .lead{font-size:28px;line-height:1.6;color:rgba(255,255,255,.86);margin-top:14px}
  .tags{display:flex;flex-wrap:wrap;gap:12px;margin-top:22px}
  .tags span{font-size:27px;font-weight:600;padding:10px 20px;border-radius:100px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.24)}
  .tels{margin-top:26px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.2);border-radius:20px;padding:20px 26px}
  .tels .hint{font-size:25px;color:rgba(255,255,255,.66);letter-spacing:1px;margin-bottom:10px}
  .telrow{display:flex;align-items:baseline;gap:20px;padding:4px 0}
  .telrow em{font-style:normal;font-size:30px;color:rgba(255,255,255,.85);width:116px;flex:0 0 auto}
  .telrow b{font-size:62px;font-weight:800;letter-spacing:2px;color:#ffb27a;line-height:1.12}
  .strip{display:flex;margin-top:24px;border-top:1px solid rgba(255,255,255,.18);border-bottom:1px solid rgba(255,255,255,.18);padding:18px 0}
  .strip div{flex:1;text-align:center;position:relative;font-size:33px;font-weight:800;letter-spacing:1px}
  .strip div+div::before{content:"";position:absolute;left:0;top:2px;bottom:2px;width:1px;background:rgba(255,255,255,.2)}

  /* ---------- 2 四项服务（浅底） ---------- */
  .light{background:#f3f7fa;color:#12324a}
  .light .eyebrow{color:#1d6fa8;opacity:1}
  .light .sub{color:#4a6478;opacity:1}
  .sec{padding:40px 64px 42px}
  .sec__head{margin-bottom:22px}
  .svc{display:flex;gap:20px;align-items:flex-start;padding:16px 0;border-top:1px solid #d9e3ec}
  .svc:first-of-type{border-top:none}
  .svc__no{width:64px;height:64px;flex:0 0 auto;border-radius:18px;background:#0d4a7b;color:#fff;font-size:28px;font-weight:800;display:flex;align-items:center;justify-content:center}
  .svc__body{flex:1}
  .svc__title{font-size:36px;font-weight:800;letter-spacing:.5px;line-height:1.2}
  .svc__desc{font-size:28px;line-height:1.55;color:#45637a;margin-top:6px}
  .svc__desc b{color:#12324a;font-weight:700}

  /* ---------- 3 三大承诺（中蓝底，三列） ---------- */
  .mid{background:linear-gradient(180deg,#0d4a7b,#083453);padding:40px 64px 42px}
  .prom__row{display:flex;gap:18px;margin-top:24px}
  .prom{flex:1;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.16);border-radius:18px;padding:22px 20px}
  .prom__no{font-size:26px;font-weight:800;color:#ffbe8c}
  .prom__title{font-size:32px;font-weight:800;letter-spacing:.5px;margin-top:8px}
  .prom__desc{font-size:26px;line-height:1.6;color:rgba(255,255,255,.8);margin-top:10px}

  /* ---------- 4 施工实拍（浅底，8 图两排） ---------- */
  .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
  .grid figure{position:relative;border-radius:12px;overflow:hidden;background:#dce6ee}
  .grid img{width:100%;height:168px;object-fit:cover;display:block}
  .grid figcaption{position:absolute;left:0;right:0;bottom:0;padding:20px 8px 8px;font-size:22px;font-weight:700;color:#fff;background:linear-gradient(180deg,transparent,rgba(6,26,42,.88))}
  .works__note{margin-top:18px;font-size:27px;color:#45637a;line-height:1.55}

  /* ---------- 5 五步流程（白底细条） ---------- */
  .steps{background:#fff;color:#12324a;padding:28px 64px 30px}
  .steps h2{font-size:34px;margin-top:0}
  .steps__row{display:flex;margin-top:16px}
  .step{flex:1;position:relative;text-align:center;padding:0 6px}
  .step .dot{width:52px;height:52px;margin:0 auto 10px;border-radius:50%;background:#0d4a7b;color:#fff;font-size:26px;font-weight:800;display:flex;align-items:center;justify-content:center;position:relative;z-index:1}
  .step b{display:block;font-size:26px;font-weight:800}
  .step+.step::before{content:"";position:absolute;left:0;top:26px;width:100%;height:2px;background:#d9e3ec;z-index:0;transform:translateX(-50%)}

  /* ---------- 6 底部联系 ---------- */
  .contact{position:relative;padding:42px 64px 34px;background:linear-gradient(170deg,#0a3d68,#062a45);overflow:hidden}
  .contact::before{content:"";position:absolute;width:640px;height:640px;left:-260px;bottom:-320px;border-radius:50%;background:radial-gradient(circle,rgba(242,101,27,.18),transparent 70%)}
  .contact>*{position:relative}
  .contact__hint{font-size:28px;color:rgba(255,255,255,.8);line-height:1.55;margin-top:10px}
  .qrs{display:flex;gap:40px;justify-content:center;margin-top:26px}
  .qr{flex:0 0 auto;text-align:center;width:280px}
  .qr-slot{width:280px;height:280px;background:#ff00ff;border-radius:20px}
  .qr__cap{font-size:28px;font-weight:700;margin-top:12px;color:#fff}
  .qr__cap span{display:block;font-size:24px;font-weight:400;color:rgba(255,255,255,.66);margin-top:4px}
  .contact__tels{margin-top:26px;border-top:1px solid rgba(255,255,255,.18);padding-top:18px}
  .contact__tels .telrow b{font-size:54px}
  .addr{margin-top:18px;font-size:26px;color:rgba(255,255,255,.72);line-height:1.65}
  .foot{margin-top:20px;padding-top:18px;border-top:1px solid rgba(255,255,255,.16);display:flex;justify-content:space-between;font-size:24px;color:rgba(255,255,255,.6);letter-spacing:.5px}
  .foot b{color:#fff;font-weight:700}
</style>
</head>
<body>
<div class="poster">

  <!-- 1 首屏 -->
  <div class="hero">
    <div class="brand">
      <div class="mark"><svg viewBox="0 0 24 24"><rect x="3.5" y="3.5" width="17" height="17" rx="2"/><path d="M12 3.5v17M3.5 12h17"/></svg></div>
      <div>
        <div class="name">九原吉祥门窗服务</div>
        <div class="loc">包头市九原区 · 本地专业老师傅直营 · 没有中间商</div>
      </div>
    </div>
    <h1>门窗的事<br>找本地师傅<em>一次办妥</em></h1>
    <div class="lead">断桥铝门窗安装、金刚纱窗定制、漏风维修、换漏气玻璃。<br>先量尺、先报价、后施工，活不分大小都能上门。</div>
    <div class="tags">
      <span>断桥铝门窗</span><span>金刚纱窗</span><span>漏风维修</span><span>换漏气玻璃</span>
    </div>
    <div class="tels">
      <div class="hint">打电话，师傅本人接 · 就近约上门量尺</div>
      <div class="telrow"><em>吉继山</em><b>15147291185</b></div>
      <div class="telrow"><em>刘红侠</em><b>18247359113</b></div>
    </div>
    <div class="strip">
      <div>没有中间商</div><div>质量保证</div><div>本地专业老师傅</div>
    </div>
  </div>

  <!-- 2 四项服务 -->
  <div class="light sec">
    <div class="sec__head">
      <div class="eyebrow">能帮您做什么</div>
      <h2>装新窗、修旧窗，一样拿手</h2>
      <div class="sub">只坏一处，就不换整套。活不分大小，都能上门给您处理。</div>
    </div>
    <div class="svc">
      <div class="svc__no">01</div>
      <div class="svc__body">
        <div class="svc__title">断桥铝门窗安装</div>
        <div class="svc__desc">旧窗换新、封阳台、全屋换窗；<b>按洞口定制</b>，发泡填充加耐候胶密封。</div>
      </div>
    </div>
    <div class="svc">
      <div class="svc__no">02</div>
      <div class="svc__body">
        <div class="svc__title">金刚纱窗定制</div>
        <div class="svc__desc"><b>304 不锈钢金刚网</b>，防蚊防鼠防坠窗；可拆洗，旧网破了能单换。</div>
      </div>
    </div>
    <div class="svc">
      <div class="svc__no">03</div>
      <div class="svc__body">
        <div class="svc__title">维修窗户漏风</div>
        <div class="svc__desc">胶条老化、锁点松、胶开裂、扇下垂，<b>先找漏点再动手</b>，能调不换。</div>
      </div>
    </div>
    <div class="svc">
      <div class="svc__no">04</div>
      <div class="svc__body">
        <div class="svc__title">更换漏气玻璃</div>
        <div class="svc__desc">中空玻璃起雾进水珠是密封失效，<b>按原尺寸单换一块</b>，不用换整窗。</div>
      </div>
    </div>
  </div>

  <!-- 3 三大承诺 -->
  <div class="mid">
    <div class="sec__head">
      <div class="eyebrow">为什么找我们</div>
      <h2>没有中间商 · 质量保证 · 本地专业老师傅</h2>
    </div>
    <div class="prom__row">
      <div class="prom">
        <div class="prom__no">01</div>
        <div class="prom__title">没有中间商</div>
        <div class="prom__desc">电话就是师傅本人接，不转包不派单，量尺到售后都是同一个人。</div>
      </div>
      <div class="prom">
        <div class="prom__no">02</div>
        <div class="prom__title">质量保证</div>
        <div class="prom__desc">材料按报价配置进场可当场验，工序一步不省，装完逐项试。</div>
      </div>
      <div class="prom">
        <div class="prom__no">03</div>
        <div class="prom__title">本地专业老师傅</div>
        <div class="prom__desc">两位师傅在九原住、在九原干，就近上门，干完留电话找得到人。</div>
      </div>
    </div>
  </div>

  <!-- 4 施工实拍 -->
  <div class="light sec">
    <div class="sec__head">
      <div class="eyebrow">真实施工现场</div>
      <h2>不是效果图，是干活时随手拍的</h2>
      <div class="sub">没有摆拍、没有网图。材料自己拉、工序自己干，不转手。</div>
    </div>
    <div class="grid">
      <figure><img src="__W01__" alt="整车窗框送到现场"><figcaption>材料进场</figcaption></figure>
      <figure><img src="__W02__" alt="旧窗拆下新框就位"><figcaption>拆旧安装</figcaption></figure>
      <figure><img src="__W03__" alt="水平仪找正窗框"><figcaption>找正固定</figcaption></figure>
      <figure><img src="__W04__" alt="打孔固定框体"><figcaption>打孔固定</figcaption></figure>
      <figure><img src="__W06__" alt="框周打胶密封"><figcaption>框周打胶</figcaption></figure>
      <figure><img src="__W07__" alt="双扇窗换好"><figcaption>双扇完工</figcaption></figure>
      <figure><img src="__W09__" alt="客厅大窗完工"><figcaption>客厅大窗</figcaption></figure>
      <figure><img src="__W00__" alt="当着业主的面施工"><figcaption>业主在场</figcaption></figure>
    </div>
    <div class="works__note">8 张现场照片，从抬框上门到完工验收，都是我们自己的工地。</div>
  </div>

  <!-- 5 五步流程 -->
  <div class="steps">
    <h2>怎么合作 · 五步走</h2>
    <div class="steps__row">
      <div class="step"><div class="dot">1</div><b>电话咨询</b></div>
      <div class="step"><div class="dot">2</div><b>上门量尺</b></div>
      <div class="step"><div class="dot">3</div><b>明码报价</b></div>
      <div class="step"><div class="dot">4</div><b>专业施工</b></div>
      <div class="step"><div class="dot">5</div><b>验收售后</b></div>
    </div>
  </div>

  <!-- 6 底部联系 -->
  <div class="contact">
    <div class="eyebrow">联系我们</div>
    <h2>一个电话，师傅上门</h2>
    <div class="contact__hint">不方便打电话，长按识别二维码加微信，把窗框、胶条缝、玻璃起雾的地方拍张照片发过来。</div>
    <div class="qrs">
      <div class="qr"><div class="qr-slot" id="q1"></div><div class="qr__cap">吉继山 · 微信<span>长按识别加好友</span></div></div>
      <div class="qr"><div class="qr-slot" id="q2"></div><div class="qr__cap">刘红侠 · 微信<span>长按识别加好友</span></div></div>
    </div>
    <div class="contact__tels">
      <div class="telrow"><em>吉继山</em><b>15147291185</b></div>
      <div class="telrow"><em>刘红侠</em><b>18247359113</b></div>
    </div>
    <div class="addr">包头市九原区 · 就近上门<br>来电时说下小区名称、大概几樘窗、想装还是想修，师傅能更快给您报个准价。</div>
    <div class="foot">
      <span><b>九原吉祥门窗服务</b> · 没有中间商 · 质量保证</span>
      <span>长按识别二维码 · 存图转发都行</span>
    </div>
  </div>

</div>
</body>
</html>
"""


def build_html():
    html = HTML
    for key, rel in WORKS.items():
        html = html.replace("__%s__" % key.upper(), data_uri(rel, "image/webp"))
    return html


def shoot(html_path, raw_png):
    import tempfile
    profile = tempfile.mkdtemp(prefix="jjs-long-")
    cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-sandbox",
        "--user-data-dir=" + profile,
        "--force-device-scale-factor=1",
        "--window-size=1080,5000",
        "--virtual-time-budget=4000",
        "--screenshot=" + raw_png,
        "file://" + html_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if not os.path.exists(raw_png):
        sys.exit("Chrome 截图失败：\n" + r.stderr[-2000:])
    return r


def compose(raw_png):
    from PIL import Image, ImageDraw
    import numpy as np
    import cv2

    img = Image.open(raw_png).convert("RGB")
    arr = np.array(img)
    # 洋红占位：精确定位两个二维码框
    mask = ((arr[:, :, 0] > 235) & (arr[:, :, 1] < 25) & (arr[:, :, 2] > 235)).astype("uint8") * 255
    n, labels, stats, cents = cv2.connectedComponentsWithStats(mask, 8)
    boxes = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area > 40000 and 220 < w < 360 and 220 < h < 360:
            boxes.append((x, y, w, h))
    boxes.sort(key=lambda b: b[0])
    if len(boxes) != 2:
        sys.exit("二维码占位识别失败，找到 %d 个：%s" % (len(boxes), boxes))

    # 裁掉底部空白（body 纯背景色）
    bg = np.array([6, 42, 69])
    diff = np.abs(arr.astype(int) - bg).sum(axis=2)
    rows = np.where(diff.max(axis=1) > 18)[0]
    content_bottom = int(rows.max()) + 1 if len(rows) else arr.shape[0]
    img = img.crop((0, 0, img.width, min(img.height, content_bottom + 2)))

    out = img.copy()
    for (x, y, w, h), rel in zip(boxes, [QRS["jjs"], QRS["lhx"]]):
        qr = Image.open(os.path.join(ROOT, rel)).convert("RGB")
        pad = 10
        side = min(w, h) - pad * 2
        qr = qr.resize((side, side), Image.LANCZOS)
        tile = Image.new("RGB", (side + pad * 2, side + pad * 2), "white")
        tile.paste(qr, (pad, pad))
        mask_r = Image.new("L", tile.size, 0)
        ImageDraw.Draw(mask_r).rounded_rectangle((0, 0, tile.width - 1, tile.height - 1), radius=18, fill=255)
        out.paste(tile, (x + (w - tile.width) // 2, y + (h - tile.height) // 2), mask_r)
    return out, boxes


def verify(path, expect=2):
    try:
        import zxingcpp
        from PIL import Image
        found = zxingcpp.read_barcodes(Image.open(path))
        ok = [f for f in found if "QR" in str(f.format)]
        print("  二维码解码：%d 个" % len(ok))
        for f in ok:
            print("    ->", f.text[:70])
        return len(ok) >= expect
    except Exception as e:
        print("  二维码校验跳过（%s）" % e)
        return None


def main():
    html_path = os.path.join(PROMO, "long.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build_html())
    print("已生成版式源文件 long.html")

    raw = os.path.join(PROMO, "_long_raw.png")
    shoot(html_path, raw)
    print("已截图")

    out, boxes = compose(raw)
    png = os.path.join(PROMO, "微信长图.png")
    jpg = os.path.join(PROMO, "微信长图.jpg")
    out.save(png, "PNG", optimize=True)
    q = 88
    while True:
        out.save(jpg, "JPEG", quality=q, optimize=True, progressive=True, subsampling=0)
        size = os.path.getsize(jpg)
        if size <= 2_200_000 or q <= 72:
            break
        q -= 4
    print("成品：%s  %dx%d" % (png, out.width, out.height))
    print("成品：%s  %dx%d  quality=%d  %.2f MB  (比例 1:%.2f)" %
          (jpg, out.width, out.height, q, size / 1024 / 1024, out.height / out.width))

    top = out.crop((0, 0, 1080, 1080))
    top_jpg = os.path.join(PROMO, "微信长图-首屏.jpg")
    top.save(top_jpg, "JPEG", quality=88, optimize=True, progressive=True)
    print("首屏方图：%s  1080x1080  %.2f MB" % (top_jpg, os.path.getsize(top_jpg) / 1024 / 1024))

    print("校验成品二维码：")
    verify(jpg)
    os.remove(raw)


if __name__ == "__main__":
    main()
