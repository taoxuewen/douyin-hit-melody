# 夏夜心跳 (Summer Night Heartbeat)

一首完全由代码合成的抖音风格神曲，约 60 秒。无采样、无 DAW、无外部音源——一个 Python 脚本从正弦波开始合成出整首编曲并直接输出 MP3。

🎵 **直接听**：[`output/xia_ye_xin_tiao.mp3`](output/xia_ye_xin_tiao.mp3)

## 神曲配方（为什么它"洗脑"）

| 要素 | 本曲设定 | 神曲套路依据 |
|---|---|---|
| 和弦走向 | Am–F–C–G 循环（6-4-1-5） | 万能进行，《学猫叫》《少年》等无数爆款同款 |
| 速度 | 120 BPM 四四拍 | 短视频卡点剪辑的舒适区（100–128 BPM） |
| 旋律 | 自然小调、级进为主、音域仅一个八度多 | 人人能跟唱，降低传播门槛 |
| Hook | 副歌动机 4 次重复 + 第三句上行跳进到最高音 | 重复产生记忆点，跳进制造情绪峰值 |
| 结构 | 前奏4 → 主歌8 → 爬升4(军鼓滚奏) → 副歌8 → 尾奏6 小节 | 15 秒内进副歌的短视频友好结构 |
| 编曲 | 副歌四踩底鼓 + 反拍开镲 + 低音八度弹跳 | 抖音 BGM 标配律动 |

## 重新生成 / 魔改

```bash
pip install numpy lameenc
python3 generate_song.py        # 输出 output/xia_ye_xin_tiao.mp3
```

可玩的参数（都在 `generate_song.py` 顶部或乐谱区）：

- `BPM`：改速度（试试 100 变抒情、128 变电音）
- `PADS / BASS / ARPS`：换和弦走向（如 4536：F–G–Em–Am）
- `HOOK_A / HOOK_B`：改副歌旋律，格式为 `(起始拍, MIDI 音高, 时值)`
- `lead() / pluck() / pad_chord()`：改音色

## 技术说明

- 纯 numpy 合成：加法合成锯齿波 lead（三路失谐 + 颤音）、三角波拨弦、正弦 pad/bass、噪声打击乐（底鼓为 160→46Hz 扫频正弦）
- ADSR 包络、等功率声像、Haas 效应加宽、尾部淡出
- `lameenc` 直接编码 192kbps MP3，无需 ffmpeg

## License

代码与音乐均为程序生成，MIT 协议，随意使用（商用、做视频 BGM、二创均可）。
