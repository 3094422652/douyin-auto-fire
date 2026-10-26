from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from app.browser import open_douyin, open_private_messages
from app.config import load_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
LOGGER = logging.getLogger("verify_douyin")


async def main() -> None:
    settings = load_settings()
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Starting Douyin Contact Verification via Proxy...")
    print("=" * 60)

    async with open_douyin(settings) as session:
        page = session.page
        print("[1] Navigating to Douyin Chat page...")
        await open_private_messages(page)
        print("[OK] Douyin Chat page opened successfully.")

        # Wait 5 seconds for sidebar conversation list to fully mount
        await page.wait_for_timeout(5000)

        # 1. Full page overview screenshot
        p1 = artifacts_dir / "01_chat_full_page.png"
        await page.screenshot(path=str(p1), full_page=False)
        print(f"[OK] Captured initial chat page screenshot: {p1}")

        # 2. Extract and inspect all items in left conversation list
        items = page.locator(
            '[data-e2e="conversation-item"], [class*="conversationConversationItem"], [class*="ConversationItem"], [class*="conversation-item"], [class*="chat-item"]'
        )
        count = await items.count()
        print(f"\n>>> Total conversation items found in sidebar: {count} <<<")
        for i in range(count):
            item = items.nth(i)
            txt = await item.inner_text()
            lines = [l.strip() for l in txt.splitlines() if l.strip()]
            header = lines[0] if lines else "Empty"
            print(f"  [Item #{i+1}] Header: \"{header}\" | Full: {lines}")

        # 3. Check for keywords directly in page text
        page_text = await page.evaluate("() => document.body.innerText")
        has_wang = "汪鹏" in page_text
        has_ye = "无敌大野猪" in page_text
        print("\n--- Page Keyword Check ---")
        print(f"  '汪鹏' present in DOM: {has_wang}")
        print(f"  '无敌大野猪' present in DOM: {has_ye}")

        # 4. Click item #3 if present to inspect active chat window
        if count >= 3:
            print("\n[2] Clicking on Item #3 in conversation list...")
            await items.nth(2).click()
            await page.wait_for_timeout(3000)
            p_c3 = artifacts_dir / "02_item3_chat_opened.png"
            await page.screenshot(path=str(p_c3), full_page=False)
            print(f"[OK] Captured item #3 chat window: {p_c3}")

            header_loc = page.locator('[class*="RightPanelHeader"], [class*="chatHeader"], [class*="ChatHeader"]').first
            if await header_loc.count():
                htxt = await header_loc.inner_text()
                print(f"  Active Chat Header: {htxt.splitlines()}")

        # 5. Search for '汪鹏'
        search_inputs = (
            'input[placeholder*="搜索"]',
            'input[placeholder="搜索"]',
            '[role="textbox"][placeholder*="搜索"]',
            'input[aria-label*="搜索"]',
        )
        search_box = None
        for sel in search_inputs:
            loc = page.locator(sel).first
            if await loc.count() and await loc.is_visible():
                search_box = loc
                print(f"\n[3] Found search input with selector: {sel}")
                break

        if search_box:
            print("Searching for '汪鹏' in search box...")
            await search_box.click()
            await search_box.fill("")
            await search_box.fill("汪鹏")
            await page.wait_for_timeout(3500)

            p_s1 = artifacts_dir / "03_search_wangpeng.png"
            await page.screenshot(path=str(p_s1), full_page=False)
            print(f"[OK] Captured search screenshot: {p_s1}")

            s_items = page.locator('[class*="SearchPanelitembox"], [class*="SearchPanelitem-box"], [class*="SearchPanelitem_box"]')
            s_count = await s_items.count()
            print(f"Search results count for '汪鹏': {s_count}")
            for j in range(s_count):
                stxt = await s_items.nth(j).inner_text()
                print(f"  Result #{j+1}: {stxt.splitlines()}")

            print("\n[4] Searching for '无敌大野猪' in search box...")
            await search_box.click()
            await search_box.fill("")
            await search_box.fill("无敌大野猪")
            await page.wait_for_timeout(3500)

            p_s2 = artifacts_dir / "04_search_wudidayezhu.png"
            await page.screenshot(path=str(p_s2), full_page=False)
            print(f"[OK] Captured search screenshot: {p_s2}")

            s_items2 = page.locator('[class*="SearchPanelitembox"], [class*="SearchPanelitem-box"], [class*="SearchPanelitem_box"]')
            s_count2 = await s_items2.count()
            print(f"Search results count for '无敌大野猪': {s_count2}")
            for j in range(s_count2):
                stxt = await s_items2.nth(j).inner_text()
                print(f"  Result #{j+1}: {stxt.splitlines()}")

    print("\n" + "=" * 60)
    print("Verification finished successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
