import re
from typing import Dict, Optional, Tuple, Type, Union, cast

import pytest
from playwright.sync_api import Page, expect
import sys
sys.path.append("/home/ying/projects/web_navigation/webarena/")
import time
from help_scripts import process_accessibility_tree, get_close_id
from browser_env import (
    ScriptBrowserEnv,
    create_id_based_action,
    create_key_press_action,
    create_playwright_action,
    create_scroll_action,
)
from browser_env import actions
HEADLESS = True
SLOW_MO = 0


def test_frame_locator(script_browser_env: ScriptBrowserEnv) -> None:
    env = script_browser_env
    seq = """page.goto("https://www.littlewebhut.com/articles/html_iframe_example/")
    page.frame_locator("iframe[name=\\"imgbox\\"]").get_by_role("img").click()"""

    env.reset()
    for action in seq.split("\n"):
        action = action.strip()
        _, success, _, _, info = env.step(create_playwright_action(action))
        assert success


def test_basic(script_browser_env: ScriptBrowserEnv) -> None:
    # click, fill, press, check, goto
    env = script_browser_env
    seq = """page.goto("https://demo.playwright.dev/todomvc/")
    page.get_by_placeholder("What needs to be done?").click()
    page.get_by_placeholder("What needs to be done?").fill("hello")
    page.get_by_placeholder("What needs to be done?").press("Enter")
    page.get_by_placeholder("What needs to be done?").fill("world")
    page.get_by_placeholder("What needs to be done?").press("Enter")
    page.get_by_placeholder("What needs to be done?").fill("yes")
    page.get_by_placeholder("What needs to be done?").press("Enter")
    page.get_by_placeholder("What needs to be done?").fill("no")
    page.get_by_placeholder("What needs to be done?").press("Enter")
    page.get_by_role("listitem").filter(has_text="world").get_by_role("checkbox", name="Toggle Todo").check()
    page.get_by_role("button", name="Clear completed").click()"""

    env.reset()
    for action in seq.split("\n"):
        action = action.strip()
        _, success, _, _, info = env.step(create_playwright_action(action))
        assert success


def test_hover(script_browser_env: ScriptBrowserEnv) -> None:
    env = script_browser_env
    seq = """page.goto("https://ianlunn.github.io/Hover/")
    page.get_by_role("link", name="Download on GitHub").hover()"""

    env.reset()
    for action in seq.split("\n"):
        action = action.strip()
        _, success, _, _, info = env.step(create_playwright_action(action))
        assert success


def test_select_option(script_browser_env: ScriptBrowserEnv) -> None:
    env = script_browser_env
    seq = """page.goto("https://russmaxdesign.github.io/exercise/#link-two")
    page.get_by_role("combobox", name="Favourite mammal").select_option("African Wild Dog")"""
    env.reset()
    for action in seq.split("\n"):
        action = action.strip()
        _, success, _, _, info = env.step(create_playwright_action(action))
        assert success


def test_xpath(script_browser_env: ScriptBrowserEnv) -> None:
    env = script_browser_env

    seq = """page.goto("https://demo.playwright.dev/todomvc/")
    page.goto("https://demo.playwright.dev/todomvc/#/")
    page.get_by_placeholder("What needs to be done?").click()
    page.get_by_placeholder("What needs to be done?").fill("hello")
    page.get_by_placeholder("What needs to be done?").press("Enter")
    page.get_by_role("link", name="Completed").click()
    page.locator("xpath=/html/body/section/div/header/input").fill("no")
    page.get_by_placeholder("What needs to be done?").press("Enter")
    page.goto("https://bic-berkeley.github.io/psych-214-fall-2016/string_literals.html")
    page.locator("xpath=//*[@id=\'searchbox\']/div/form/input[1]").fill("type")"""
    env.reset()
    for action in seq.split("\n"):
        action = action.strip()
        _, success, _, _, info = env.step(create_playwright_action(action))
        assert success


def test_inter_page_actions(
    script_browser_env: ScriptBrowserEnv,
) -> None:
    env = script_browser_env
    seq = """page.goto("https://demo.playwright.dev/todomvc/")
    browser.new_tab()
    browser.page_focus(0)
    browser.page_focus(1)
    page.page_close()
    page.goto("https://google.com")
    page.goto("https://demo.playwright.dev/todomvc/")
    page.go_back()
    page.go_forward()"""
    env.reset()
    for action in seq.split("\n"):
        action = action.strip()
        _, success, _, _, info = env.step(create_playwright_action(action))
        assert success
    assert "https://demo.playwright.dev/todomvc" in info["page"].url


def test_scroll(
    current_viewport_script_browser_env: ScriptBrowserEnv,
) -> None:
    env = current_viewport_script_browser_env
    env.reset()
    _, success, _, _, _ = env.step(create_scroll_action("down"))
    assert success
    _, success, _, _, _ = env.step(create_scroll_action("up"))
    assert success


