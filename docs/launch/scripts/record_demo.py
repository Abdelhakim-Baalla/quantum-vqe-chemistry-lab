#!/usr/bin/env python3
"""Record the live Quantum Lab walkthrough with a synthetic cursor.

Playwright's headless capture does not record the operating-system pointer. To
make the interaction legible, this script injects a small cursor overlay, moves
it smoothly, paints a click ripple, and applies a subtle zoom pulse around each
click. All content in the app is produced by a real H2 VQE run.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

OUT = Path(os.environ.get("QUANTUM_LAB_RAW_DIR", "/tmp/opencode/video_raw"))
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)

HIDE = """
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
#MainMenu,
footer { display: none !important; }
"""

OVERLAY_CSS = """
html, body, * { cursor: none !important; }
[data-testid="stSidebar"] { padding-top: 1.2rem !important; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.72rem !important; }
#stMain [data-testid="stMainBlockContainer"] { padding-bottom: 520px !important; }
#lab-video-caption {
  position: fixed;
  left: 328px;
  bottom: 24px;
  z-index: 2147483647;
  display: flex;
  align-items: center;
  gap: 11px;
  min-width: 300px;
  padding: 8px 14px 8px 8px;
  background: rgba(247, 247, 245, 0.96);
  border: 1px solid #d9d9d9;
  box-shadow: 0 8px 28px rgba(22, 22, 22, 0.09);
  font-family: "Noto Sans", "Helvetica Neue", Arial, sans-serif;
  opacity: 1;
  transition: opacity 180ms ease;
  pointer-events: none;
}
#lab-video-caption .cap-badge {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0f62fe;
  color: #ffffff;
  font-family: "Noto Sans Mono", "SFMono-Regular", Consolas, monospace;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.08em;
  flex: none;
}
#lab-video-caption .cap-copy { display: flex; flex-direction: column; gap: 3px; }
#lab-video-caption .cap-title {
  font-family: "Noto Sans Mono", "SFMono-Regular", Consolas, monospace;
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.09em;
  color: #161616;
  line-height: 1;
}
#lab-video-caption .cap-sub {
  font-size: 12px;
  color: #6f6f6f;
  line-height: 1.2;
}
#lab-cursor {
  position: fixed;
  left: 0;
  top: 0;
  z-index: 2147483647;
  width: 24px;
  height: 24px;
  pointer-events: none;
  will-change: transform;
  filter: drop-shadow(0 2px 3px rgba(22, 22, 22, 0.22));
  transform: translate(1650px, 900px);
}
.lab-ripple {
  position: fixed;
  z-index: 2147483646;
  width: 18px;
  height: 18px;
  border: 2px solid #0f62fe;
  border-radius: 50%;
  pointer-events: none;
  transform: translate(-50%, -50%) scale(0.2);
  animation: lab-ripple 560ms ease-out forwards;
}
@keyframes lab-ripple {
  0% { opacity: 0.9; transform: translate(-50%, -50%) scale(0.2); }
  100% { opacity: 0; transform: translate(-50%, -50%) scale(3.2); }
}
"""

CAPTION_HTML = """
<div id="lab-video-caption">
  <div class="cap-badge">LIVE</div>
  <div class="cap-copy">
    <div class="cap-title">LOCAL WORKBENCH</div>
    <div class="cap-sub">H₂ / STO-3G / UCCSD</div>
  </div>
</div>
<div id="lab-cursor" aria-hidden="true">
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
    <path d="M3.5 2.5 L20 12 L12.2 13.2 L9.1 21 Z"
          fill="#161616" stroke="#ffffff" stroke-width="1.6" stroke-linejoin="round"/>
  </svg>
