#!/usr/bin/env python3
"""Gera todos os arquivos de áudio sintetizados para Head Soccer DesSoft.

Execute na raiz do projeto:
    python generate_sounds.py

Cria:
  assets/sounds/sfx/  -> kick.wav  goal.wav  whistle.wav  jump.wav
                         bounce.wav  powerup.wav  crowd.wav
  assets/sounds/music/ -> menu.wav  gameplay.wav
"""

import os
import wave
import numpy as np

SAMPLE_RATE = 44100
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit PCM


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def save_wav(path: str, samples: np.ndarray) -> None:
    samples = np.clip(samples, -1.0, 1.0)
    pcm = (samples * 32767).astype(np.int16)
    with wave.open(path, "w") as f:
        f.setnchannels(CHANNELS)
        f.setsampwidth(SAMPLE_WIDTH)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(pcm.tobytes())
    print(f"  criado: {path}")


def sine(freq: float, dur: float) -> np.ndarray:
    t = np.linspace(0, dur, int(dur * SAMPLE_RATE), endpoint=False)
    return np.sin(2 * np.pi * freq * t)


def noise(dur: float) -> np.ndarray:
    return np.random.default_rng(42).uniform(-1.0, 1.0, int(dur * SAMPLE_RATE))


def freq_sweep(f0: float, f1: float, dur: float) -> np.ndarray:
    """Sine com varredura linear de frequência de f0 até f1."""
    t = np.linspace(0, dur, int(dur * SAMPLE_RATE), endpoint=False)
    freqs = np.linspace(f0, f1, len(t))
    phase = np.cumsum(2 * np.pi * freqs / SAMPLE_RATE)
    return np.sin(phase)


def exp_env(dur: float, decay: float) -> np.ndarray:
    """Envelope de decaimento exponencial."""
    t = np.linspace(0, dur, int(dur * SAMPLE_RATE), endpoint=False)
    return np.exp(-decay * t)


def adsr(n: int, a: float, d: float, sl: float, s_len: float, r: float) -> np.ndarray:
    """Envelope ADSR em amostras."""
    sr = SAMPLE_RATE
    env = np.zeros(n)
    ai, di, si, ri = int(a * sr), int(d * sr), int(s_len * sr), int(r * sr)
    ai = min(ai, n)
    env[:ai] = np.linspace(0, 1, ai)
    end_d = min(ai + di, n)
    env[ai:end_d] = np.linspace(1, sl, end_d - ai)
    end_s = min(end_d + si, n)
    env[end_d:end_s] = sl
    end_r = min(end_s + ri, n)
    env[end_s:end_r] = np.linspace(sl, 0, end_r - end_s)
    return env


def note_freq(name: str) -> float:
    """Converte nome de nota (ex.: 'C4', 'A#3') para frequência Hz."""
    table = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    semitone = table[name[0]] + (int(name[-1]) - 4) * 12
    return 440.0 * (2 ** ((semitone - 9) / 12))


def play_note(freq: float, dur: float, wave_type: str = "sine",
              volume: float = 0.6) -> np.ndarray:
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n, endpoint=False)
    if wave_type == "sine":
        sig = np.sin(2 * np.pi * freq * t)
    elif wave_type == "triangle":
        sig = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
    elif wave_type == "square":
        sig = np.sign(np.sin(2 * np.pi * freq * t)) * 0.5
    else:
        sig = np.sin(2 * np.pi * freq * t)

    env = adsr(n, 0.005, 0.02, 0.8, max(dur - 0.07, 0), 0.04)
    return sig * env * volume


# ---------------------------------------------------------------------------
# Efeitos sonoros
# ---------------------------------------------------------------------------

def make_kick() -> np.ndarray:
    """Impacto percussivo grave — bola sendo chutada."""
    dur = 0.35
    body = freq_sweep(110, 40, dur) * 0.85
    click_n = int(0.015 * SAMPLE_RATE)
    click = np.random.default_rng(1).uniform(-1, 1, click_n) * 0.5
    buf = np.zeros(int(dur * SAMPLE_RATE))
    buf[:click_n] = click
    mix = body + buf
    return mix * exp_env(dur, 14) * 0.9