def test_id_click(
    accessibility_tree_current_viewport_script_browser_env: ScriptBrowserEnv,
) -> None:
    env = accessibility_tree_current_viewport_script_browser_env
    env.reset()

    obs, success, _, _, info = env.step(
        create_playwright_action(
            'page.goto("https://russmaxdesign.github.io/exercise/")'
        )
    )
    assert success
    assert "link 'McKenna/Bell'" in obs["text"]
    # get the id of the link
    element_id = re.search(r"\[(\d+)\] link 'McKenna/Bell'", obs["text"]).group(1)  # type: ignore

    obs, success, _, _, info = env.step(
        create_id_based_action(f"click [{element_id}]")
    )
    assert success
    assert (
        info["page"].url
        == "https://russmaxdesign.github.io/exercise/#link-four"
    )

    obs, success, _, _, info = env.step(create_scroll_action("down"))
    assert "link 'Classification'" in obs["text"]
    element_id = re.search(r"\[(\d+)\] link 'Classification'", obs["text"]).group(1)  # type: ignore

    obs, success, _, _, info = env.step(
        create_id_based_action(f"click [{element_id}]")
    )
    assert success
    assert (
        info["page"].url
        == "https://russmaxdesign.github.io/exercise/#link-two"
    )
    assert "radio 'Weekly'" in obs["text"]
    element_id = re.search(r"\[(\d+)\] radio 'Weekly'", obs["text"]).group(1)  # type: ignore

    obs, success, _, _, info = env.step(
        create_id_based_action(f"click [{element_id}]")
    )
    assert success
    assert "radio 'Weekly'" in obs["text"]


def test_id_hover(
    accessibility_tree_current_viewport_script_browser_env: ScriptBrowserEnv,
) -> None:
    env = accessibility_tree_current_viewport_script_browser_env
    env.reset()

    obs, success, _, _, info = env.step(
        create_playwright_action(
            'page.goto("https://ianlunn.github.io/Hover/")'
        )
    )
    assert success
    assert "link 'Download on GitHub'" in obs["text"]
    element_id = re.search(r"\[(\d+)\] link 'Download on GitHub'", obs["text"]).group(1)  # type: ignore

    obs, success, _, _, info = env.step(
        create_id_based_action(f"hover [{element_id}]")
    )
    assert success


def test_key_press(
    accessibility_tree_current_viewport_script_browser_env: ScriptBrowserEnv,
) -> None:
    env = accessibility_tree_current_viewport_script_browser_env
    env.reset()

    obs, success, _, _, info = env.step(
        create_playwright_action(
            'page.goto("https://russmaxdesign.github.io/exercise/")'
        )
    )
    assert success
    assert "textbox 'Full name'" in obs["text"]
    element_id = re.search(r"\[(\d+)\] textbox 'Full name'", obs["text"]).group(1)  # type: ignore
    s = "My Name IS XYZ"

    obs, success, _, _, info = env.step(
        create_id_based_action(f"type [{element_id}] [{s}] [0]")
    )

    assert success
    expect(env.page.get_by_label("Full name")).to_be_focused()
    expect(env.page.get_by_label("Full name")).to_have_value(s)

    obs, success, _, _, info = env.step(
        create_id_based_action("press [meta+a]")
    )
    assert success

    env.page.get_by_label("Full name").type(s)
    expect(env.page.get_by_label("Full name")).to_have_value(s)

    obs, success, _, _, info = env.step(create_key_press_action("Enter"))
    assert success
    expect(env.page.get_by_label("Email")).to_be_focused()


def test_id_type(
    accessibility_tree_current_viewport_script_browser_env: ScriptBrowserEnv,
) -> None:
    env = accessibility_tree_current_viewport_script_browser_env
    env.reset()
    obs, success, _, _, info = env.step(
        create_playwright_action(
            'page.goto("https://russmaxdesign.github.io/exercise/")'
        )
    )
    assert success
    assert "textbox 'Full name'" in obs["text"]
    s = "My Name IS XYZ"
    element_id = re.search(r"\[(\d+)\] textbox 'Full name'", obs["text"]).group(1)  # type: ignore

    obs, success, _, _, info = env.step(
        create_id_based_action(f"type [{element_id}] [{s}]")
    )
    assert success
    locator = env.page.get_by_label("Full name")
    expect(locator).to_have_value(s)


def test_e2e_id_based_actions(
    accessibility_tree_script_browser_env: ScriptBrowserEnv,
) -> None:
    env = accessibility_tree_script_browser_env
    env.reset()
    obs, *_ = env.step(
        create_id_based_action(
            "goto [https://russmaxdesign.github.io/exercise/]"
        )
    )
    element_id = re.search(r"\[(\d+)\] link 'What are mammals\?'", obs["text"]).group(1)  # type: ignore
    obs, *_ = env.step(create_id_based_action(f"click [{element_id}]"))
    element_id = re.search(r"\[(\d+)\] textbox 'Email'", obs["text"]).group(1)  # type: ignore
    env.step(
        create_id_based_action(f"type [{element_id}] [test@gmail.com] [0]")
    )
    env.step(create_id_based_action("scroll [down]"))
    env.step(create_id_based_action("scroll [up]"))
    env.step(create_id_based_action("new_tab"))
    env.step(create_id_based_action("tab_focus [0]"))
    env.step(create_id_based_action("tab_focus [1]"))
    env.step(create_id_based_action("goto [https://example.com/]"))
    env.step(create_id_based_action("go_back"))
    x = env.step(create_id_based_action("go_forward"))
    assert x[-1]["page"].url == "https://example.com/"
    x = env.step(create_id_based_action("tab_focus [0]"))
    assert (
        x[-1]["page"].url
        == "https://russmaxdesign.github.io/exercise/#link-one"
    )


