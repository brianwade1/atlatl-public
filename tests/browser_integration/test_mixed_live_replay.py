"""S18-F: native live messages and original replay viewer share exact oracles."""

from contextlib import ExitStack

import pytest
from playwright.sync_api import expect

from tests.support.browser_helpers import checked_page
from tests.support.episode_assertions import read_replay
from tests.support.integration_server import running_server, read_report
from tests.support.live_play import real_page, down, expose
from tests.support.mixed_episode import episode
from tests.support.playback import load_page, assert_observation, snapshot

pytestmark = [pytest.mark.browser, pytest.mark.integration, pytest.mark.protocol]


def test_mixed_city_combat_fog_live_and_replay(browser, http_base_url, tmp_path):
    scenario, actions, states, transcripts = episode()
    with running_server(tmp_path, socket=True, scenario=scenario) as child:
        port = child.ready()["port"]
        with ExitStack() as stack:
            pages = {}
            for role in ("blue", "red"):
                context = stack.enter_context(browser.new_context())
                page = real_page(context, port)
                stack.enter_context(checked_page(page))
                page.goto(http_base_url + "/browser/play.html")
                expose(page)
                expect(page.locator("#" + role)).to_be_enabled()
                page.locator("#" + role).click()
                pages[role] = page
            for role, page in pages.items():
                page.wait_for_function("received.length === 2")
                assert page.evaluate("received") == transcripts[role][:2]
                assert_observation(page, transcripts[role][1]["observation"]["units"])
            for index, action in enumerate(actions):
                page = pages[states[index]["status"]["onMove"]]
                expect(page.locator("#end-move")).to_be_enabled()
                if action["type"] == "pass":
                    page.locator("#end-move").click()
                else:
                    down(page, action.get("source", action.get("mover")))
                    down(page, "mark " + action.get("target", action.get("destination")))
                for role, observer_page in pages.items():
                    observer_page.wait_for_function("n => received.length === n", arg=index+3)
                    assert observer_page.evaluate("received") == transcripts[role][:index+3]
                    assert_observation(observer_page, transcripts[role][index+2]["observation"]["units"])
            for page in pages.values():
                expect(page.locator("#onmove")).to_have_text("terminal")
                expect(page.locator("#score")).to_have_text("-84")
                expect(page.locator("#end-move")).to_be_disabled()
            child.wait()
    report = read_report(tmp_path)
    assert report["state"] == states[-1]
    assert report["reps_done"] == 1
    blue_hidden = [record["observation"]["units"][6]["hex"] for record in transcripts["blue"][1:]]
    assert blue_hidden == ["fog"] * 3 + ["hex-0-6"] * 4 + ["fog"] * 3
    for role in ("blue", "red"):
        path = tmp_path / (role + ".js")
        assert read_replay(path) == transcripts[role]
        with browser.new_context() as context:
            page = context.new_page()
            with checked_page(page):
                load_page(page, http_base_url, path.read_text(encoding="utf-8"))
                # Initialization consumes parameters; Step consumes observations.
                for record in transcripts[role][1:]:
                    page.locator("#step").click()
                    assert_observation(page, record["observation"]["units"])
                terminal = snapshot(page)
                assert page.evaluate("Playback.next_message()") is False
                page.locator("#step").click()
                assert snapshot(page) == terminal
