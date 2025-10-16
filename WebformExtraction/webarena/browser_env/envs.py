import json
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union

import numpy as np
import numpy.typing as npt
from beartype import beartype
from beartype.door import is_bearable
from gymnasium import Env
from gymnasium.spaces import Box, Text
import ssl
from playwright.sync_api import (
    CDPSession,
    Page,
    Playwright,
    ViewportSize,
    expect,
    sync_playwright,
)

from .actions import Action, execute_action, get_action_space
from .processors import ObservationHandler, ObservationMetadata
from .utils import (
    AccessibilityTree,
    DetachedPage,
    Observation,
    png_bytes_to_numpy,
)


@dataclass
class PlaywrightScript:
    function: str  # goto, get_by_role
    destination: str  # https://www.google.com/, combobox
    name: str | None = None  # Search, Avatar 2009
    operation: str | None = None  # click, fill, press
    value: str | None = None  # avatar movie, Enter


def parse_action(action: str) -> PlaywrightScript:
    splitted = action.strip().split(" ")
    assert len(splitted) >= 2
    match splitted[:2]:
        case ["goto", url]:
            assert len(splitted) == 2
            return PlaywrightScript("goto", url)
        case ["get_by_role", destination]:
            assert len(splitted) >= 4
            match splitted[2:]:
                case [name, operation]:
                    return PlaywrightScript(
                        "get_by_role", destination, name, operation
                    )
                case [name, operation, value]:
                    return PlaywrightScript(
                        "get_by_role", destination, name, operation, value
                    )
                case _:
                    raise ValueError("Invalid action")
        case _:
            raise ValueError(f"Invalid action {action}")


