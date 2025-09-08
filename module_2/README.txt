Checked robots.txt on https://www.thegradcafe.com/robots.txt
As of 9/7/25, general scraping allowed except /cgi-bin/ and /index-ad-test.php. Screenshot included as screenshot.jpg

Note: Local LLM pass included (llm_hosting/app.py). Tested with sample_data.json.
Output (llm_extend_applicant_data.json) is generated but empty on some runs due to
model environment. Primary scraper/cleaner pipeline validated separately.
Note: Installed certifi to resolve macOS SSL verification issues with urllib3.
This is not required for all environments, but included here for compatibility.