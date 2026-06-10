#!/usr/bin/env python3
"""《夏夜心跳》— 程序化合成的抖音风格神曲（约 60 秒）。

神曲配方：
- 和弦走向：Am - F - C - G（万能 6-4-1-5，无数爆款同款）
- 速度：120 BPM，四四拍，副歌四踩底鼓 + 反拍镲
- 旋律：自然小调、级进为主、副歌 hook 动机重复 4 次（洗脑点）
- 结构：前奏(4小节) → 主歌(8) → 预副歌爬升(4) → 副歌(8) → 尾奏(6)

用法: python3 generate_song.py   # 输出 output/xia_ye_xin_tiao.mp3
依赖: numpy, lameenc
"""
import os

import numpy as np

SR = 44100
BPM = 120
BEAT = 60.0 / BPM            # 0.5 秒
BAR = 4 * BEAT               # 2 秒
TOTAL_BARS = 30              # 60 秒
TAIL = 2.0                   # 混响尾巴余量

rng = np.random.default_rng(42)
master = np.zeros((int((TOTAL_BARS * BAR + TAIL) * SR), 2))


def freq(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def adsr(n, a=0.01, d=0.08, s=0.75, r=0.08):
    a_n, d_n, r_n = (max(1, int(x * SR)) for x in (a, d, r))
    s_n = max(1, n - a_n - d_n - r_n)
    env = np.concatenate([
        np.linspace(0, 1, a_n),
        np.linspace(1, s, d_n),
        np.full(s_n, s),
        np.linspace(s, 0, r_n),
    ])
    return env[:n] if len(env) >= n else np.pad(env, (0, n - len(env)))


def add(start_sec, sig, gain=1.0, pan=0.0):
    """pan ∈ [-1, 1]，等功率声像。"""
    i = int(start_sec * SR)
    j = min(i + len(sig), len(master))
    seg = sig[: j - i]
    theta = (pan + 1) * np.pi / 4
    master[i:j, 0] += seg * gain * np.cos(theta)
    master[i:j, 1] += seg * gain * np.sin(theta)


# ---------------- 音色 ----------------

def saw_additive(phase, f0, brightness=12000):
    """加法合成锯齿波（按相位驱动），限制谐波数避免混叠。"""
    out = np.zeros_like(phase)
    for k in range(1, min(24, int(brightness / f0)) + 1):
        out += np.sin(k * phase) / k
    return out


def lead(midi, dur):
    """超级锯齿 lead：三路微失谐 + 颤音。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f0 = freq(midi)
    f = f0 * (1 + 0.003 * np.sin(2 * np.pi * 5.5 * t))
    phase = 2 * np.pi * np.cumsum(f) / SR
    sig = sum(saw_additive(phase * d, f0) for d in (0.996, 1.0, 1.004)) / 3
    return sig * adsr(n, 0.012, 0.1, 0.72, 0.1)


def pluck(midi, dur):
    """快衰减三角波，做琶音音色。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = freq(midi)
    tri = 2 / np.pi * np.arcsin(np.sin(2 * np.pi * f * t))
    return tri * np.exp(-t * 7) * adsr(n, 0.004, 0.05, 0.8, 0.05)


def pad_chord(midis, dur):
    """柔和铺底和弦。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = np.zeros(n)
    for m in midis:
        f = freq(m)
        sig += np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t)
    return sig / len(midis) * adsr(n, 0.35, 0.2, 0.8, 0.5)


def bass(midi, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = freq(midi)
    sig = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t)
    return sig * adsr(n, 0.006, 0.05, 0.85, 0.06)


def kick():
    t = np.arange(int(0.28 * SR)) / SR
    f = 160 * np.exp(-t * 28) + 46
    phase = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(phase) * np.exp(-t * 16)
    click = rng.standard_normal(len(t)) * np.exp(-t * 220) * 0.25
    return body + click


def clap():
    t = np.arange(int(0.18 * SR)) / SR
    noise = np.diff(rng.standard_normal(len(t) + 1))  # 简易高通
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 32) * 0.4
    return noise * np.exp(-t * 24) + body


def hat(open_=False):
    dur = 0.16 if open_ else 0.05
    t = np.arange(int(dur * SR)) / SR
    noise = np.diff(rng.standard_normal(len(t) + 1))
    return noise * np.exp(-t * (28 if open_ else 75))


# ---------------- 乐谱 ----------------
# 和弦（每小节循环 Am F C G）
PADS = [(57, 60, 64), (53, 57, 60), (55, 60, 64), (55, 59, 62)]
BASS = [45, 41, 48, 43]
ARPS = [(69, 72, 76, 81), (65, 69, 72, 77), (67, 72, 76, 79), (67, 71, 74, 79)]

# 旋律：(起始拍, MIDI 音高, 时值/拍)。一个乐句 = 4 小节 = 16 拍
VERSE_A = [(0, 69, 1), (1, 72, .5), (1.5, 72, .5), (2, 74, 1), (3, 72, 1),
           (4, 69, 1), (5, 69, .5), (5.5, 67, .5), (6, 69, 2),
           (8, 67, 1), (9, 72, .5), (9.5, 72, .5), (10, 74, 1), (11, 76, 1),
           (12, 74, .5), (12.5, 72, .5), (13, 71, 1), (14, 67, 2)]
VERSE_B = VERSE_A[:-4] + [(12, 74, .5), (12.5, 76, .5), (13, 72, 1), (14, 69, 2)]

PRE = [(0, 69, .5), (.5, 71, .5), (1, 72, .5), (1.5, 74, .5), (2, 76, 2),
       (4, 72, .5), (4.5, 74, .5), (5, 76, .5), (5.5, 77, .5), (6, 76, 2),
       (8, 76, .5), (8.5, 77, .5), (9, 79, .5), (9.5, 77, .5), (10, 76, 1), (11, 74, 1),
       (12, 74, 1), (13, 76, 1), (14, 79, 2)]

HOOK_A = [(0, 76, 1), (1, 76, .5), (1.5, 76, .5), (2, 74, 1), (3, 72, 1),
          (4, 72, .5), (4.5, 74, .5), (5, 72, 1), (6, 69, 2),
          (8, 76, 1), (9, 76, .5), (9.5, 76, .5), (10, 79, 1), (11, 76, 1),
          (12, 74, .5), (12.5, 76, .5), (13, 74, 1), (14, 71, 2)]
HOOK_B = HOOK_A[:-4] + [(12, 74, .5), (12.5, 72, .5), (13, 71, 1), (14, 69, 2)]


def melody(notes, start_bar, gain=0.5, octave_double=False):
    base = start_bar * BAR
    for beat, midi, dur in notes:
        t0 = base + beat * BEAT
        add(t0, lead(midi, dur * BEAT), gain)
        if octave_double:
            add(t0, lead(midi + 12, dur * BEAT), gain * 0.3)


def pads(start_bar, n_bars, gain=0.16):
    for b in range(n_bars):
        chord = PADS[(start_bar + b) % 4]
        t0 = (start_bar + b) * BAR
        add(t0, pad_chord(chord, BAR * 1.05), gain, pan=-0.3)
        add(t0 + 0.012, pad_chord(chord, BAR * 1.05), gain, pan=0.3)  # Haas 加宽


def arps(start_bar, n_bars, gain=0.22):
    for b in range(n_bars):
        tones = ARPS[(start_bar + b) % 4]
        pattern = [tones[0], tones[1], tones[2], tones[3], tones[2], tones[1], tones[2], tones[1]]
        for i, m in enumerate(pattern):
            add((start_bar + b) * BAR + i * BEAT / 2, pluck(m, BEAT * 0.9), gain,
                pan=0.4 if i % 2 else -0.4)


def bassline(start_bar, n_bars, gain=0.4, octave_bounce=False):
    for b in range(n_bars):
        root = BASS[(start_bar + b) % 4]
        for i in range(8):  # 八分音符
            m = root + 12 if (octave_bounce and i % 2) else root
            g = gain if i % 2 == 0 else gain * 0.7
            add((start_bar + b) * BAR + i * BEAT / 2, bass(m, BEAT * 0.45), g)


def drums(start_bar, n_bars, four_floor=True, with_clap=True, hats=True):
    for b in range(n_bars):
        t0 = (start_bar + b) * BAR
        for beat in range(4):
            if four_floor or beat in (0, 2):
                add(t0 + beat * BEAT, kick(), 0.85)
            if with_clap and beat in (1, 3):
                add(t0 + beat * BEAT, clap(), 0.4)
            if hats:
                add(t0 + beat * BEAT + BEAT / 2, hat(open_=four_floor), 0.22)
                if four_floor:
                    add(t0 + beat * BEAT, hat(), 0.1)


def snare_roll(start_bar):
    """预副歌最后一小节的 16 分军鼓滚奏，渐强。"""
    t0 = start_bar * BAR
    for i in range(16):
        add(t0 + i * BEAT / 4, clap(), 0.08 + 0.025 * i)


# ---------------- 编曲时间线（30 小节 = 60 秒） ----------------
arps(0, 4); pads(0, 4)                                   # 前奏
drums(2, 2, four_floor=False, with_clap=False)

melody(VERSE_A, 4, gain=0.42); melody(VERSE_B, 8, gain=0.42)   # 主歌 8 小节
pads(4, 8); bassline(4, 8, gain=0.34)
drums(4, 8, four_floor=False, with_clap=True)

melody(PRE, 12, gain=0.48)                               # 预副歌爬升 4 小节
pads(12, 4, gain=0.2); arps(12, 4); bassline(12, 4)
drums(12, 3, four_floor=False); snare_roll(15)

melody(HOOK_A, 16, gain=0.55, octave_double=True)        # 副歌 8 小节（hook）
melody(HOOK_B, 20, gain=0.55, octave_double=True)
pads(16, 8, gain=0.22); arps(16, 8, gain=0.18)
bassline(16, 8, gain=0.42, octave_bounce=True)
drums(16, 8, four_floor=True)

melody(HOOK_B, 24, gain=0.4)                             # 尾奏：hook 再现 + 收尾
pads(24, 6, gain=0.18); arps(24, 6, gain=0.2)
bassline(24, 4, gain=0.3)
drums(24, 4, four_floor=False, with_clap=True)
add(28 * BAR, lead(69, BAR * 2 * 0.9), 0.35)             # 长音收在主音 A

# ---------------- 缩混 & 导出 ----------------
peak = np.max(np.abs(master))
master = master / peak * 0.9
fade = int(2.5 * SR)
master[-fade:] *= np.linspace(1, 0, fade)[:, None]

pcm = (master * 32767).astype(np.int16)

import lameenc  # noqa: E402

enc = lameenc.Encoder()
enc.set_bit_rate(192)
enc.set_in_sample_rate(SR)
enc.set_channels(2)
enc.set_quality(2)
mp3 = enc.encode(pcm.tobytes()) + enc.flush()

os.makedirs("output", exist_ok=True)
out = os.path.join("output", "xia_ye_xin_tiao.mp3")
with open(out, "wb") as f:
    f.write(mp3)
print(f"已生成 {out}（{len(master)/SR:.1f} 秒, {len(mp3)/1024:.0f} KB）")