def test_id_delete_input(
    accessibility_tree_current_viewport_script_browser_env: ScriptBrowserEnv,
) -> None:
    env = accessibility_tree_current_viewport_script_browser_env
    env.reset()
    obs, success, _, _, info = env.step(
        create_playwright_action(
            'page.goto("https://russmaxdesign.github.io/exercise/")'
        )
    )
    assert success
    assert "textbox 'Full name'" in obs["text"]
    s = "My Name IS XYZ"
    element_id = re.search(r"\[(\d+)\] textbox 'Full name'", obs["text"]).group(1)  # type: ignore

    obs, success, _, _, info = env.step(
        create_id_based_action(f"type [{element_id}] [{s}]")
    )
    assert success
    locator = env.page.get_by_label("Full name")
    expect(locator).to_have_value(s)

    obs, success, _, _, info = env.step(
        create_id_based_action(f"click [{element_id}]")
    )
    assert success

    obs, success, _, _, info = env.step(
        create_id_based_action(f"press [Meta+a]")
    )
    assert success

    obs, success, _, _, info = env.step(
        create_id_based_action("press [backspace]")
    )
    assert success

    new_s = "NEW"
    obs, success, _, _, info = env.step(
        create_id_based_action(f"type [{element_id}] [{new_s}]")
    )
    locator = env.page.get_by_label("Full name")
    expect(locator).to_have_value(new_s)

def test_id_click_dialog_remove(
    accessibility_tree_current_viewport_script_browser_env: ScriptBrowserEnv,
) -> None:
    env = accessibility_tree_current_viewport_script_browser_env
    env.reset()

    obs, success, _, _, info = env.step(
        create_playwright_action(
            'page.goto("https://eslfaceitgroup.com/career/")'
        )
    )
    close_id = get_close_id(obs['text'])
    print(close_id)
    obs, success, _, _, info = env.step(
        create_id_based_action(f"click {close_id}")
    )
    # obs, success, _, _, info = env._remove_popups()
    # assert success
    # assert "link 'Training'" in obs["text"]

    # (1076.359375, 360.28125)
    # (1091.359375, 2591.28125)
    # scroll x,y (451.359375, 2231.28125)
    # (new_center_x, new_y) (1116.9296875, 380.28125)

    # env.page.evaluate(f"""window.scrollTo({{
    #     top: 2231.28125,
    #     left: 451.359375,
    #     behavior: 'smooth'
    #     }});""")
    # # env.page.mouse.move(1116.9296875, 480.28125)
    # # time.sleep(5)
    # env.page.mouse.click(1231.9296875, 481.28125)
    # # # env.page.mouse.click(1116.9296875, 380.28125)
    # print("success")
    # time.sleep(50000)
    # 1131.9296875
    # 449.2812499999999
    # with open('obs.txt', 'w') as f:
    #     f.write(obs['text'])
    element_id = re.search(r"\[(\d+)\] link 'APPLY'", obs["text"]).group(1)  # type: ignore
    # # print(element_id)
    obs, success, _, _, info = env.step(
        create_id_based_action(f"click [{element_id}]")
    )
    print(111)
    time.sleep(20)
    # # process_accessibility_tree(obs['text'])
    # # print(obs)
    # print('end')
    # assert success
env = ScriptBrowserEnv(
    headless=False,
    slow_mo=100,
    observation_type="accessibility_tree",
    current_viewport_only=False,
    viewport_size={"width": 1280, "height": 720},
)
test_id_click_dialog_remove(env)
    # assert (
    #     info["page"].url
    #     == "https://russmaxdesign.github.io/exercise/#link-four"
    # )

    # obs, success, _, _, info = env.step(create_scroll_action("down"))
    # assert "link 'Classification'" in obs["text"]
    # element_id = re.search(r"\[(\d+)\] link 'Classification'", obs["text"]).group(1)  # type: ignore

    # obs, success, _, _, info = env.step(
    #     create_id_based_action(f"click [{element_id}]")
    # )
    # assert success
    # assert (
    #     info["page"].url
    #     == "https://russmaxdesign.github.io/exercise/#link-two"
    # )
    # assert "radio 'Weekly'" in obs["text"]
    # element_id = re.search(r"\[(\d+)\] radio 'Weekly'", obs["text"]).group(1)  # type: ignore

    # obs, success, _, _, info = env.step(
    #     create_id_based_action(f"click [{element_id}]")
    # )
    # assert success
    # assert "radio 'Weekly'" in obs["text"]


  