class ScriptBrowserEnv(Env[dict[str, Observation], Action]):
    """
    The goal of this environment is to produce a prototype of a browser environment.
    In the end, we want to support a fully configurable browser environment with wide
    range of action spaces and observation spaces, both structured and unstructured.
    But in this prototype, we just support action space specified by Playwright script,
    and observation space is the html content of the page.
    """

    @beartype
    def __init__(
        self,
        max_page_length: int = 8192,
        headless: bool = True,
        slow_mo: int = 0,
        observation_type: str = "html",
        current_viewport_only: bool = False,
        viewport_size: ViewportSize = {"width": 1280, "height": 720},
        save_trace_enabled: bool = False,
        sleep_after_execution: float = 0.0,
    ):
        # TODO: make Space[Action] = ActionSpace
        self.action_space = get_action_space()  # type: ignore[assignment]
        self.headless = headless
        self.slow_mo = slow_mo
        self.current_viewport_only = current_viewport_only
        self.reset_finished = False
        self.viewport_size = viewport_size
        self.save_trace_enabled = save_trace_enabled
        self.sleep_after_execution = sleep_after_execution

        match observation_type:
            case "html" | "accessibility_tree":
                self.text_observation_type = observation_type
                self.image_observation_type = ""
                self.main_observation_type = "text"
            case "image":
                self.image_observation_type = observation_type
                self.text_observation_type = ""  # type: ignore[assignment]
                self.main_observation_type = "image"
            case _:
                raise ValueError(
                    f"Unsupported observation type: {observation_type}"
                )

        self.observation_handler = ObservationHandler(
            self.main_observation_type,
            self.text_observation_type,
            self.image_observation_type,
            self.current_viewport_only,
            self.viewport_size,
        )

        self.observation_space = (
            self.observation_handler.get_observation_space()
        )
    def _find_iframes(self):
        iframe_contents = []
        iframes = self.page.frames
        for i, frames in enumerate(iframes):
            for frame in frames.child_frames:
                time.sleep(2)
                try:
                    frame_content = frame.content()
                except:
                    continue
                if "<input" not in frame_content:
                    continue
                frame_name = frame.name
                frame_url = frame.url
                iframe_element = self.page.query_selector(f'iframe[src="{frame_url}"]') or self.page.query_selector(f'iframe[name="{frame_name}"]')
                if iframe_element:
                    title = iframe_element.get_attribute('title')
                else:
                    title = ""
                # accessibility_tree = iframe_element.content_frame().accessibility.snapshot()
                iframe_contents.append([frame_content, title, frame_url])
        return iframe_contents
    def _fetch_accessibility_tree(self, client:CDPSession):
        AccessibilityTree = client.send(
            "Accessibility.getFullAXTree", {}
        )['nodes']
        return AccessibilityTree
    def _check_iframe(self, iframe_info):
        ret_dict = []
        for item in iframe_info:
            frame_content = item[0]
            title = item[1]
            frame_url = item[2]
            tmp_dict = {}
            tab = self.context.new_page()
            tab.goto(frame_url)
            # tmp_client = tab.context.new_cdp_session(tab)
            # tmp_client.send("Accessibility.enable")
            obs = tab.accessibility.snapshot(interesting_only=False)
            tmp_dict['frame_content'] = frame_content
            tmp_dict['title'] = title
            tmp_dict['url'] = frame_url
            tmp_dict['obs'] = obs
            tab.close()
            self.page.click('body')
            ret_dict.append(tmp_dict)
        return ret_dict

    def _check_popups(self)->bool:
        has_dialog = self.page.locator('[role="dialog"]').count() > 0
        has_alertdialog = self.page.locator('[role="alertdialog"]').count() > 0

        if has_dialog or has_alertdialog:
            return True
        return False

    def _return_msgs(self)->tuple[dict[str, Observation], float, bool, bool, dict[str, Any]]:
        success = False
        fail_error = ""
        observation = self._get_obs()
        observation_metadata = self._get_obs_metadata()
        xpaths_input = self._get_xpaths_all_elements()
        closes_spans = self._all_close_elements()
        popups = self._check_popups()
        iframes = self._find_iframes()
        iframes = self._check_iframe(iframes)
        info = {
            "page": DetachedPage(self.page.url, self.page.content()),
            "fail_error": fail_error,
            "obs": self._fetch_accessibility_tree(self.page.client),
            "observation_metadata": observation_metadata,
            'xpaths_input': xpaths_input,
            'closes_ele': closes_spans,
            'popup': popups,
            'iframe': iframes
        }
        msg = (
            observation,
            float(success),  # reward
            False,  # terminated
            False,  # truncated
            info,
        )
        return msg
    def _remove_popups(self)->tuple[dict[str, Observation], float, bool, bool, dict[str, Any]]:
        success = False
        fail_error = ""
        try:
            self.page.evaluate("""() => {
                const dialog = document.querySelector('[role="dialog"]');
                if (dialog) {
                    dialog.remove();
                }
            }""")
        
            self.page.evaluate("""() => {
                const dialog = document.querySelector('[role="alertdialog"]');
                if (dialog) {
                    dialog.remove();
                }
            }""")
            success = True
        except Exception as e:
            fail_error = str(e)

        observation = self._get_obs()
        observation_metadata = self._get_obs_metadata()
        xpaths_input = self._get_xpaths_all_elements()
        closes_spans = self._all_close_elements()
        popups = self._check_popups()
        iframes = self._find_iframes()
        iframes = self._check_iframe(iframes)
        info = {
            "page": DetachedPage(self.page.url, self.page.content()),
            "fail_error": fail_error,
            "obs": self._fetch_accessibility_tree(self.page.client),
            "observation_metadata": observation_metadata,
            'xpaths_input': xpaths_input,
            'closes_ele': closes_spans,
            'popup': popups,
            'iframe': iframes
        }
        msg = (
            observation,
            float(success),  # reward
            False,  # terminated
            False,  # truncated
            info,
        )
        return msg

    def _find_all_dialogs(self):
        dialog_selector = "[class*='dialog']"
        modal_selector = "[class*='modal']"
        # dialog_elements = page.query_selector_all("[class*='dialog']")
        # modal_elements = page.query_selector_all("[class*='modal']")
        dialog_xpath_html_dict = self._get_xpath_outhtml_by_selector(dialog_selector)
        modal_xpath_html_dict = self._get_xpath_outhtml_by_selector(modal_selector)
        dialog_xpath_html_dict.update(modal_xpath_html_dict)
        return dialog_xpath_html_dict
    
    def _filter_outer_xpaths(self, xpath_dict)->dict:
        '''
            The XPath dict is dict {xpath: outerhtml}
        '''
        xpaths_list = list(xpath_dict.keys())
        xpaths = sorted(xpaths_list, key=lambda x: x.count('/'))
        outer_xpaths = []

        for xpath in xpaths:
            if not any(xpath.startswith(outer_xpath + '/') for outer_xpath in outer_xpaths):
                outer_xpaths.append(xpath)
        filtered_dict = {key: xpath_dict[key] for key in outer_xpaths}

        return filtered_dict


    def _find_close_elements(self)->dict:
        button_close_selector = "button[class*='close'], button[class*='exit']"
        close_xpath_html = self._get_xpath_outhtml_by_selector(button_close_selector)

        span_close_selector = "span[class*='close'], span[class*='exit']"
        close_xpath_html.update(self._get_xpath_outhtml_by_selector(span_close_selector))
        return close_xpath_html

    # def filter_close_button_xpaths(dialog_xpaths):
    #     # Filter button XPaths to ensure they are subpaths of dialog XPaths
    #     # and that they represent 'close' buttons (assuming a naming convention in the XPath).
    #     button_close = 'button[class*="close"]'
    #     button_close_xpath_html = self._get_xpath_outhtml_by_selector(button_close)
    #     # button_xpath =
    #     filtered_button_xpaths = [
    #         button_xpath for button_xpath in button_xpaths
    #         if any(button_xpath.startswith(dialog_xpath + '/') and '/button[' in button_xpath for dialog_xpath in dialog_xpaths)
    #     ]

    #     return filtered_button_xpaths

    def filter_span_xpaths(self, dialog_xpaths, close_xpaths, span_xpaths):
        # Filter close XPaths to ensure they are subpaths of dialog XPaths
        filtered_close_xpaths = [
            close_xpath for close_xpath in close_xpaths
            if any(close_xpath.startswith(dialog_xpath + '/') for dialog_xpath in dialog_xpaths)
        ]

        # Filter span XPaths to ensure they are subpaths of the filtered close XPaths
        filtered_span_xpaths = [
            span_xpath for span_xpath in span_xpaths
            if any(span_xpath.startswith(close_xpath + '/') for close_xpath in filtered_close_xpaths)
        ]

        return filtered_span_xpaths
    def filter_close_xpaths(self, dialog_xpaths, close_xpaths)->list:
        filtered_close_xpaths = [
            close_xpath for close_xpath in close_xpaths
            if any(close_xpath.startswith(dialog_xpath + '/') for dialog_xpath in dialog_xpaths)
        ]
        return filtered_close_xpaths

    def _all_close_elements(self)->list:
        dialog_modals = self._find_all_dialogs()
        filtered_dialog_modals = self._filter_outer_xpaths(dialog_modals)
        dialog_xpaths = list(filtered_dialog_modals.keys())
        # print(dialog_xpaths)

        closes = self._find_close_elements()
        filtered_closes = self._filter_outer_xpaths(closes)
        close_xpaths = list(filtered_closes.keys())
        # print(close_xpaths)

        filtered_close_xpaths = self.filter_close_xpaths(dialog_xpaths, close_xpaths)
        return filtered_close_xpaths

    def _get_xpath(self, element):
        try:
            return self.page.evaluate('''(element) => {
                function getElementXPath(elem) {
                    if (!elem || elem.nodeType !== 1) {
                        return ''; // Return empty if the element is not valid or not an element node
                    }

                    if (elem === document.documentElement) {
                        return elem.tagName.toLowerCase();  // Return the tag name of the root element
                    }

                    // Return a more specific XPath if the element has a unique ID
                    if (elem.id && document.querySelectorAll(`#${CSS.escape(elem.id)}`).length === 1) {
                        return `id("${elem.id}")`;
                    }

                    // Get the siblings and this element's tag count among them
                    let siblings = elem.parentNode ? elem.parentNode.childNodes : [];
                    let sameTagCount = 0;
                    let ownPosition = 0;
                    for (let i = 0; i < siblings.length; i++) {
                        let sibling = siblings[i];
                        if (sibling.nodeType === 1 && sibling.tagName === elem.tagName) {
                            sameTagCount++;
                            if (sibling === elem) {
                                ownPosition = sameTagCount;
                            }
                        }
                    }
                    let tagName = elem.tagName.toLowerCase();
                    let suffix = sameTagCount > 1 ? `[${ownPosition}]` : '';  
                    let parentPath = getElementXPath(elem.parentNode);
                    return `${parentPath}/${tagName}${suffix}`;
                }
                return getElementXPath(element);
            }''', element)
        except:
            return ""


    def _get_xpaths_for_a_tags(self)->dict:
        links = self.page.query_selector_all('a')
        xpath_url_pairs_dict = {}
        for link in links:
            xpath = self._get_xpath(link)
            url = link.get_attribute('href')  # Get the URL from the href attribute
            xpath_url_pairs_dict[xpath] = url

        return xpath_url_pairs_dict

    def _get_xpath_outhtml_by_selector(self, selector)->dict:
        elements = self.page.query_selector_all(selector)
        xpath_html_dict = {}
        for element in elements:
            html_content = self.page.evaluate("element => element.outerHTML", element)
            xpath = self._get_xpath(element)
            xpath_html_dict[xpath]=html_content
        return xpath_html_dict


    def _get_xpaths_all_elements(self)->dict:
        selector = 'input, button, textarea, select'
        elements = self.page.query_selector_all(selector)

        xpath_element_pairs_dict = {}
        for element in elements:
            html_content = self.page.evaluate("element => element.outerHTML", element)
            xpath = self._get_xpath(element)
            xpath_element_pairs_dict[xpath] = html_content
            # xpath_element_pairs.append((xpath, html_content))
        return xpath_element_pairs_dict

    @beartype
    def setup(self, config_file: Path | None = None) -> None:
        # username = "fr3ya_q4spN"
        # password = "Ly19981123=="
        # proxy_server = "http://pr.oxylabs.io:7777"
        # proxy_server = "http://ddc.oxylabs.io:8002"
        # proxy_server = "brd.superproxy.io:33335"
        proxy_server = "brd.superproxy.io:33335"
        # username = "brd-customer-hl_00e5ebe3-zone-datacenter_proxy3-country-gb"
        # username = "brd-customer-hl_00e5ebe3-zone-residential_proxy1"
        username = "brd-customer-hl_00e5ebe3-zone-datacenter_proxy8-country-gb"
        # username = "brd-customer-hl_00e5ebe3-zone-residential_proxy1-country-gb"
        # password = "fl03h601nv53"
        # password = "vp4q11vhwgfm"
        password = "6ttrzyx33hx6"
        # AUTH = 'brd-customer-hl_00e5ebe3-zone-scraping_browser1:fl03h601nv53'
        # SBR_WS_CDP = f'wss://{AUTH}@brd.superproxy.io:9222'

        token = "5cd2eebefb34ac098d896a164b37a0e404deb92106b5dbc5027c33878f0c470b"
        self.context_manager = sync_playwright()
        self.playwright = self.context_manager.__enter__()
        # self.browser = self.playwright.chromium.connect_over_cdp(SBR_WS_CDP)
        ca_cert_path  = "/home/ying/certificate.crt"
        # context = ssl.create_default_context(cafile=ca_cert_path)
        self.browser = self.playwright.chromium.launch(
            headless=self.headless, slow_mo=self.slow_mo,#,
            proxy={'server':proxy_server,
                   'username':username,
                   'password':password
                   },
            # args = [f"--ignore-certificate-errors",
            #         "--use-system-ca-certificates",
            #         "--disable-web-security",
            #         "--ssl-cert-file=/home/ying/certificate.crt",
            #         "--import-certificate=/home/ying/certificate.crt"
            #         ],
        )

        if config_file:
            with open(config_file, "r") as f:
                instance_config = json.load(f)
        else:
            instance_config = {}

        storage_state = instance_config.get("storage_state", None)
        start_url = instance_config.get("start_url", None)
        geolocation = instance_config.get("geolocation", None)
        
        self.context = self.browser.new_context(
            # geolocation={"latitude": 51.5074, "longitude": -0.1278},
            # permissions=["geolocation"],
            # locale="en-GB",\
            ignore_https_errors=True,
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            extra_http_headers={
                # "Authorization": f"Bearer {token}",
                "Accept-Language": "en-GB",
                'Referer': 'https://www.google.com',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            },
            # extra_http_headers={
            #     'Accept-Language': 'en-GB'
            # },
            viewport=self.viewport_size,
            storage_state=storage_state,
            # geolocation={"latitude": 51.5074, "longitude": -0.1278},
            device_scale_factor=1,
        )
        # self.context.set_geolocation({"latitude": 51.5074, "longitude": -0.1278})


        if self.save_trace_enabled:
            self.context.tracing.start(screenshots=True, snapshots=True)
        if start_url:
            start_urls = start_url.split(" |AND| ")
            for url in start_urls:
                page = self.context.new_page()
                client = page.context.new_cdp_session(
                    page
                )  # talk to chrome devtools
                if self.text_observation_type == "accessibility_tree":
                    client.send("Accessibility.enable")
                page.client = client  # type: ignore # TODO[shuyanzh], fix this hackey client
                page.goto(url, wait_until="domcontentloaded")
            # set the first page as the current page
            self.page = self.context.pages[0]   
            self.page.bring_to_front()
        else:
            self.page = self.context.new_page()
            client = self.page.context.new_cdp_session(self.page)
            if self.text_observation_type == "accessibility_tree":
                client.send("Accessibility.enable")
            self.page.client = client  # type: ignore
        time.sleep(2)
        # closes_spans = self._all_close_elements()
        # if len(closes_spans)>0:
        #     self.modal_close(closes_spans)
        
    def modal_close(self, closes_spans):
        visited_xpath = []
        closed_xpath = []
        for _ in closes_spans:
            visited_xpath.append(_)
            try:
                print(_)
                self.page.locator(f"xpath={_}").click(timeout=200)
                closed_xpath.append(_)
            except Exception as e:
                print("Modal Close Exception:",e)
        msg = self._return_msgs()
        return closed_xpath, visited_xpath, msg

    # def continue_step(self, closes_spans):

    def get_page_client(self, page: Page) -> CDPSession:
        return page.client  # type: ignore

    def _get_obs(self) -> dict[str, Observation]:
        
        obs = self.observation_handler.get_observation(
            self.page, self.get_page_client(self.page)
        )
        return obs

    def _get_obs_metadata(self) -> dict[str, ObservationMetadata]:
        metadata = self.observation_handler.get_observation_metadata()
        return metadata

    def _extract_page_links(self, page_content: str)->dict:
        links = self.page.query_selector_all('a')
        text_url_pairs_dict = {}
        for link in links:
            text = link.text_content()
            url = link.get_attribute('href')  # Get the URL from the href attribute
            text_url_pairs_dict[text.strip().lower()] = url
        return text_url_pairs_dict
        
    @beartype
    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, str] | None = None,
    ) -> tuple[dict[str, Observation], dict[str, Any]]:
        """
        Reset the environment.
        :param options: options for the environment. The current supported options are:
            - "storage_state": the storage state of the browser. It is a file path to a json file.
        """
        super().reset(seed=seed, options=options)
        if self.reset_finished:
            self.context_manager.__exit__()

        if options is not None and "config_file" in options:
            config_file = Path(options["config_file"])
            if config_file.exists():
                self.setup(config_file=config_file)
            else:
                raise ValueError(f"Config file {config_file} does not exist.")
        else:
            self.setup()
        self.reset_finished = True

        if self.sleep_after_execution > 0:
            time.sleep(self.sleep_after_execution)

        # start_url = json.load(config_file).get("start_url", None)
        observation = self._get_obs()
        observation_metadata = self._get_obs_metadata()
        # xpaths_for_tags = self._get_xpaths_for_a_tags()
        xpaths_input = self._get_xpaths_all_elements()
        closes_spans = self._all_close_elements()
        popups = self._check_popups()
        iframes = self._find_iframes()
        iframes = self._check_iframe(iframes)
        obs = self._fetch_accessibility_tree(self.page.client)
        page_content = self.page.content()
        text_url_pairs = self._extract_page_links(page_content)
        info = {
            "page": DetachedPage(self.page.url, page_content),
            "fail_error": "",
            "obs": obs,#.page.accessibility.snapshot(interesting_only=False),
            "observation_metadata": observation_metadata,
            "text_url_pairs": text_url_pairs,
            # "xpaths_for_a_tags": xpaths_for_tags,
            "xpaths_input": xpaths_input,
            "closes_ele": closes_spans,
            "popup": popups, # True or False
            "iframe": iframes
        }
        # with open("obs.json", "w") as f:
        #     json.dump(obs,f)
        return (observation, info)

    def save_trace(self, trace_path: str | Path) -> None:
        if self.save_trace_enabled:
            self.context.tracing.stop(path=trace_path)

    def close(self) -> None:
        if self.reset_finished:
            try:
                # Try to close browser and context first if they exist
                if hasattr(self, 'browser'):
                    try:
                        self.browser.close()
                    except:
                        pass
                if hasattr(self, 'context'):
                    try:
                        self.context.close()
                    except:
                        pass
                # Then try to exit the context manager
                self.context_manager.__exit__(None, None, None)
            except Exception as e:
                # Log error but don't raise to ensure cleanup continues
                print(f"Warning: Error during environment cleanup: {str(e)}")

    def step(
        self, action: Action
    ) -> tuple[dict[str, Observation], float, bool, bool, dict[str, Any]]:
        if not self.reset_finished:
            raise RuntimeError("Call reset first before calling step.")
        success = False
        fail_error = ""

        # self.page.evaluate("window.scrollTo(0, document.body.scrollHeight);")

        # # Wait for a second to see the scroll effect
        # # self.page.wait_for_timeout(10)

        # # Scroll back to the top of the page
        # self.page.evaluate("window.scrollTo(0, 0);")
        try:
            # if action["action_type"] == ActionTypes.CLICK:
            print("ACTIONS:",action)
            text_url_pairs = self._extract_page_links(self.page.content())

            self.page = execute_action(
                action,
                text_url_pairs,
                self.page,
                self.context,
                self.observation_handler.action_processor,
            )
            success = True
        except Exception as e:
            fail_error = str(e)

        # hard sleep TODO[shuyanzh] suboptimal, may need to check network
        if self.sleep_after_execution > 0:
            time.sleep(self.sleep_after_execution)
       
        
        # time.sleep(5)
        # observation = self._get_obs()
        # self.page = self.context.pages[-1]
        # self.page.bring_to_front()
        # observation = self._get_obs()
        time.sleep(1)
        # self.page = 
        self.context.pages[-1].bring_to_front()
        self.page = self.context.pages[-1]
        client = self.page.context.new_cdp_session(self.page)
        if self.text_observation_type == "accessibility_tree":
                client.send("Accessibility.enable")
        self.page.client = client
        # print(2)
        observation = self._get_obs()

        observation_metadata = self._get_obs_metadata()
        # xpaths_for_tags = self._get_xpaths_for_a_tags()
        xpaths_input = self._get_xpaths_all_elements()
        closes_spans = self._all_close_elements()
        popups = self._check_popups()
        iframes = self._find_iframes()
        iframes = self._check_iframe(iframes)
        page_content = self.page.content()
        text_url_pairs = self._extract_page_links(page_content)
        info = {
            "page": DetachedPage(self.page.url, self.page.content()),
            "fail_error": fail_error,
            "obs": self._fetch_accessibility_tree(self.page.client),
            "text_url_pairs": text_url_pairs,
            # 'obs': self.page.
            "observation_metadata": observation_metadata,
            'xpaths_input': xpaths_input,
            'closes_ele': closes_spans,
            'popup': popups,
            'iframe': iframes
        }
        msg = (
            observation,
            float(success),  # reward
            False,  # terminated
            False,  # truncated
            info,
        )
        
        return msg