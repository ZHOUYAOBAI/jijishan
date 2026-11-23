#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
九原吉祥门窗服务 · 30 秒剪辑版宣传片（最终交付版）

12 个段落 × 2.5 秒 = 30.0 秒；配乐 96 BPM，每小节正好 2.5 秒，
所有画面切换都踩在小节线上（卡点剪辑）。

6 段真实现场视频（快切 + 底部工序字幕 + 顶部品牌条 + 进度条）
6 张信息卡（品牌 / 四项服务 / 三个保证 / 完工实拍 / 联系页定格）
片尾最后 2.5 秒完全静止，方便客户暂停截图扫二维码。

产出：promo/宣传片-朋友圈30秒.mp4（覆盖旧版）
依赖：promo/bgm-30.wav（由 make_bgm_30.py 生成）、/tmp/slides/s*.png
"""
import os
import shutil
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
TMP = '/tmp/vseg-final30'
SLIDES = '/tmp/slides'
BGM = os.path.join(BASE, 'bgm-30.wav')
OUT = os.path.join(BASE, '宣传片-朋友圈30秒.mp4')
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SRC_DIR = '/Users/mac/Desktop/大舅'

CLIPS = {
    'a': (os.path.join(SRC_DIR, '0d9bfd2f05b00c9aca4459977c730f5a.mp4'), 6.0),   # 业主+师傅一起抬窗扇
    'b': (os.path.join(SRC_DIR, '0d9bfd2f05b00c9aca4459977c730f5a.mp4'), 9.0),   # 师傅上梯装窗
    'c': (os.path.join(SRC_DIR, '258065be9e283d404cb7c1ec0d2e295a.mp4'), 12.0),  # 业主在旁看装窗
    'd': (os.path.join(SRC_DIR, '258065be9e283d404cb7c1ec0d2e295a.mp4'), 16.0),  # 窗前调试验收
    'e': (os.path.join(SRC_DIR, 'dda55b769fdbdec3e242424c93e58288.mp4'), 6.5),   # 弯腰打胶/收边
    'f': (os.path.join(SRC_DIR, '258065be9e283d404cb7c1ec0d2e295a.mp4'), 20.0),  # 窗装好，站窗前
}

SEG = 2.5
# (类型, 来源, 字幕大标题, 字幕小字, 现场序号)
TIMELINE = [
    ('card', 's1', None, None, None),
    ('clip', 'a', '抬整块玻璃进门', '业主搭手，一起抬进屋', 1),
    ('clip', 'b', '工序自己干', '找正、固定，师傅上梯装窗', 2),
    ('clip', 'c', '当着业主的面做', '业主就在旁边，做到哪步都看得见', 3),
    ('card', 's2', None, None, None),
    ('clip', 'd', '装完当面验收', '开关、密封、排水逐项试', 4),
    ('card', 's9', None, None, None),
    ('clip', 'e', '框周打胶 · 密封做严', '发泡填实，内外打耐候胶', 5),
    ('clip', 'f', '三面窗都换好了', '现场实拍，不是效果图', 6),
    ('card', 's6', None, None, None),
    ('card', 's7', None, None, None),   # 片尾前 2.5s：轻微推近
    ('card', 's7s', None, None, None),  # 最后 2.5s：完全静止，方便截图扫码
]

ENC = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
       '-r', '30', '-an', '-movflags', '+faststart']
FONTS = {
    'bold': '/System/Library/Fonts/STHeiti Medium.ttc',
    'reg': '/System/Library/Fonts/Hiragino Sans GB.ttc',
}


def run(args, label):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print('[%s] 失败' % label)
        print(r.stderr[-2500:])
        sys.exit(1)


def make_caption(path, title, sub, idx):
    """用 PIL 画半透明字幕层：顶部品牌条 + 底部工序字幕 + 进度条。"""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fb = lambda s: ImageFont.truetype(FONTS['bold'], s)
    fr = lambda s: ImageFont.truetype(FONTS['reg'], s)

    # 顶部品牌条
    d.rounded_rectangle((48, 62, 1032, 190), radius=26, fill=(5, 30, 52, 175))
    d.rounded_rectangle((78, 94, 146, 162), radius=16, fill=(255, 174, 116, 255))
    d.rectangle((96, 106, 128, 150), outline=(255, 255, 255, 255), width=3)
    d.line((112, 106, 112, 150), fill=(255, 255, 255, 255), width=3)
    d.line((96, 128, 128, 128), fill=(255, 255, 255, 255), width=3)
    d.text((172, 88), '九原吉祥门窗服务', font=fb(42), fill=(255, 255, 255, 255))
    d.text((174, 142), '包头市九原区 · 本地专业老师傅直营', font=fr(25), fill=(196, 220, 238, 245))
    tag = '现场 %02d / 06' % idx
    tw = d.textbbox((0, 0), tag, font=fr(26))[2]
    d.text((1000 - tw, 120), tag, font=fr(26), fill=(255, 190, 140, 255))

    # 底部字幕卡
    d.rounded_rectangle((48, 1480, 1032, 1792), radius=30, fill=(5, 30, 52, 205))
    d.rounded_rectangle((80, 1524, 92, 1748), radius=6, fill=(255, 174, 116, 255))
    d.text((124, 1524), sub, font=fr(29), fill=(168, 205, 232, 255))
    d.text((122, 1584), title, font=fb(62), fill=(255, 255, 255, 255))
    d.text((124, 1694), '没有中间商 · 质量保证 · 本地专业老师傅',
           font=fr(26), fill=(210, 228, 240, 235))

    # 进度条
    d.rounded_rectangle((48, 1846, 1032, 1856), radius=5, fill=(255, 255, 255, 60))
    d.rounded_rectangle((48, 1846, int(48 + 984 * idx / 6), 1856), radius=5,
                        fill=(255, 174, 116, 255))
    im.save(path)


def ensure_slides():
    """优先复用已渲染的分镜图；缺失时用无头 Chrome 补渲染。"""
    import tempfile
    need = ['s1', 's2', 's6', 's7', 's9']
    missing = [n for n in need if not os.path.exists(os.path.join(SLIDES, n + '.png'))]
    if not missing:
        return
    os.makedirs(SLIDES, exist_ok=True)
    html = os.path.join(BASE, 'video-slides.html')
    for n in set(missing):
        profile = tempfile.mkdtemp(prefix='jjs-slide-')
        run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars',
             '--no-sandbox', '--user-data-dir=' + profile,
             '--force-device-scale-factor=1', '--window-size=1080,1920',
             '--virtual-time-budget=3000',
             '--screenshot=' + os.path.join(SLIDES, n + '.png'),
             'file://' + html + '?s=' + n[1:]], 'render ' + n)


def render_video_seg(idx, key, title, sub, num, out):
    cap = os.path.join(TMP, 'cap%02d.png' % idx)
    make_caption(cap, title, sub, num)
    src, ss = CLIPS[key]
    vf = ('[0:v]scale=1080:1920:force_original_aspect_ratio=increase,'
          'crop=1080:1920,setsar=1,fps=30,format=yuv420p,'
          'trim=duration=%.3f,setpts=PTS-STARTPTS[bg];'
          '[1:v]format=rgba[cap];[bg][cap]overlay=0:0:format=auto,'
          'format=yuv420p[v]' % SEG)
    args = ['ffmpeg', '-v', 'error', '-y',
            '-ss', str(ss), '-t', str(SEG), '-i', src,
            '-loop', '1', '-framerate', '30', '-t', str(SEG), '-i', cap,
            '-filter_complex', vf, '-map', '[v]'] + ENC + [out]
    run(args, 'seg%02d clip' % idx)


def render_card_seg(idx, name, out, zoom=True):
    src = os.path.join(SLIDES, ('s7' if name == 's7s' else name) + '.png')
    if zoom:
        vf = ('scale=1240:2205:force_original_aspect_ratio=increase,crop=1240:2205,'
              "zoompan=z='min(zoom+0.00032,1.09)':d=1:"
              "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,"
              'setsar=1,format=yuv420p,trim=duration=%.3f,setpts=PTS-STARTPTS' % SEG)
    else:
        vf = ('scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,'
              'setsar=1,fps=30,format=yuv420p,trim=duration=%.3f,setpts=PTS-STARTPTS' % SEG)
    args = ['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-loop', '1',
            '-t', str(SEG), '-i', src, '-vf', vf] + ENC + [out]
    run(args, 'seg%02d card' % idx)


def main():
    from PIL import Image  # noqa: F401
    if not os.path.exists(BGM):
        sys.exit('缺少配乐，请先运行 make_bgm_30.py')
    ensure_slides()
    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)

    paths = []
    for i, (kind, src, title, sub, num) in enumerate(TIMELINE):
        out = os.path.join(TMP, 'seg%02d.mp4' % i)
        if kind == 'clip':
            render_video_seg(i, src, title, sub, num, out)
        else:
            render_card_seg(i, src, out, zoom=(src != 's7s'))
        paths.append(out)
        print('段 %02d/%d 完成  %s' % (i + 1, len(TIMELINE),
              ('现场 ' + str(num) + ' ' + title) if kind == 'clip' else ('卡片 ' + src)))

    listfile = os.path.join(TMP, 'list.txt')
    with open(listfile, 'w') as fh:
        for p in paths:
            fh.write("file '%s'\n" % p)
    joined = os.path.join(TMP, 'joined.mp4')
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0',
         '-i', listfile, '-c', 'copy', joined], 'concat')

    probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                            '-show_entries', 'stream=duration', '-of', 'csv=p=0', joined],
                           capture_output=True, text=True)
    total = float(probe.stdout.strip())
    print('画面总时长', round(total, 2), '秒')

    total = min(total, 30.0)
    run(['ffmpeg', '-v', 'error', '-y', '-i', joined, '-i', BGM,
         '-filter_complex',
         '[0:v]fade=t=in:st=0:d=0.4,fade=t=out:st=29.3:d=0.7,format=yuv420p[v];'
         '[1:a]volume=0.82,atrim=0:%.2f,asetpts=PTS-STARTPTS[a]' % total,
         '-map', '[v]', '-map', '[a]',
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
         '-r', '30', '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
         '-movflags', '+faststart', '-t', '%.2f' % total, OUT], 'final')

    # 从成片第 1.2 秒抽帧做封面，保证封面与视频一致
    cover = os.path.join(BASE, '宣传片封面.jpg')
    run(['ffmpeg', '-v', 'error', '-y', '-ss', '1.2', '-i', OUT,
         '-frames:v', '1', '-q:v', '3', cover], 'cover')
    print('已输出', OUT, round(os.path.getsize(OUT) / 1024 / 1024, 2), 'MB')
    print('封面已同步', cover)


if __name__ == '__main__':
    main()