</div>
"""

_cursor = {"x": 1650.0, "y": 900.0}
_marks: dict[str, float] = {}
_t0 = 0.0


def mark(name: str) -> None:
    _marks[name] = round(time.monotonic() - _t0, 3)


def ensure_overlay(page: Page) -> None:
    page.evaluate(
        """([css, html]) => {
            if (!document.getElementById('lab-video-caption')) {
                document.body.insertAdjacentHTML('beforeend', html);
            }
            const cursor = document.getElementById('lab-cursor');
            if (cursor) {
                cursor.style.transform = `translate(${window.__labCursorX ?? 1650}px, ${window.__labCursorY ?? 900}px)`;
            }
            let style = document.getElementById('lab-overlay-style');
            if (!style) {
                style = document.createElement('style');
                style.id = 'lab-overlay-style';
                style.textContent = css;
                document.head.appendChild(style);
            }
            const sidebarCaptions = document.querySelectorAll(
                '[data-testid="stSidebar"] [data-testid="stCaptionContainer"]'
            );
            if (sidebarCaptions.length) {
                sidebarCaptions[sidebarCaptions.length - 1].style.display = 'none';
            }
        }""",
        [OVERLAY_CSS, CAPTION_HTML],
    )


def set_caption(page: Page, badge: str, title: str, subtitle: str) -> None:
    ensure_overlay(page)
    page.evaluate(
        """([badge, title, subtitle]) => {
            const el = document.getElementById('lab-video-caption');
            if (!el) return;
            el.style.opacity = '0';
            setTimeout(() => {
                el.querySelector('.cap-badge').textContent = badge;
                el.querySelector('.cap-title').textContent = title;
                el.querySelector('.cap-sub').textContent = subtitle;
                el.style.opacity = '1';
            }, 140);
        }""",
        [badge, title, subtitle],
    )
    page.wait_for_timeout(260)


def move_cursor(page: Page, x: float, y: float, duration: int = 650) -> None:
    start_x, start_y = _cursor["x"], _cursor["y"]
    page.evaluate(
        """([sx, sy, ex, ey, duration]) => new Promise((resolve) => {
            const cursor = document.getElementById('lab-cursor');
            if (!cursor) { resolve(); return; }
            const started = performance.now();
            const ease = (t) => 1 - Math.pow(1 - t, 3);
            function frame(now) {
                const t = Math.min(1, (now - started) / duration);
                const p = ease(t);
                cursor.style.transform =
                    `translate(${sx + (ex - sx) * p}px, ${sy + (ey - sy) * p}px)`;
                if (t < 1) requestAnimationFrame(frame);
                else {
                    window.__labCursorX = ex;
                    window.__labCursorY = ey;
                    resolve();
                }
            }
            requestAnimationFrame(frame);
        })""",
        [start_x, start_y, x, y, duration],
    )
    _cursor["x"], _cursor["y"] = x, y
    page.wait_for_timeout(duration + 60)


def ripple(page: Page, x: float, y: float) -> None:
    page.evaluate(
        """([x, y]) => {
            const el = document.createElement('div');
            el.className = 'lab-ripple';
            el.style.left = `${x}px`;
            el.style.top = `${y}px`;
            document.body.appendChild(el);
            setTimeout(() => el.remove(), 700);
        }""",
        [x, y],
    )


def zoom_pulse(page: Page, x: float, y: float, scale: float = 1.022) -> None:
    page.evaluate(
        """([x, y, scale]) => {
            const app = document.querySelector('.stApp');
            if (!app) return;
            app.style.transition = 'transform 220ms cubic-bezier(.2, .8, .2, 1)';
            app.style.transformOrigin = `${x}px ${y}px`;
            app.style.transform = `scale(${scale})`;
        }""",
        [x, y, scale],
    )
    page.wait_for_timeout(240)
    page.evaluate(
        """() => {
            const app = document.querySelector('.stApp');
            if (app) app.style.transform = 'scale(1)';
        }"""
    )
    page.wait_for_timeout(300)


def click_locator(page: Page, locator, *, pause: int = 900) -> None:
    box = locator.bounding_box()
    if box is None:
        raise RuntimeError("click target is not visible")
    x = box["x"] + box["width"] / 2
    y = box["y"] + box["height"] / 2
    move_cursor(page, x, y, 450)
    page.mouse.click(x, y)
    ripple(page, x, y)
    zoom_pulse(page, x, y)
    page.wait_for_timeout(pause)
    ensure_overlay(page)


def smooth_scroll(page: Page, target: float, duration: int = 1200) -> None:
    page.evaluate(
        """([target, duration]) => new Promise((resolve) => {
            const el = document.querySelector('#stMain');
            if (!el) { resolve(); return; }
            const start = el.scrollTop;
            const delta = Math.max(0, target) - start;
            const started = performance.now();
            const ease = (t) => t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
            function frame(now) {
                const t = Math.min(1, (now - started) / duration);
                el.scrollTop = start + delta * ease(t);
                if (t < 1) requestAnimationFrame(frame);
                else resolve();
            }
            requestAnimationFrame(frame);
        })""",
        [target, duration],
    )
    page.wait_for_timeout(120)


def scroll_to_locator(page: Page, locator, offset: int = 42, duration: int = 1500) -> None:
    box = locator.bounding_box()
    if box is None:
        return
    current = page.locator("#stMain").evaluate("el => el.scrollTop")
    smooth_scroll(page, current + box["y"] - offset, duration)


with sync_playwright() as p:
    launch_options = {
        "headless": True,
        "args": ["--no-sandbox", "--force-color-profile=srgb"],
    }
    if os.environ.get("CHROME_PATH"):
        launch_options["executable_path"] = os.environ["CHROME_PATH"]
    browser = p.chromium.launch(**launch_options)
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        record_video_dir=str(OUT),
        record_video_size={"width": 1920, "height": 1080},
        device_scale_factor=1,
        color_scheme="light",
        locale="en-US",
    )
    page = context.new_page()
    _t0 = time.monotonic()
    page.goto("http://127.0.0.1:8501", wait_until="domcontentloaded", timeout=60_000)
    page.get_by_role("button", name="Run VQE Experiment").wait_for(timeout=60_000)
    page.wait_for_timeout(2_800)
    page.add_style_tag(content=HIDE)
    ensure_overlay(page)
    move_cursor(page, 1660, 920, 900)
    page.wait_for_timeout(500)

    # Hero
    set_caption(page, "LIVE", "LOCAL WORKBENCH", "H₂ / STO-3G / UCCSD")
    mark("hero")
    page.wait_for_timeout(1_900)

    # Run. The click gets a cursor move, ripple and subtle zoom before the app
    # enters its real optimization loop.
    run_button = page.get_by_role("button", name="Run VQE Experiment")
    click_locator(page, run_button, pause=250)
    set_caption(page, "01", "RUN THE EXPERIMENT", "24 evaluations · 4 iterations")
    page.get_by_text(re.compile("Run verified")).wait_for(timeout=180_000)
    page.wait_for_timeout(800)
    ensure_overlay(page)
    mark("run_complete")

    # Dashboard
    set_caption(page, "02", "THE DASHBOARD", "12 metrics · six real-data views")
    scroll_to_locator(
        page,
        page.get_by_role("heading", name="Run dashboard", exact=True).first,
        offset=82,
        duration=1_000,
    )
    move_cursor(page, 980, 610, 550)
    mark("dashboard_view")
    page.wait_for_timeout(3_200)

    # Experiment result
    set_caption(page, "03", "THE RESULT", "VQE vs exact: 4.44 × 10⁻¹⁶ Ha")
    smooth_scroll(page, 0, duration=500)
    click_locator(page, page.get_by_role("tab", name="Experiment").first, pause=600)
    scroll_to_locator(
        page,
        page.get_by_role("heading", name="Energy results", exact=True).first,
        offset=82,
        duration=1_000,
    )
    move_cursor(page, 1300, 560, 500)
    mark("result_view")
    page.wait_for_timeout(3_300)

    # Optimizer trace
    set_caption(page, "04", "THE OPTIMIZER TRACE", "every recorded evaluation")
    smooth_scroll(page, 0, duration=500)
    click_locator(page, page.get_by_role("tab", name="Convergence").first, pause=600)
    scroll_to_locator(
        page,
        page.get_by_role("heading", name="Convergence history", exact=True).first,
        offset=82,
        duration=900,
    )
    move_cursor(page, 1100, 500, 500)
    mark("convergence_view")
    page.wait_for_timeout(3_300)

    # Executed circuit
    set_caption(page, "05", "THE EXECUTED CIRCUIT", "rendered from the real UCCSD ansatz")
    smooth_scroll(page, 0, duration=500)
    click_locator(page, page.get_by_role("tab", name="Quantum circuit").first, pause=600)
    click_locator(page, page.get_by_role("tab", name="Pauli evolution").first, pause=900)
    page.wait_for_timeout(1_500)
    circuit_heading = page.get_by_role(
        "heading", name="Quantum circuit explorer", exact=True
    ).first
    scroll_to_locator(page, circuit_heading, offset=82, duration=900)
    page.wait_for_timeout(250)
    scroll_to_locator(page, circuit_heading, offset=82, duration=450)
    move_cursor(page, 1200, 560, 500)
    mark("circuit_view")
    page.wait_for_timeout(3_800)
    mark("circuit_hold")

    # Park the cursor out of the way for the closing beat.
    move_cursor(page, 1760, 930, 550)
    mark("end")
    page.wait_for_timeout(700)

    video = page.video
    context.close()
    browser.close()
    raw = Path(video.path())
    target = OUT / "demo_raw.webm"
    shutil.move(str(raw), target)
    (OUT / "timeline.json").write_text(json.dumps(_marks, indent=2) + "\n")
    print("raw video", target, target.stat().st_size)
    print("timeline", json.dumps(_marks))
