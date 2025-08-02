"""Frontend tests for the Medical Imaging GUI."""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

@pytest.mark.frontend
class TestMedicalImagingGUI:
    """Test cases for the Medical Imaging GUI."""

    @pytest.fixture(scope="class")
    def browser(self):
        """Set up browser for testing."""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()

    def test_frontend_loads(self, browser, test_metrics: "TestMetrics"):
        """Test that the frontend loads successfully."""
        start_time = time.time()
        browser.get("http://localhost:3000")
        
        try:
            WebDriverWait(browser, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "medical-image-viewer"))
            )
            load_time = time.time() - start_time
            test_metrics.add_metric("frontend_load_time", load_time)
            assert load_time < 10.0, "Frontend took too long to load"
            
        except TimeoutException:
            test_metrics.add_metric("frontend_load_time", -1)
            pytest.fail("Frontend failed to load within timeout")

    def test_viewer_tools(self, browser, test_metrics: "TestMetrics"):
        """Test that the viewer tools are working."""
        browser.get("http://localhost:3000")
        
        tools = ["Pan", "Zoom", "WindowLevel", "Length", "Reset"]
        found_tools = []
        
        for tool in tools:
            try:
                button = browser.find_element(By.XPATH, f"//button[contains(text(), '{tool}')]")
                button.click()
                found_tools.append(tool)
                time.sleep(0.5)  # Allow time for tool activation
            except Exception as e:
                print(f"Tool {tool} not found or not clickable: {e}")
        
        test_metrics.add_metric(
            "tool_availability",
            len(found_tools) / len(tools)
        )
        
        assert len(found_tools) == len(tools), "Not all viewer tools are available"

    def test_file_upload(self, browser, test_metrics: "TestMetrics"):
        """Test file upload functionality."""
        browser.get("http://localhost:3000")
        
        try:
            # Find and interact with file upload
            upload_input = browser.find_element(By.CSS_SELECTOR, "input[type='file']")
            upload_input.send_keys("/path/to/test/image.dcm")
            
            # Wait for processing indicator
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "processing-indicator"))
            )
            
            # Wait for viewer to update
            WebDriverWait(browser, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "image-loaded"))
            )
            
            test_metrics.add_metric("upload_success", 1.0)
        except Exception as e:
            test_metrics.add_metric("upload_success", 0.0)
            pytest.fail(f"File upload failed: {e}")

    def test_responsive_layout(self, browser, test_metrics: "TestMetrics"):
        """Test responsive layout at different screen sizes."""
        browser.get("http://localhost:3000")
        
        window_sizes = [
            (1920, 1080),  # Desktop
            (1366, 768),   # Laptop
            (768, 1024),   # Tablet
            (375, 812)     # Mobile
        ]
        
        layout_scores = []
        
        for width, height in window_sizes:
            browser.set_window_size(width, height)
            time.sleep(1)  # Allow time for layout adjustment
            
            try:
                # Check if viewer maintains proper layout
                viewer = browser.find_element(By.CLASS_NAME, "medical-image-viewer")
                toolbar = browser.find_element(By.CLASS_NAME, "toolbar")
                
                layout_scores.append(
                    viewer.is_displayed() and toolbar.is_displayed()
                )
            except Exception:
                layout_scores.append(False)
        
        test_metrics.add_metric(
            "responsive_score",
            sum(layout_scores) / len(window_sizes)
        )
        
        assert all(layout_scores), "Layout not responsive at all screen sizes"