def make_goal() -> np.ndarray:
    """Fanfarra ascendente C4–E4–G4–C5 + nota final sustentada."""
    notes = ["C4", "E4", "G4", "C5"]
    segs = []
    for i, n in enumerate(notes):
        f = note_freq(n)
        note_dur = 0.20
        seg = sine(f, note_dur) * 0.6 + sine(f * 2, note_dur) * 0.2
        env = exp_env(note_dur, 3) * np.clip(
            np.linspace(0, 1, int(note_dur * SAMPLE_RATE)) * 50, 0, 1
        )
        segs.append(seg * env)
        segs.append(np.zeros(int(0.02 * SAMPLE_RATE)))

    final_dur = 0.7
    f = note_freq("C5")
    final = sine(f, final_dur) * 0.6 + sine(f * 2, final_dur) * 0.2
    final *= exp_env(final_dur, 2) * np.clip(
        np.linspace(0, 1, int(final_dur * SAMPLE_RATE)) * 50, 0, 1
    )
    segs.append(final)
    return np.concatenate(segs) * 0.8


def make_whistle() -> np.ndarray:
    """Apito de árbitro: tom agudo com vibrato."""
    dur = 1.3
    f = 2200.0
    t = np.linspace(0, dur, int(dur * SAMPLE_RATE), endpoint=False)
    vibrato = 1 + 0.012 * np.sin(2 * np.pi * 7 * t)
    sig = np.sin(2 * np.pi * f * t * vibrato)
    sig += np.sin(2 * np.pi * f * 2 * t) * 0.08

    n = len(sig)
    env = np.ones(n)
    a = int(0.025 * SAMPLE_RATE)
    r = int(0.25 * SAMPLE_RATE)
    env[:a] = np.linspace(0, 1, a)
    env[-r:] = np.linspace(1, 0, r)
    return sig * env * 0.55


def make_jump() -> np.ndarray:
    """Varredura ascendente breve — jogador salta."""
    dur = 0.28
    sig = freq_sweep(180, 480, dur) * 0.6 + noise(dur) * 0.08
    n = len(sig)
    env = exp_env(dur, 9) * np.clip(np.arange(n) / (0.01 * SAMPLE_RATE), 0, 1)
    return sig * env * 0.75


def make_bounce() -> np.ndarray:
    """Quique elástico — bola no chão."""
    dur = 0.28
    body = freq_sweep(280, 70, dur) * 0.75
    n_buf = noise(dur) * 0.25
    mix = body + n_buf
    return mix * exp_env(dur, 12) * 0.85


def make_powerup() -> np.ndarray:
    """Arpejo ascendente brilhante — power-up coletado."""
    notes = ["C5", "E5", "G5", "C6"]
    segs = []
    for n in notes:
        f = note_freq(n)
        d = 0.14
        seg = sine(f, d) * 0.55 + sine(f * 2, d) * 0.25
        seg *= exp_env(d, 9) * np.clip(
            np.linspace(0, 1, int(d * SAMPLE_RATE)) * 80, 0, 1
        )
        segs.append(seg)
    return np.concatenate(segs) * 0.8


def make_crowd() -> np.ndarray:
    """Torcida vibrante — ruído de multidão."""
    dur = 2.5
    n = int(dur * SAMPLE_RATE)
    rng = np.random.default_rng(7)
    raw = rng.standard_normal(n)

    # Low-pass suave via média móvel (simula rumble de multidão)
    window = 60
    filtered = np.convolve(raw, np.ones(window) / window, mode="same")

    # Soma bandas de frequência moduladas para textura
    crowd = filtered * 0.5
    t = np.linspace(0, dur, n, endpoint=False)
    for base in [250, 420, 650, 900]:
        mod = np.sin(2 * np.pi * base * t)
        band = rng.standard_normal(n)
        crowd += band * mod * 0.08

    # Envelope swell + fade out
    env = np.sin(np.pi * t / dur) * 0.75 + 0.25
    env[: int(0.08 * SAMPLE_RATE)] *= np.linspace(0, 1, int(0.08 * SAMPLE_RATE))
    return crowd * env * 0.5


# ---------------------------------------------------------------------------
# Músicas
# ---------------------------------------------------------------------------

def sequence_notes(notes_durs, wave_type="sine", volume=0.55) -> np.ndarray:
    """Renderiza uma sequência [(nota_str, duração_s), ...] em áudio."""
    segs = []
    for name, dur in notes_durs:
        f = note_freq(name)
        segs.append(play_note(f, dur, wave_type, volume))
    return np.concatenate(segs)


