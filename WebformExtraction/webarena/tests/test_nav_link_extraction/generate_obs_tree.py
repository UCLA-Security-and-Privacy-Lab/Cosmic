import re
from typing import Dict, Optional, Tuple, Type, Union, cast

import pytest
from playwright.sync_api import Page, expect
import sys
sys.path.append("/home/ying/projects/web_navigation/webarena/")
import time
from bs4 import BeautifulSoup

from browser_env import (
    ScriptBrowserEnv,
    create_id_based_action,
    create_key_press_action,
    create_playwright_action,
    create_scroll_action,
)
from browser_env import actions

env = ScriptBrowserEnv(
    headless=False,
    # slow_mo=100,
    observation_type="accessibility_tree",
    current_viewport_only=False,
    viewport_size={"width": 1280, "height": 720},
)
env.reset()
obs, success, _, _, info = env.step(
        create_playwright_action(
            'page.goto("https://www.cabi.org/what-we-do/science-and-social-science-research/")'
        )
    )

obs_tree = obs['text']
print(obs_tree)
