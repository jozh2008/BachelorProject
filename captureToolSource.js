const puppeteer = require('puppeteer');

async function captureToolSource() {
  const url = process.argv[2];
  const browser = await puppeteer.launch({
    headless: "new", // Set to true for headless mode
  });
  const page = await browser.newPage();
  await page.goto(url);

  // Wait for the dropdown to be visible
  await page.waitForSelector('.tool-dropdown');

  // Click on the dropdown toggle button
  await page.click('.tool-dropdown button');

  // Wait for some time to ensure the dropdown menu has fully expanded
  await page.waitForTimeout(1000);

  // Click on the "View Tool source" option
  await page.click('.dropdown-item:has(svg.fa-eye)');

  // Wait for some time to ensure JavaScript has loaded on the new page
  await page.waitForTimeout(5000);

  // Capture the content of the new page
  const content = await page.content();

  await browser.close();

  // Return the captured content
  return content;
}

// Call the function and handle the return value
captureToolSource()
  .then((capturedContent) => {
    console.log(capturedContent)
    // Do something with the captured content if needed
  })
  .catch((error) => {
    console.error('Error capturing content:', error);
  });
