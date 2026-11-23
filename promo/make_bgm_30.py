#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
30 秒宣传片配乐（原创，无版权风险）。
D 大调，96 BPM —— 每小节恰好 2.5 秒，画面 12 个段落全部踩在小节线上。
在原有钢琴/弦垫风格上加轻鼓点（kick / snare / hi-hat），比 40 秒版更精神，
但仍是背景乐，不抢画面。输出 promo/bgm-30.wav
"""
import math, wave, array, random, os

SR = 44100
DUR = 30.5
N = int(SR * DUR)
random.seed(20261124)

TB = 4096
SINE = [math.sin(2 * math.pi * i / TB) for i in range(TB)]


def wt(table, ph):
    return table[int(ph) & (TB - 1)]


def add_note(buf, start, dur, freq, amp, harm=0.0, attack=0.02, decay=0.6,
             sustain=0.0, release=0.5):
    i0 = int(start * SR)
    n = min(int((dur + release) * SR), N - i0)
    if i0 >= N or n <= 0:
        return
    inc = freq * TB / SR
    a, d, r, body = attack * SR, decay * SR, release * SR, dur * SR
    ph = 0.0
    for k in range(n):
        if k < a:
            e = k / a
        elif k < a + d:
            e = 1.0 - (1.0 - sustain) * (k - a) / d
        elif k < body:
            e = sustain
        else:
            u = (k - body) / r if r > 0 else 1.0
            e = sustain * max(0.0, 1.0 - u)
        if e <= 0:
            ph += inc
            continue
        s = wt(SINE, ph) + harm * wt(SINE, ph * 2.0)
        buf[i0 + k] += amp * e * s
        ph += inc


BPM = 96.0
BEAT = 60.0 / BPM          # 0.625 s
BAR = 4 * BEAT             # 2.5 s —— 与画面段落等长
CH = {
    'D':  [50, 57, 62, 66],
    'A':  [45, 52, 57, 61],
    'Bm': [47, 54, 59, 62],
    'G':  [43, 50, 55, 59],
}
BASS = {'D': 38, 'A': 33, 'Bm': 35, 'G': 31}
PROG = ['D', 'A', 'Bm', 'G'] * 3


def hz(m):
    return 440.0 * (2 ** ((m - 69) / 12.0))


pad = array.array('d', [0.0]) * N
bass = array.array('d', [0.0]) * N
pluckL = array.array('d', [0.0]) * N
pluckR = array.array('d', [0.0]) * N
drums = array.array('d', [0.0]) * N

for bi, name in enumerate(PROG):
    t0 = bi * BAR
    if t0 > DUR:
        break
    notes = CH[name]
    for j, m in enumerate(notes):
        add_note(pad, t0, BAR * 0.96, hz(m), 0.085 if j else 0.10,
                 harm=0.22, attack=0.85, decay=1.0, sustain=0.72, release=1.4)
    add_note(bass, t0, BEAT * 1.7, hz(BASS[name]), 0.16,
             harm=0.08, attack=0.03, decay=0.5, sustain=0.35, release=0.6)
    add_note(bass, t0 + BEAT * 2, BEAT * 1.6, hz(BASS[name]), 0.11,
             harm=0.06, attack=0.04, decay=0.5, sustain=0.3, release=0.6)
    if bi >= 1:
        pat = [0, 2, 1, 3, 2, 3, 1, 2]
        for k, idx in enumerate(pat):
            tt = t0 + k * BEAT / 2
            m = notes[idx] + 12
            amp = 0.068 * (0.82 + 0.18 * random.random())
            pan_r = 0.35 if k % 2 == 0 else 0.62
            add_note(pluckL, tt, 0.10, hz(m), amp * (1 - pan_r),
                     harm=0.30, attack=0.004, decay=0.40, sustain=0.0, release=0.5)
            add_note(pluckR, tt, 0.10, hz(m), amp * pan_r,
                     harm=0.30, attack=0.004, decay=0.40, sustain=0.0, release=0.5)

    # ---- 轻鼓点：bi>=1 进鼓，前 1 小节纯铺底 ----
    if bi >= 1:
        gain = 0.55 if bi == 1 else (0.85 if bi < 10 else 0.55)
        for beat in (0, 2):  # kick 在 1、3 拍
            st = t0 + beat * BEAT
            i0, n = int(st * SR), int(0.20 * SR)
            ph = 0.0
            for k in range(n):
                u = k / n
                f = 48.0 + 95.0 * math.exp(-u * 18.0)
                ph += f * TB / SR
                drums[i0 + k] += 0.30 * gain * math.exp(-u * 11.0) * wt(SINE, ph)
        for beat in (1, 3):  # snare 在 2、4 拍
            st = t0 + beat * BEAT
            i0, n = int(st * SR), int(0.13 * SR)
            prev = 0.0
            for k in range(n):
                u = k / n
                white = random.uniform(-1, 1)
                hp = white - prev
                prev = white
                drums[i0 + k] += 0.10 * gain * hp * math.exp(-u * 16.0)
        for k in range(8):  # hi-hat 八分
            st = t0 + k * BEAT / 2
            i0, n = int(st * SR), int(0.045 * SR)
            prev = 0.0
            amp = 0.035 * gain * (1.0 if k % 2 == 0 else 0.6)
            for j in range(n):
                u = j / n
                white = random.uniform(-1, 1)
                hp = white - prev
                prev = white
                drums[i0 + j] += amp * hp * math.exp(-u * 22.0)


def reverb(src, taps=((0.058, 0.28), (0.113, 0.20), (0.191, 0.13), (0.293, 0.09))):
    out = array.array('d', src)
    for dly, g in taps:
        d = int(dly * SR)
        prev = 0.0
        for i in range(d, N):
            prev += 0.35 * (out[i - d] - prev)
            out[i] += g * prev
    return out


pad_r = reverb(pad)
plL_r = reverb(pluckL)
plR_r = reverb(pluckR)

mix = array.array('d', [0.0]) * N
for i in range(N):
    mix[i] = pad_r[i] + bass[i] * 0.9 + plL_r[i] + plR_r[i] + drums[i]

fade_in, fade_out = 1.0 * SR, 3.2 * SR
peak = 1e-9
for i in range(N):
    e = 1.0
    if i < fade_in:
        e *= i / fade_in
    if i > N - fade_out:
        e *= max(0.0, (N - i) / fade_out)
    v = math.tanh(mix[i] * 1.22) * e
    mix[i] = v
    peak = max(peak, abs(v))
gain = 0.86 / peak if peak > 0 else 1.0

frames = array.array('h', [0]) * (N * 2)
for i in range(N):
    l = mix[i] * gain
    r = l * 0.99
    frames[2 * i] = int(max(-1.0, min(1.0, l)) * 32767)
    frames[2 * i + 1] = int(max(-1.0, min(1.0, r)) * 32767)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bgm-30.wav')
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(frames.tobytes())
print('已生成', out, os.path.getsize(out) // 1024, 'KB', DUR, '秒', 'BPM', BPM, '每小节', BAR, '秒')
