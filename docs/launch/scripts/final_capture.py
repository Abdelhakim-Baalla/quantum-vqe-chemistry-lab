#!/usr/bin/env python3
"""Capture the final README screenshots and carousel source images.

The app is a real Streamlit process on 127.0.0.1:8501. All captures happen
after a real H2 VQE run; no mock data is injected.
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

LAUNCH = Path(__file__).resolve().parents[1]
ROOT = LAUNCH.parents[1]
OUT = LAUNCH / "screenshots"
ASSETS = ROOT / "docs" / "assets"
OUT.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)

HIDE = """
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
#MainMenu,
footer { display: none !important; }
"""

CLEAN_MAIN = """
[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="stMetricValue"] { font-size: 1.08rem !important; }
"""


def scroll_to(page: Page, locator, offset: int = 16) -> None:
    box = locator.bounding_box()
    if box is None:
        raise RuntimeError("target is not visible")
    current = page.locator("#stMain").evaluate("el => el.scrollTop")
    page.locator("#stMain").evaluate(
        "(el, y) => { el.scrollTop = y; }", int(current + box["y"] - offset)
    )
    page.wait_for_timeout(800)


def hide_chrome(page: Page) -> None:
    page.add_style_tag(content=HIDE)
    page.mouse.move(8, 8)
    page.wait_for_timeout(250)


def capture(page: Page, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(path))
    print("saved", path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


with sync_playwright() as p:
    launch_options = {
        "headless": True,
        "args": ["--no-sandbox", "--force-color-profile=srgb"],
    }
    if os.environ.get("CHROME_PATH"):
        launch_options["executable_path"] = os.environ["CHROME_PATH"]
    browser = p.chromium.launch(**launch_options)
    context = browser.new_context(
        viewport={"width": 1600, "height": 1200},
        device_scale_factor=2,
        color_scheme="light",
        locale="en-US",
    )
    page = context.new_page()
    page.goto("http://127.0.0.1:8501", wait_until="domcontentloaded", timeout=60_000)
    page.get_by_role("button", name="Run VQE Experiment").wait_for(timeout=60_000)
    page.wait_for_timeout(2_800)
    hide_chrome(page)

    page.get_by_role("button", name="Run VQE Experiment").click()
    page.get_by_text(re.compile("Run verified")).wait_for(timeout=180_000)
    page.wait_for_timeout(3_500)

    # README: light dashboard, scrolled to the analytical content.
    scroll_to(page, page.get_by_role("tab", name="Dashboard").first, offset=12)
    capture(page, ASSETS / "quantum-lab-dashboard-light.png")
    shutil.copyfile(
        ASSETS / "quantum-lab-dashboard-light.png",
        ASSETS / "quantum-lab-dashboard.png",
    )

    # README: the same real run in dark mode.
    page.get_by_text("Dark", exact=True).click()
    page.wait_for_timeout(2_600)
    scroll_to(page, page.get_by_role("tab", name="Dashboard").first, offset=12)
    capture(page, ASSETS / "quantum-lab-dashboard-dark.png")
    shutil.copyfile(
        ASSETS / "quantum-lab-dashboard-light.png",
        OUT / "quantum-lab-dashboard-light.png",
    )
    shutil.copyfile(
        ASSETS / "quantum-lab-dashboard-dark.png",
        OUT / "quantum-lab-dashboard-dark.png",
    )

    # Back to light for the carousel source captures.
    page.get_by_text("Light", exact=True).click()
    page.wait_for_timeout(2_200)
    scroll_to(page, page.get_by_role("tab", name="Dashboard").first, offset=12)

    # Carousel screenshots use a wider canvas without the sidebar.
    page.locator('[data-testid="stSidebarCollapseButton"]').first.click()
    page.wait_for_timeout(900)
    page.set_viewport_size({"width": 1900, "height": 1350})
    page.wait_for_timeout(1_300)
    page.add_style_tag(content=HIDE + CLEAN_MAIN)
    page.mouse.move(8, 8)

    scroll_to(page, page.get_by_role("tab", name="Dashboard").first, offset=12)
    capture(page, OUT / "01_dashboard_hero.png")

    page.get_by_role("tab", name="Experiment").click()
    page.wait_for_timeout(2_000)
    scroll_to(page, page.get_by_role("heading", name="Energy results", exact=True).first, 48)
    capture(page, OUT / "02_energy_results.png")

    page.get_by_role("tab", name="Quantum circuit").click()
    page.wait_for_timeout(2_400)
    page.get_by_role("tab", name="Pauli evolution").click()
    page.wait_for_timeout(1_800)
    page.add_style_tag(content=HIDE + CLEAN_MAIN)
    page.mouse.move(8, 8)
    scroll_to(page, page.get_by_role("heading", name="Quantum circuit explorer", exact=True).first, 48)
    capture(page, OUT / "03_circuit.png")

    page.get_by_role("tab", name="Convergence").click()
    page.wait_for_timeout(2_400)
    page.add_style_tag(content=HIDE + CLEAN_MAIN)
    page.mouse.move(8, 8)
    scroll_to(page, page.get_by_role("heading", name="Convergence history", exact=True).first, 48)
    capture(page, OUT / "04_convergence.png")

    page.get_by_role("tab", name="Experiment").click()
    page.wait_for_timeout(1_800)
    page.add_style_tag(content=HIDE + CLEAN_MAIN)
    page.mouse.move(8, 8)
    page.locator("#stMain").evaluate("el => { el.scrollTop = 0; }")
    page.wait_for_timeout(700)
    capture(page, OUT / "05_experiment_wide.png")

    print("captured README and carousel source images")
    context.close()
    browser.close()
