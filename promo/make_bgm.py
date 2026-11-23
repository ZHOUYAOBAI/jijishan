#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成一段 36 秒的原创器乐配乐（无版权风险）。
写法：纯 Python 合成，正弦波表 + ADSR 包络 + 多抽头延迟做空间感。
调性 D 大调，66 BPM，钢琴/弦垫风格的柔和背景乐，适合门店宣传片。
"""
import math, wave, array, random, os

SR = 44100
DUR = 40.0
N = int(SR * DUR)
random.seed(20261123)

# ---------- 波表 ----------
TB = 4096
SINE = [math.sin(2 * math.pi * i / TB) for i in range(TB)]
TRI = [2 * abs(2 * (i / TB) - 1) - 1 for i in range(TB)]

def wt(table, ph):
    return table[int(ph) & (TB - 1)]

# ---------- 事件渲染 ----------
def add_note(buf, start, dur, freq, amp, table=SINE, harm=0.0, attack=0.02,
             decay=0.6, sustain=0.0, release=0.5, pan=0.0):
    """把一个音符叠加进单声道缓冲（pan 由外部处理）"""
    i0 = int(start * SR)
    n = int((dur + release) * SR)
    if i0 >= N:
        return
    n = min(n, N - i0)
    inc = freq * TB / SR
    inc2 = 2 * inc
    ph = 0.0
    # 包络分段
    a = attack * SR
    d = decay * SR
    r = release * SR
    body = dur * SR
    g = amp
    for k in range(n):
        t = k
        if t < a:
            e = t / a
        elif t < a + d:
            u = (t - a) / d
            e = 1.0 - (1.0 - sustain) * u
        elif t < body:
            e = sustain
        else:
            u = (t - body) / r if r > 0 else 1.0
            e = sustain * max(0.0, 1.0 - u)
        if e <= 0.0:
            continue
        s = wt(SINE, ph)
        if harm:
            s += harm * wt(SINE, ph * 2.0)
        buf[i0 + t] += g * e * s
        ph += inc
        if ph >= TB * 1e6:
            ph -= TB * 1e6

# ---------- 编曲 ----------
BPM = 66.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT

# 和弦（MIDI 音高）：D - A - Bm - G
CH = {
    'D':  [50, 57, 62, 66],
    'A':  [45, 52, 57, 61],
    'Bm': [47, 54, 59, 62],
    'G':  [43, 50, 55, 59],
}
BASS = {'D': 38, 'A': 33, 'Bm': 35, 'G': 31}
PROG = ['D', 'A', 'Bm', 'G', 'D', 'A', 'Bm', 'G', 'D', 'A', 'D']

def hz(m):
    return 440.0 * (2 ** ((m - 69) / 12.0))

pad = array.array('d', [0.0]) * N
bass = array.array('d', [0.0]) * N
pluckL = array.array('d', [0.0]) * N
pluckR = array.array('d', [0.0]) * N

for bi, name in enumerate(PROG):
    t0 = bi * BAR
    if t0 > DUR:
        break
    notes = CH[name]
    # 弦垫：整小节保持
    for j, m in enumerate(notes):
        add_note(pad, t0, BAR * 0.96, hz(m), 0.085 if j else 0.10,
                 harm=0.22, attack=1.1, decay=1.2, sustain=0.72, release=1.6)
    # 低音：第 1、3 拍
    add_note(bass, t0, BEAT * 1.7, hz(BASS[name]), 0.16,
             harm=0.08, attack=0.03, decay=0.5, sustain=0.35, release=0.6)
    add_note(bass, t0 + BEAT * 2, BEAT * 1.6, hz(BASS[name]), 0.11,
             harm=0.06, attack=0.04, decay=0.5, sustain=0.3, release=0.6)
    # 分解和弦（八分音符），左右轻微交替
    if bi >= 2:  # 前两小节留白，进入更自然
        pat = [0, 2, 1, 3, 2, 3, 1, 2]
        for k, idx in enumerate(pat):
            tt = t0 + k * BEAT / 2
            m = notes[idx] + 12
            amp = 0.070 * (0.82 + 0.18 * random.random())
            pan_r = 0.35 if k % 2 == 0 else 0.62
            add_note(pluckL, tt, 0.10, hz(m), amp * (1 - pan_r),
                     harm=0.30, attack=0.004, decay=0.42, sustain=0.0,
                     release=0.55)
            add_note(pluckR, tt, 0.10, hz(m), amp * pan_r,
                     harm=0.30, attack=0.004, decay=0.42, sustain=0.0,
                     release=0.55)

# ---------- 混响（多抽头延迟 + 一阶低通） ----------
def reverb(src, taps=((0.058, 0.30), (0.113, 0.22), (0.191, 0.15), (0.293, 0.10))):
    out = array.array('d', src)
    for dly, g in taps:
        d = int(dly * SR)
        prev = 0.0
        for i in range(d, N):
            s = out[i - d]
            prev += 0.35 * (s - prev)          # 简单低通，避免高频刺耳
            out[i] += g * prev
    return out

pad_r = reverb(pad)
pluckL_r = reverb(pluckL)
pluckR_r = reverb(pluckR)

# ---------- 合并、淡入淡出、限幅 ----------
mix = array.array('d', [0.0]) * N
for i in range(N):
    mix[i] = pad_r[i] + bass[i] * 0.9 + pluckL_r[i] + pluckR_r[i]

fade_in = 1.6 * SR
fade_out = 4.0 * SR
peak = 1e-9
for i in range(N):
    e = 1.0
    if i < fade_in:
        e *= i / fade_in
    if i > N - fade_out:
        e *= max(0.0, (N - i) / fade_out)
    v = math.tanh(mix[i] * 1.25) * e
    mix[i] = v
    if abs(v) > peak:
        peak = abs(v)
gain = 0.86 / peak if peak > 0 else 1.0

outL = array.array('h', [0]) * N
outR = array.array('h', [0]) * N
for i in range(N):
    l = mix[i] * gain
    # 轻微立体声展开
    r = l * 0.99
    outL[i] = int(max(-1.0, min(1.0, l)) * 32767)
    outR[i] = int(max(-1.0, min(1.0, r)) * 32767)

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bgm.wav')
with wave.open(path, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    frames = array.array('h', [0]) * (N * 2)
    for i in range(N):
        frames[2 * i] = outL[i]
        frames[2 * i + 1] = outR[i]
    w.writeframes(frames.tobytes())

print('已生成', path, os.path.getsize(path) // 1024, 'KB', '时长', DUR, '秒')
