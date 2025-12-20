"""
LinkedIn Profile Analysis MCP Server - Direct Search Extraction
Extracts ALL data directly from search results page
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright, Page

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
app = FastMCP("LinkedIn Profile Analyzer")

# Global browser state
_browser_context = {}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def wait_for_page_load(page: Page, timeout: int = 10000):
    """Wait for page to be fully loaded"""
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception as e:
        logger.warning(f"Network idle timeout: {e}")
        await asyncio.sleep(2)

async def scroll_page_gradually(page: Page, num_scrolls: int = 5):
    """Gradually scroll down the page to trigger lazy loading"""
    try:
        for i in range(num_scrolls):
            await page.evaluate(f'window.scrollTo(0, document.body.scrollHeight * {(i + 1) / num_scrolls})')
            await asyncio.sleep(0.5)
        # Scroll back to top
        await page.evaluate('window.scrollTo(0, 0)')
        await asyncio.sleep(0.5)
    except Exception as e:
        logger.warning(f"Scroll error: {e}")

# ============================================================================
# MCP TOOLS
# ============================================================================

@app.tool()
async def login_linkedin(email: str, password: str) -> Dict[str, Any]:
    """
    Log into LinkedIn with provided credentials
    
    Args:
        email: LinkedIn account email
        password: LinkedIn account password
        
    Returns:
        Status message and session ID
    """
    try:
        logger.info(f"Initiating LinkedIn login for {email}")
        
        playwright = await async_playwright().start()
        headless_mode = os.getenv("HEADLESS", "true").lower() == "true"
        browser = await playwright.chromium.launch(
            headless=headless_mode,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        await page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded')
        await wait_for_page_load(page)
        
        await page.fill('input[name="session_key"]', email)
        await page.fill('input[name="session_password"]', password)
        await page.click('button[type="submit"]')
        
        # Wait for navigation to complete
        await asyncio.sleep(3)
        
        # Check for successful login indicators
        try:
            # Wait for either feed or global nav
            await page.wait_for_selector('.global-nav__me-photo, .feed-identity-module, #global-nav', timeout=10000)
            is_logged_in = True
        except:
            is_logged_in = False

        current_url = page.url
        if is_logged_in or 'feed' in current_url:
            logger.info("LinkedIn login successful")
            
            session_id = f"session_{id(browser)}"
            _browser_context[session_id] = {
                'playwright': playwright,
                'browser': browser,
                'context': context,
                'page': page
            }
            
            return {
                "success": True,
                "message": "Successfully logged into LinkedIn",
                "session_id": session_id
            }
        else:
            # Take screenshot of failure
            debug_dir = Path("debug_screenshots")
            debug_dir.mkdir(exist_ok=True)
            await page.screenshot(path=str(debug_dir / f"login_fail_{id(browser)}.png"))
            
            await browser.close()
            await playwright.stop()
            return {
                "success": False,
                "message": f"Login failed. Current URL: {current_url}. Check debug_screenshots."
            }
            
    except Exception as e:
        logger.error(f"LinkedIn login failed: {e}")
        return {
            "success": False,
            "message": f"Login error: {str(e)}"
        }


@app.tool()
async def extract_all_search_profiles_with_images(
    session_id: str,
    search_url: str
) -> Dict[str, Any]:
    """
    Extract ALL profiles from LinkedIn search results by clicking through ALL pages.
    Uses multiple selector strategies to ensure all profiles are captured.
    
    Args:
        session_id: Session ID from login_linkedin
        search_url: LinkedIn search results URL
        
    Returns:
        success, list of ALL profiles (rank, name, url, location, imageUrl), count, message
    """
    import random
    try:
        if session_id not in _browser_context:
            return {
                "success": False,
                "profiles": [],
                "message": "Invalid session_id. Please login first."
            }

        page = _browser_context[session_id]['page']

        logger.info(f"🔍 Navigating to search results: {search_url}")
        await page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
        await wait_for_page_load(page)

        # Initial scroll to load all profiles on first page
        await asyncio.sleep(2)
        await scroll_page_gradually(page, num_scrolls=3)
        await asyncio.sleep(1)

        collected = []
        seen_urls = set()
        pages_processed = 0

        logger.info(f"📜 Starting multi-page extraction with enhanced selectors")

        async def extract_from_dom():
            """Enhanced extraction with multiple selector strategies"""
            return await page.evaluate('''() => {
                const results = [];
                const seenInThisPage = new Set();
                
                // Strategy 1: Find all list items that could be search results
                const selectors = [
                    'li.reusable-search__result-container',
                    'div.entity-result',
                    'div[class*="search-result"]',
                    'li[class*="search"]',
                    'div[data-chameleon-result-urn]'
                ];
                
                const allContainers = [];
                selectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        if (!allContainers.includes(el)) {
                            allContainers.push(el);
                        }
                    });
                });
                
                console.log(`Found ${allContainers.length} potential profile containers`);
                
                allContainers.forEach((container) => {
                    try {
                        // Find profile link - try multiple approaches
                        let profileLink = container.querySelector('a[href*="/in/"]');
                        
                        if (!profileLink) {
                            // Try finding any link within the container that looks like a profile
                            const allLinks = container.querySelectorAll('a');
                            for (const link of allLinks) {
                                if (link.href && link.href.includes('/in/')) {
                                    profileLink = link;
                                    break;
                                }
                            }
                        }
                        
                        if (!profileLink || !profileLink.href) return;
                        
                        // Clean the URL
                        let url = profileLink.href.split('?')[0].replace(/\/$/, '');
                        if (!url || !url.includes('/in/')) return;
                        
                        // Skip duplicates within this extraction
                        if (seenInThisPage.has(url)) return;
                        seenInThisPage.add(url);
                        
                        // Extract name - try multiple selectors
                        let name = null;
                        const nameSelectors = [
                            'span.entity-result__title-text span[aria-hidden="true"]',
                            'span[aria-hidden="true"]',
                            'div.entity-result__title-text',
                            'a[href*="/in/"] span:first-child',
                            '.entity-result__title-line'
                        ];
                        
                        for (const selector of nameSelectors) {
                            const nameElement = container.querySelector(selector);
                            if (nameElement && nameElement.textContent.trim()) {
                                name = nameElement.textContent.trim();
                                // Clean up name (remove extra whitespace, "View X's profile" etc)
                                name = name.replace(/View .* profile/i, '').trim();
                                if (name) break;
                            }
                        }
                        
                        // Extract location - try multiple selectors
                        let location = null;
                        const locationSelectors = [
                            '.entity-result__secondary-subtitle',
                            'div[class*="secondary-subtitle"]',
                            'div[class*="location"]',
                            '.entity-result__summary'
                        ];
                        
                        for (const selector of locationSelectors) {
                            const locationElement = container.querySelector(selector);
                            if (locationElement && locationElement.textContent.trim()) {
                                location = locationElement.textContent.trim();
                                break;
                            }
                        }
                        
                        // Extract image - try multiple approaches
                        let imageUrl = null;
                        const imageSelectors = [
                            'img.presence-entity__image',
                            'img[class*="presence"]',
                            'img.EntityPhoto',
                            'img[class*="entity-result"]',
                            'img'
                        ];
                        
                        for (const selector of imageSelectors) {
                            const imageElement = container.querySelector(selector);
                            if (imageElement && imageElement.src && 
                                !imageElement.src.includes('data:image') && 
                                !imageElement.src.includes('static')) {
                                imageUrl = imageElement.src;
                                break;
                            }
                        }
                        
                        // Extract position - try multiple selectors
                        let position = null;
                        const positionSelectors = [
                            '.entity-result__primary-subtitle',
                            'div.entity-result__primary-subtitle',
                            'div[class*="primary-subtitle"]',
                            'div.t-14.t-black.t-normal'
                        ];

                        for (const selector of positionSelectors) {
                            const positionElement = container.querySelector(selector);
                            if (positionElement && positionElement.textContent.trim()) {
                                position = positionElement.textContent.trim();
                                break;
                            }
                        }

                        results.push({
                            name: name,
                            url: url,
                            location: location,
                            imageUrl: imageUrl,
                            position: position
                        });

                        
                    } catch (e) {
                        console.error('Error extracting profile:', e);
                    }
                });
                
                console.log(`Extracted ${results.length} profiles from page`);
                return results;
            }''')

        # Extract from first page
        logger.info(f"📄 Extracting profiles from page 1...")
        profiles_data = await extract_from_dom()
        logger.info(f"Page 1: Found {len(profiles_data)} candidate profiles")
        pages_processed += 1

        # Process initial results
        for p in profiles_data:
            url = p.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                collected.append({
                    "rank": len(collected) + 1,
                    "name": p.get("name") or "Unknown",
                    "url": url,
                    "location": p.get("location"),
                    "imageUrl": p.get("imageUrl"),
                    "position": p.get("position")
                })


        logger.info(f"✅ Page 1 complete: {len(collected)} unique profiles collected")

        # Pagination loop
        button_selector = 'button.artdeco-pagination__button--next'
        max_pages = 1  # Safety limit
        
        while pages_processed < max_pages:
            try:
                # Check if next button exists and is enabled
                button = await page.query_selector(button_selector)
                
                if not button:
                    logger.info("🛑 Next button not found - reached end of results")
                    break
                
                is_disabled = await button.evaluate('(el) => el.disabled || el.getAttribute("aria-disabled") === "true"')
                
                if is_disabled:
                    logger.info("🛑 Next button is disabled - reached end of results")
                    break
                
                # Click next button
                logger.info(f"🔘 Loading page {pages_processed + 1}...")
                
                try:
                    await button.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)
                    await button.click()
                except Exception as e:
                    logger.warning(f"Click failed, trying JS: {e}")
                    await page.evaluate(f'''() => {{
                        const btn = document.querySelector('{button_selector}');
                        if (btn && !btn.disabled) btn.click();
                    }}''')
                
                # Wait for page load and new content
                await asyncio.sleep(2.5 + random.random() * 1.5)
                await wait_for_page_load(page, timeout=10000)
                
                # Scroll to load all profiles on this page
                await scroll_page_gradually(page, num_scrolls=3)
                await asyncio.sleep(1)
                
                pages_processed += 1
                
                # Extract from new page
                logger.info(f"📄 Extracting profiles from page {pages_processed}...")
                new_profiles = await extract_from_dom()
                logger.info(f"Page {pages_processed}: Found {len(new_profiles)} candidate profiles")
                
                new_added = 0
                for p in new_profiles:
                    url = p.get("url")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        collected.append({
                            "rank": len(collected) + 1,
                            "name": p.get("name") or "Unknown",
                            "url": url,
                            "location": p.get("location"),
                            "imageUrl": p.get("imageUrl"),
                            "position": p.get("position")
                        })

                        new_added += 1
                
                logger.info(f"✅ Page {pages_processed}: Added {new_added} new profiles (Total: {len(collected)})")
                
                # If no new profiles found, we might be done
                if new_added == 0:
                    logger.warning("No new profiles found on this page - might be at the end")
                    # Double check if there's a next button
                    button = await page.query_selector(button_selector)
                    if not button:
                        break
                
                await asyncio.sleep(1 + random.random() * 1.0)
                
            except Exception as e:
                logger.error(f"Error during pagination: {e}")
                await asyncio.sleep(2.0)
                break

        # Final results
        if len(collected) > 0:
            logger.info(f"🎉 Extraction complete!")
            logger.info(f"📊 Total profiles: {len(collected)} from {pages_processed} pages")
            
            # Show sample
            if collected:
                sample = collected[0]
                logger.info(f"Sample: {sample.get('name')} | {sample.get('location')} | Image: {'✓' if sample.get('imageUrl') else '✗'}")
            
            return {
                "success": True,
                "profiles": collected,
                "count": len(collected),
                "pages_processed": pages_processed,
                "message": f"Successfully extracted {len(collected)} profiles from {pages_processed} pages"
            }
        else:
            # Debug: save page state
            debug_dir = Path("debug_screenshots")
            debug_dir.mkdir(exist_ok=True)
            
            screenshot_path = debug_dir / f"no_profiles_{session_id}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            
            html_path = debug_dir / f"no_profiles_{session_id}.html"
            html_content = await page.content()
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.error(f"❌ No profiles extracted. Debug files saved to: {debug_dir}")
            
            return {
                "success": False,
                "profiles": [],
                "count": 0,
                "pages_processed": pages_processed,
                "message": f"No profiles found. Check debug files: {screenshot_path}"
            }

    except Exception as e:
        logger.error(f"Failed to extract profiles: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "profiles": [],
            "count": 0,
            "message": f"Error: {str(e)}"
        }

@app.tool()
async def extract_education_data(
    session_id: str,
    profile_url: str
) -> Dict[str, Any]:
    """
    Extract raw education data from a LinkedIn profile.
    Returns education entries as structured data for LLM analysis.
    
    Args:
        session_id: Session ID from login_linkedin
        profile_url: Full LinkedIn profile URL
        
    Returns:
        Dictionary with raw education data (school, degree, dates)
    """
    import random
    
    try:
        if session_id not in _browser_context:
            return {
                "success": False,
                "message": "Invalid session_id. Please login first.",
                "education": []
            }

        page = _browser_context[session_id]['page']
        
        logger.info(f"🎓 Navigating to profile: {profile_url}")
        await page.goto(profile_url, wait_until='domcontentloaded', timeout=30000)
        await wait_for_page_load(page)
        
        # Wait for initial content to load
        await asyncio.sleep(2 + random.random())
        
        # Scroll down gradually to trigger lazy loading of education section
        logger.info("Scrolling to load education section...")
        for i in range(5):
            scroll_amount = 600 * (i + 1)
            await page.evaluate(f'window.scrollTo(0, {scroll_amount})')
            await asyncio.sleep(0.8 + random.random() * 0.5)
        
        # Scroll to bottom to ensure everything is loaded
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(1.5)
        
        # Scroll back up slightly to education section
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.5)')
        await asyncio.sleep(1)
        
        # Extract education data - ONLY from Education section
        education_data = await page.evaluate('''() => {
            const educations = [];

            console.log("=== Extracting Education CLEAN ===");

            // Locate the EDUCATION SECTION
            let eduSection = document.querySelector('section[id*="education"]');

            if (!eduSection) {
                const allSections = document.querySelectorAll("section");
                for (const sec of allSections) {
                    const h2 = sec.querySelector("h2");
                    if (h2 && h2.textContent.toLowerCase().includes("education")) {
                        eduSection = sec;
                        break;
                    }
                }
            }

            if (!eduSection) {
                console.log("❌ No education section found");
                return [];
            }

            // Extract each education item cleanly
            const items = eduSection.querySelectorAll(
                "div.display-flex.flex-row.justify-space-between"
            );

            items.forEach((block) => {
                try {
                    let school = null;
                    let degree = null;
                    let date_range = null;

                    // SCHOOL: First aria-hidden span
                    const schoolEl = block.querySelector('span[aria-hidden="true"]');
                    if (schoolEl) school = schoolEl.textContent.trim();

                    // DEGREE: nested visually-hidden span inside .t-14.t-normal
                    const degreeEl = block.querySelector(
                        "span.t-14.t-normal span.visually-hidden"
                    );
                    if (degreeEl) degree = degreeEl.textContent.trim();

                    // DATE RANGE
                    const dateEl = block.querySelector("span.pvs-entity__caption-wrapper");
                    if (dateEl) date_range = dateEl.textContent.trim();

                    // Add only if meaningful (ignore empty garbage entries)
                    if (school || degree || date_range) {
                        educations.push({
                            school: school || null,
                            degree: degree || null,
                            date_range: date_range || null
                        });
                    }

                } catch (err) {
                    console.log("Error parsing education block", err);
                }
            });

            return educations;
        }''')


        
        logger.info(f"📚 Found {len(education_data)} education entries")
        
        return {
            "success": True,
            "education": education_data,
            "message": f"Extracted {len(education_data)} education entries"
        }
        
    except Exception as e:
        logger.error(f"Failed to extract education: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "education": [],
            "message": f"Error: {str(e)}"
        }


@app.tool()
async def close_browser(session_id: str) -> Dict[str, Any]:
    """Close browser and cleanup resources"""
    try:
        if session_id not in _browser_context:
            return {"success": False, "message": "Invalid session_id"}
        
        context_data = _browser_context[session_id]
        
        try:
            await context_data['context'].close()
        except:
            pass
        
        try:
            await context_data['browser'].close()
        except:
            pass
        
        try:
            await context_data['playwright'].stop()
        except:
            pass
        
        del _browser_context[session_id]
        
        logger.info(f"Browser session closed: {session_id}")
        
        return {"success": True, "message": "Browser closed"}
        
    except Exception as e:
        logger.error(f"Error closing browser: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}


if __name__ == "__main__":
    logger.info("Starting LinkedIn Profile Analyzer MCP Server")
    app.run()