#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合成 1080x1920 竖版宣传片：逐段渲染 → concat 拼接 → 混入配乐。"""
import subprocess, os, sys, shutil, wave

BASE = os.path.dirname(os.path.abspath(__file__))
TMP = '/tmp/vseg'
CLIP = '/Users/mac/Desktop/大舅/0d9bfd2f05b00c9aca4459977c730f5a.mp4'
CLIP_SS, CLIP_T = 5.0, 9.0
BGM = os.path.join(BASE, 'bgm.wav')
OUT = os.path.join(BASE, '宣传片.mp4')

segments = [
    ('/tmp/slides/s1.png', 4.0, True),   # 开场
    ('/tmp/slides/s2.png', 4.0, False),  # 四项服务
    ('/tmp/slides/s3.png', 3.5, True),   # 没有中间商
    ('/tmp/slides/s4.png', 3.5, True),   # 质量保证
    ('/tmp/slides/s5.png', 3.5, True),   # 本地老师傅
    ('/tmp/slides/s8.png', 2.5, False),  # 真实现场
    ('CLIP',              9.0, False),   # 实拍片段
    ('/tmp/slides/s6.png', 4.0, True),   # 完工实拍
    ('/tmp/slides/s7.png', 5.5, False),  # 联系方式
]

if os.path.isdir(TMP):
    shutil.rmtree(TMP)
os.makedirs(TMP)

ENC = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
       '-r', '30', '-an', '-movflags', '+faststart']

def run(args, label):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print(f'[{label}] 失败')
        print(r.stderr[-2000:])
        sys.exit(1)

paths = []
for idx, (src, dur, zoom) in enumerate(segments):
    out = os.path.join(TMP, f'seg{idx:02d}.mp4')
    if src == 'CLIP':
        vf = (f'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,'
              f'setsar=1,fps=30,format=yuv420p,trim=duration={dur},setpts=PTS-STARTPTS')
        args = ['ffmpeg', '-v', 'error', '-y', '-ss', str(CLIP_SS), '-t', str(CLIP_T),
                '-i', CLIP, '-vf', vf] + ENC + [out]
    elif zoom:
        vf = (f'scale=1240:2205:force_original_aspect_ratio=increase,crop=1240:2205,'
              f"zoompan=z='min(zoom+0.00032,1.09)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
              f's=1080x1920:fps=30,setsar=1,format=yuv420p,'
              f'trim=duration={dur},setpts=PTS-STARTPTS')
        args = ['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-loop', '1', '-t', str(dur),
                '-i', src, '-vf', vf] + ENC + [out]
    else:
        vf = (f'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,'
              f'setsar=1,fps=30,format=yuv420p,trim=duration={dur},setpts=PTS-STARTPTS')
        args = ['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-loop', '1', '-t', str(dur),
                '-i', src, '-vf', vf] + ENC + [out]
    run(args, f'seg{idx:02d}')
    paths.append(out)

# 拼接
listfile = os.path.join(TMP, 'list.txt')
with open(listfile, 'w') as fh:
    for p in paths:
        fh.write(f"file '{p}'\n")
joined = os.path.join(TMP, 'joined.mp4')
run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', listfile,
     '-c', 'copy', joined], 'concat')

# 时长核对
probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                        '-show_entries', 'stream=duration', '-of', 'csv=p=0', joined],
                       capture_output=True, text=True)
total = float(probe.stdout.strip())
print('画面总时长', round(total, 2), '秒')

# 收尾：首尾淡入淡出 + 混入配乐
fade_out_st = max(0.0, total - 1.2)
run(['ffmpeg', '-v', 'error', '-y', '-i', joined, '-i', BGM,
     '-filter_complex',
     f'[0:v]fade=t=in:st=0:d=0.8,fade=t=out:st={fade_out_st:.2f}:d=1.2,format=yuv420p[v];'
     f'[1:a]volume=0.72,afade=t=in:st=0:d=1.2,afade=t=out:st={max(0,total-4.5):.2f}:d=4.5,'
     f'atrim=0:{total:.2f},asetpts=PTS-STARTPTS[a]',
     '-map', '[v]', '-map', '[a]',
     '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', '30',
     '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
     '-movflags', '+faststart', '-t', f'{total:.2f}', OUT], 'final')

print('已输出', OUT, round(os.path.getsize(OUT) / 1024 / 1024, 2), 'MB')
