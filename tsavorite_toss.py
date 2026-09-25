#!/usr/bin/env python3
"""Tsavorite Toss — neon gravity-basketball arcade for ElbowOS."""
from __future__ import annotations

import math
import os
import random
import subprocess
import sys

import pygame

W, H = 1080, 1920
FPS = 30
TITLE = "TSAVORITE TOSS"
HANDLE = "x.com/ElbowOS"
BG = (6, 18, 12)
PINE = (10, 42, 28)
INK = (230, 255, 236)
LIME = (80, 255, 120)
LEAF = (20, 170, 70)
GOLD = (255, 214, 70)
TEAL = (40, 230, 210)
AMBER = (255, 160, 40)
IVORY = (245, 255, 240)


class Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "col", "r")

    def __init__(self, x, y, vx, vy, life, col, r=5):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life, self.col, self.r = life, col, r


class Game:
    def __init__(self, record: bool):
        self.record = record
        self.surf = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.Font(None, 68)
        self.font_md = pygame.font.Font(None, 46)
        self.font_sm = pygame.font.Font(None, 32)
        self.reset()

    def reset(self) -> None:
        self.score = getattr(self, "score", 0) if getattr(self, "keep_score", False) else 0
        self.keep_score = True
        self.combo = 0
        self.t = 0.0
        self.pulse = 0.0
        self.flash = 0.0
        self.hx = W * 0.5
        self.hy = 430.0
        self.hvx = 220.0
        self.px = W * 0.5
        self.py = H - 260.0
        self.angle = 0.0
        self.power = 0.0
        self.charging = False
        self.ball = None
        self.sparks: list[Spark] = []
        self.leaves = [
            [random.uniform(0, W), random.uniform(0, H), random.uniform(10, 28),
             random.choice((PINE, (8, 50, 30), (16, 70, 40)))]
            for _ in range(22)
        ]
        self.net_wiggle = 0.0
        self.shots = 0
        self.aim_cool = 0.0

    def burst(self, x, y, col, n=16) -> None:
        for _ in range(n):
            a = random.random() * 6.283
            spd = random.uniform(90, 520)
            self.sparks.append(Spark(x, y, spd * math.cos(a), spd * math.sin(a),
                                     random.uniform(0.2, 0.6), col, random.randint(3, 9)))

    def launch(self, ang: float, pwr: float) -> None:
        pwr = max(420.0, min(1380.0, pwr))
        self.ball = {
            "x": self.px, "y": self.py - 36,
            "vx": math.sin(ang) * pwr,
            "vy": -math.cos(ang) * pwr,
            "r": 22.0, "scored": False, "age": 0.0,
        }
        self.charging = False
        self.power = 0.0
        self.shots += 1

    def autoplay(self, dt: float) -> None:
        self.aim_cool -= dt
        if self.ball is not None:
            return
        lead = self.hx + self.hvx * 0.55
        lead = max(180, min(W - 180, lead))
        dx = lead - self.px
        dy = self.py - 36 - self.hy
        want = math.atan2(dx, max(80.0, dy))
        self.angle += (want - self.angle) * min(1.0, 8.0 * dt)
        if self.aim_cool > 0:
            return
        dist = math.hypot(dx, dy)
        pwr = 620 + dist * 0.62 + abs(self.hvx) * 0.35
        pwr += random.uniform(-40, 50)
        self.launch(self.angle, pwr)
        self.aim_cool = 0.12

    def update(self, dt: float) -> None:
        self.pulse += dt
        self.t += dt
        self.flash = max(0.0, self.flash - dt)
        self.net_wiggle = max(0.0, self.net_wiggle - dt * 3.2)
        self.hx += self.hvx * dt
        if self.hx < 210 or self.hx > W - 210:
            self.hvx *= -1
            self.hx = max(210, min(W - 210, self.hx))
        self.hvx += math.sin(self.t * 0.7) * 18 * dt
        self.hvx = max(-340, min(340, self.hvx))

        for lf in self.leaves:
            lf[1] += (28 + lf[2]) * dt
            lf[0] += math.sin(self.t + lf[2]) * 18 * dt
            if lf[1] > H + 20:
                lf[0], lf[1] = random.uniform(0, W), -24

        if self.record:
            self.autoplay(dt)
        else:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.angle -= 2.1 * dt
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.angle += 2.1 * dt
            self.angle = max(-1.15, min(1.15, self.angle))
            if keys[pygame.K_SPACE] or keys[pygame.K_w]:
                if self.ball is None:
                    self.charging = True
                    self.power = min(1380.0, self.power + 980 * dt)
            elif self.charging and self.ball is None:
                self.launch(self.angle, max(480.0, self.power))

        b = self.ball
        if b:
            b["age"] += dt
            b["vy"] += 1680.0 * dt
            b["x"] += b["vx"] * dt
            b["y"] += b["vy"] * dt
            if b["x"] < 70 or b["x"] > W - 70:
                b["vx"] *= -0.86
                b["x"] = max(70, min(W - 70, b["x"]))
                self.burst(b["x"], b["y"], TEAL, 6)
            if b["y"] > H - 90:
                if not b["scored"]:
                    self.combo = 0
                self.ball = None
            rim_l, rim_r = self.hx - 78, self.hx + 78
            if (not b["scored"]) and b["vy"] > 40 and abs(b["y"] - self.hy) < 28:
                if rim_l + 10 < b["x"] < rim_r - 10:
                    b["scored"] = True
                    self.combo += 1
                    self.score += 10 + self.combo * 4
                    self.flash = 0.22
                    self.net_wiggle = 1.0
                    self.burst(self.hx, self.hy + 30, GOLD, 22)
                    self.burst(b["x"], b["y"], LIME, 10)
                    b["vx"] *= 0.35
                    b["vy"] *= 0.25
                elif rim_l - 26 < b["x"] < rim_r + 26:
                    b["vy"] = -abs(b["vy"]) * 0.55
                    b["vx"] += (b["x"] - self.hx) * 2.4
                    self.burst(b["x"], b["y"], AMBER, 8)
            if b["age"] > 4.2:
                self.ball = None

        alive = []
        for sp in self.sparks:
            sp.life -= dt
            if sp.life <= 0:
                continue
            sp.x += sp.vx * dt
            sp.y += sp.vy * dt
            sp.vy += 420 * dt
            alive.append(sp)
        self.sparks = alive

    def handle(self, ev) -> None:
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
            self.keep_score = False
            self.reset()

    def draw_hoop(self, s: pygame.Surface) -> None:
        hx, hy = int(self.hx), int(self.hy)
        pygame.draw.rect(s, (30, 90, 50), (hx - 8, hy - 110, 16, 110))
        pygame.draw.rect(s, GOLD, (hx - 8, hy - 110, 16, 110), 2)
        pygame.draw.rect(s, IVORY, (hx - 118, hy - 128, 40, 90), border_radius=6)
        pygame.draw.rect(s, TEAL, (hx - 118, hy - 128, 40, 90), 3, border_radius=6)
        pygame.draw.ellipse(s, LIME, (hx - 86, hy - 16, 172, 28), 8)
        pygame.draw.ellipse(s, GOLD, (hx - 86, hy - 16, 172, 28), 3)
        wig = int(10 * math.sin(self.pulse * 18) * self.net_wiggle)
        for i in range(7):
            x = hx - 70 + i * 23
            pygame.draw.line(s, TEAL, (x, hy + 6), (x + wig, hy + 78), 2)
        for j in range(4):
            y = hy + 18 + j * 16
            pygame.draw.line(s, (30, 160, 140), (hx - 72, y), (hx + 72, y + wig // 2), 1)

    def draw(self, s: pygame.Surface) -> None:
        s.fill(BG)
        for i in range(14):
            y = int((self.pulse * 40 + i * 150) % (H + 30)) - 16
            pygame.draw.line(s, (12, 36, 24), (0, y), (W, y), 2)
        for x, y, r, col in self.leaves:
            pygame.draw.circle(s, col, (int(x), int(y)), int(r))

        pygame.draw.rect(s, PINE, (40, 200, W - 80, H - 280), border_radius=36)
        pygame.draw.rect(s, LIME, (40, 200, W - 80, H - 280), 4, border_radius=36)
        pygame.draw.line(s, (40, 110, 70), (70, H - 320), (W - 70, H - 320), 3)
        pygame.draw.circle(s, (30, 90, 55), (W // 2, H - 320), 90, 3)

        self.draw_hoop(s)

        px, py = int(self.px), int(self.py)
        pygame.draw.rect(s, LEAF, (px - 46, py - 18, 92, 44), border_radius=16)
        pygame.draw.rect(s, GOLD, (px - 46, py - 18, 92, 44), 3, border_radius=16)
        ax = px + int(math.sin(self.angle) * 86)
        ay = py - int(math.cos(self.angle) * 86)
        pygame.draw.line(s, IVORY, (px, py - 8), (ax, ay), 8)
        pygame.draw.circle(s, LIME, (ax, ay), 10)

        if self.charging:
            bar_w = int(220 * (self.power / 1380.0))
            pygame.draw.rect(s, (20, 40, 28), (px - 110, py + 40, 220, 16), border_radius=8)
            pygame.draw.rect(s, GOLD, (px - 110, py + 40, bar_w, 16), border_radius=8)

        if self.ball:
            bx, by = int(self.ball["x"]), int(self.ball["y"])
            pygame.draw.circle(s, (40, 90, 50), (bx + 4, by + 6), 22)
            pygame.draw.circle(s, LIME, (bx, by), 22)
            pygame.draw.circle(s, IVORY, (bx, by), 22, 2)
            pygame.draw.arc(s, LEAF, (bx - 16, by - 16, 32, 32), 0.4, 3.4, 2)
            pygame.draw.circle(s, IVORY, (bx - 6, by - 7), 5)

        for sp in self.sparks:
            pygame.draw.circle(s, sp.col, (int(sp.x), int(sp.y)), max(1, int(sp.r * sp.life * 2)))

        title = self.font_lg.render(TITLE, True, LIME)
        s.blit(title, title.get_rect(center=(W // 2, 62)))
        handle = self.font_sm.render(HANDLE, True, TEAL)
        s.blit(handle, handle.get_rect(center=(W // 2, 112)))
        score = self.font_md.render(f"SCORE  {self.score}    STREAK  {self.combo}", True, GOLD)
        s.blit(score, score.get_rect(center=(W // 2, 168)))
        hint = self.font_sm.render("A / D aim   SPACE charge+toss   R reset   x.com/ElbowOS", True, TEAL)
        s.blit(hint, hint.get_rect(center=(W // 2, H - 48)))
        if self.flash > 0:
            flash = pygame.Surface((W, H), pygame.SRCALPHA)
            flash.fill((90, 255, 140, int(80 * self.flash / 0.22)))
            s.blit(flash, (0, 0))

    def play(self) -> None:
        screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                else:
                    self.handle(ev)
            self.update(dt)
            self.draw(self.surf)
            screen.blit(self.surf, (0, 0))
            pygame.display.flip()

    def record_mp4(self, path: str) -> None:
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart", path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        frames = FPS * 15
        for i in range(frames):
            self.update(1.0 / FPS)
            self.draw(self.surf)
            proc.stdin.write(pygame.image.tostring(self.surf, "RGB"))
            if i % 30 == 0:
                print(f"frame {i}/{frames}", flush=True)
        proc.stdin.close()
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed: {rc}")
        print("wrote", path)


def main() -> None:
    record = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
    play = "--play" in sys.argv
    if record or not play:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.font.init()
    g = Game(record or not play)
    if record or not play:
        out = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/TSAVORITE_TOSS_ElbowOS.mp4")
        g.record_mp4(out)
    else:
        g.play()
    pygame.quit()


if __name__ == "__main__":
    main()