def make_menu_music() -> np.ndarray:
    """Melodia calma para o menu principal (~9 s loop)."""
    bpm = 88
    b = 60 / bpm  # duração de um beat

    melody = [
        ("E4", b), ("G4", b), ("A4", b), ("G4", b * 2),
        ("E4", b), ("D4", b), ("C4", b * 2),
        ("D4", b), ("E4", b), ("G4", b), ("A4", b * 2),
        ("G4", b), ("E4", b), ("C4", b * 2),
        ("A4", b), ("G4", b), ("E4", b), ("D4", b * 2),
        ("C4", b * 2), ("E4", b), ("G4", b),
    ]

    bass = [
        ("C3", b * 4), ("G2", b * 4),
        ("F2", b * 4), ("G2", b * 4),
        ("A2", b * 4), ("F2", b * 4),
        ("C3", b * 4),
    ]
    bass = bass * 2

    mel_arr = sequence_notes(melody, "sine", 0.55)
    bas_arr = sequence_notes(bass, "sine", 0.30)

    n = min(len(mel_arr), len(bas_arr))
    return np.clip(mel_arr[:n] + bas_arr[:n], -1, 1) * 0.75


def make_gameplay_music() -> np.ndarray:
    """Música animada para a partida (~10 s loop)."""
    bpm = 138
    b = 60 / bpm

    melody = [
        ("C5", b), ("E5", b * 0.5), ("G5", b * 0.5), ("A5", b),
        ("G5", b), ("E5", b), ("C5", b * 2),
        ("D5", b), ("F5", b * 0.5), ("A5", b * 0.5), ("G5", b),
        ("F5", b), ("D5", b), ("C5", b * 2),
        ("E5", b), ("G5", b), ("B5", b), ("G5", b),
        ("E5", b * 2), ("C5", b * 2),
        ("A4", b), ("C5", b), ("E5", b), ("D5", b),
        ("C5", b * 2), ("G4", b), ("A4", b),
        ("C5", b * 3), ("C5", b),
    ]

    bass = [
        ("C3", b * 2), ("G3", b * 2),
        ("F3", b * 2), ("G3", b * 2),
        ("A3", b * 2), ("E3", b * 2),
        ("F3", b * 2), ("G3", b * 2),
    ]
    bass = bass * 4

    chords = [
        ("E4", b), ("G4", b),
        ("F4", b), ("A4", b),
        ("G4", b), ("B4", b),
        ("F4", b), ("A4", b),
    ]
    chords = chords * 8

    mel_arr = sequence_notes(melody, "triangle", 0.50)
    bas_arr = sequence_notes(bass, "sine", 0.32)
    cho_arr = sequence_notes(chords, "square", 0.12)

    n = min(len(mel_arr), len(bas_arr), len(cho_arr))
    return np.clip(mel_arr[:n] + bas_arr[:n] + cho_arr[:n], -1, 1) * 0.75


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    sfx_dir = os.path.join("assets", "sounds", "sfx")
    music_dir = os.path.join("assets", "sounds", "music")
    os.makedirs(sfx_dir, exist_ok=True)
    os.makedirs(music_dir, exist_ok=True)

    print("=== Gerando efeitos sonoros ===")
    save_wav(os.path.join(sfx_dir, "kick.wav"),    make_kick())
    save_wav(os.path.join(sfx_dir, "goal.wav"),    make_goal())
    save_wav(os.path.join(sfx_dir, "whistle.wav"), make_whistle())
    save_wav(os.path.join(sfx_dir, "jump.wav"),    make_jump())
    save_wav(os.path.join(sfx_dir, "bounce.wav"),  make_bounce())
    save_wav(os.path.join(sfx_dir, "powerup.wav"), make_powerup())
    save_wav(os.path.join(sfx_dir, "crowd.wav"),   make_crowd())

    print("\n=== Gerando músicas ===")
    save_wav(os.path.join(music_dir, "menu.wav"),     make_menu_music())
    save_wav(os.path.join(music_dir, "gameplay.wav"), make_gameplay_music())

    print("\nConcluído. Todos os arquivos de áudio gerados.")


if __name__ == "__main__":
    main()
