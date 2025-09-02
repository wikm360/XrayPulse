#!/usr/bin/env python3
"""
Xray Config Monitor
A comprehensive monitoring system for Xray configurations
"""

import os
import json
import base64
import requests
import subprocess
import platform
import time
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import queue
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ConfigFetcher:
    """Fetches and processes subscription configurations"""
    
    def __init__(self, config_dir: str = "./configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.subscription_url = None
        
    def set_subscription_url(self, url: str):
        """Set the subscription URL"""
        self.subscription_url = url
        # Save URL for future use
        with open(self.config_dir / "subscription.txt", "w") as f:
            f.write(url)
    
    def load_subscription_url(self) -> Optional[str]:
        """Load saved subscription URL"""
        url_file = self.config_dir / "subscription.txt"
        if url_file.exists():
            with open(url_file, "r") as f:
                return f.read().strip()
        return None
    
    def fetch_configs(self) -> bool:
        """Fetch configurations from subscription URL"""
        if not self.subscription_url:
            self.subscription_url = self.load_subscription_url()
            if not self.subscription_url:
                logger.error("No subscription URL configured")
                return False
        
        try:
            logger.info(f"Fetching configs from: {self.subscription_url}")
            
            # Fetch subscription data
            headers = {"User-Agent": "XrayMonitor/1.0"}
            response = requests.get(self.subscription_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Decode base64 content
            content = response.text.strip()
            if not content:
                logger.error("Empty response from subscription")
                return False
                
            try:
                decoded = base64.b64decode(content).decode('utf-8')
            except Exception as e:
                logger.warning(f"Base64 decode failed, trying direct parse: {e}")
                decoded = content
            
            # Parse configurations
            configs = [c.strip() for c in decoded.split('\n') if c.strip()]
            
            if not configs:
                logger.error("No configurations found in subscription")
                return False
            
            logger.info(f"Found {len(configs)} configurations")
            
            # Convert and save each config
            saved_count = 0
            config_list = {}
            
            for idx, config_line in enumerate(configs):
                try:
                    # Import convert module
                    from convert import convert
                    
                    # Convert to Xray JSON format
                    config_json, config_name = convert(config_line)
                    
                    if config_json and config_name != "False":
                        # Fix URL-encoded emoji names
                        try:
                            import urllib.parse
                            # Decode URL-encoded characters (like %F0%9F%87%AB)
                            config_name = urllib.parse.unquote(config_name)
                        except:
                            pass
                        
                        # Save config file
                        config_file = self.config_dir / f"config_{idx}.json"
                        with open(config_file, "w", encoding="utf-8") as f:
                            f.write(config_json)
                        
                        config_list[f"config_{idx}"] = config_name
                        saved_count += 1
                        logger.info(f"Saved config {idx}: {config_name}")
                    
                except Exception as e:
                    logger.error(f"Error processing config {idx}: {e}")
                    continue
            
            # Save config list
            with open(self.config_dir / "config_list.json", "w", encoding="utf-8") as f:
                json.dump(config_list, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Successfully saved {saved_count} configurations")
            return saved_count > 0
            
        except requests.RequestException as e:
            logger.error(f"Network error fetching subscription: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False

class PingTester:
    """Tests ping/delay for each configuration"""
    
    def __init__(self, config_dir: str = "./configs", results_file: str = "./ping_results.json"):
        self.config_dir = Path(config_dir)
        self.results_file = Path(results_file)
        self.xray_path = self._find_xray_binary()
        self.test_interval = 300  # 5 minutes default
        self.running = False
        self.thread = None
        self.results = {}
        self.test_queue = queue.Queue()
        
    def _find_xray_binary(self) -> str:
        """Find Xray binary path"""
        system = platform.system().lower()
        if system == "windows":
            xray_path = "./core/win/xray.exe"
        elif system == "linux":
            xray_path = "./core/linux/xray"
        elif system == "darwin":
            xray_path = "./core/macos/xray"
        else:
            xray_path = "xray"
        
        if not Path(xray_path).exists():
            logger.warning(f"Xray binary not found at {xray_path}, using system xray")
            return "xray"
        
        return xray_path
    
    def test_single_config(self, config_file: Path, config_name: str) -> float:
        """Test a single configuration and return delay in ms"""
        import random
        import tempfile
        
        try:
            
            # Read and modify config for testing
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Use random port to avoid conflicts
            test_port = random.randint(20000, 30000)
            
            # Update ports in config
            for inbound in config.get('inbounds', []):
                if inbound.get('tag') == 'socks':
                    inbound['port'] = test_port
                elif inbound.get('tag') == 'api':
                    inbound['port'] = test_port + 1
            
            # Write temporary config
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                json.dump(config, tmp, indent=2)
                tmp_config_path = tmp.name
            
            # Start Xray process
            creation_flags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            process = subprocess.Popen(
                [self.xray_path, '-config', tmp_config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creation_flags
            )
            
            # Wait for Xray to start
            time.sleep(3)  # Increased wait time
            
            # Test connection through proxy
            start_time = time.time()
            try:
                # Try both socks5 and socks5h
                proxies = {
                    'http': f'socks5h://127.0.0.1:{test_port}',
                    'https': f'socks5h://127.0.0.1:{test_port}'
                }
                
                response = requests.get(
                    'http://gstatic.com/generate_204',
                    proxies=proxies,
                    timeout=10
                )
                
                if response.status_code in [204, 200]:
                    delay = (time.time() - start_time) * 1000  # Convert to ms
                    logger.info(f"Config {config_name}: {delay:.2f}ms")
                else:
                    delay = 9999  # High value for failed connections
                    logger.warning(f"Config {config_name}: Failed (status {response.status_code})")
                    
            except Exception as e:
                    delay = 9999
                    logger.warning(f"Config {config_name}: Connection failed - {e}")
                # Try alternative test method
                # try:
                #     import socket
                #     import struct
                    
                #     # Simple SOCKS5 handshake test
                #     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                #     sock.settimeout(5)
                #     sock.connect(('127.0.0.1', test_port))
                    
                #     # Send SOCKS5 greeting
                #     sock.send(b'\x05\x01\x00')
                #     response = sock.recv(2)
                    
                #     if response == b'\x05\x00':
                #         # SOCKS5 server is responding
                #         delay = (time.time() - start_time) * 1000
                #         logger.info(f"Config {config_name}: {delay:.2f}ms (socket test)")
                #     else:
                #         delay = 9999
                #         logger.warning(f"Config {config_name}: SOCKS handshake failed")
                    
                #     sock.close()
                    
                # except Exception as sock_error:
                #     delay = 9999
                #     logger.warning(f"Config {config_name}: Connection failed - {sock_error}")
            
            # Cleanup
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            
            try:
                os.unlink(tmp_config_path)
            except:
                pass
            
            return delay
            
        except Exception as e:
            logger.error(f"Error testing config {config_name}: {e}")
            return 9999
    
    def run_tests(self):
        """Run ping tests for all configurations"""
        try:
            # Load config list
            config_list_file = self.config_dir / "config_list.json"
            if not config_list_file.exists():
                logger.error("Config list not found")
                return
            
            with open(config_list_file, 'r', encoding='utf-8') as f:
                config_list = json.load(f)
            
            if not config_list:
                logger.warning("No configurations to test")
                return
            
            logger.info(f"Starting ping tests for {len(config_list)} configurations")
            
            # Test each configuration
            test_results = {}
            timestamp = datetime.now().isoformat()
            
            for config_id, config_name in config_list.items():
                config_file = self.config_dir / f"{config_id}.json"
                
                if not config_file.exists():
                    logger.warning(f"Config file not found: {config_file}")
                    continue
                
                # Fix URL-encoded names for logging
                try:
                    import urllib.parse
                    display_name = urllib.parse.unquote(config_name)
                except:
                    display_name = config_name
                
                delay = self.test_single_config(config_file, display_name)
                
                test_results[config_name] = {
                    "delay": delay,
                    "timestamp": timestamp,
                    "status": "online" if delay < 9999 else "offline"
                }
                
                # Update global results
                self.results[config_name] = test_results[config_name]
                
                # Save intermediate results
                self.save_results()
                
                # Small delay between tests
                time.sleep(1)
            
            logger.info("Ping tests completed")
            
        except Exception as e:
            logger.error(f"Error during ping tests: {e}")
    
    def save_results(self):
        """Save test results to file"""
        try:
            # Add metadata
            output = {
                "last_update": datetime.now().isoformat(),
                "total_configs": len(self.results),
                "results": self.results
            }
            
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Results saved to {self.results_file}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def start(self, interval: int = 300):
        """Start periodic testing"""
        self.test_interval = interval
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(f"Started ping testing with {interval}s interval")
    
    def stop(self):
        """Stop testing"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        logger.info("Stopped ping testing")
    
    def _run_loop(self):
        """Main testing loop"""
        while self.running:
            try:
                self.run_tests()
                
                # Wait for next interval
                for _ in range(self.test_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in test loop: {e}")
                time.sleep(10)

class MonitorController:
    """Main controller for the monitoring system"""
    
    def __init__(self):
        self.fetcher = ConfigFetcher()
        self.tester = PingTester()
        self.web_server = None
        
    def setup(self):
        """Interactive setup for subscription URL"""
        print("\n" + "="*50)
        print("  Xray Config Monitor Setup")
        print("="*50 + "\n")
        
        # Try to load existing URL
        existing_url = self.fetcher.load_subscription_url()
        
        if existing_url:
            print(f"Found existing subscription URL: {existing_url}")
            use_existing = input("Use this URL? (y/n): ").strip().lower()
            if use_existing == 'y':
                self.fetcher.subscription_url = existing_url
                return True
        
        # Get new URL
        print("\nEnter your subscription URL:")
        url = input("> ").strip()
        
        if not url:
            print("No URL provided")
            return False
        
        self.fetcher.set_subscription_url(url)
        return True
    
    def run(self):
        """Run the monitoring system"""
        try:
            # Setup
            if not self.setup():
                return
            
            print("\n" + "="*50)
            print("  Starting Monitoring System")
            print("="*50 + "\n")
            
            # Fetch initial configs
            print("Fetching configurations...")
            if not self.fetcher.fetch_configs():
                print("Failed to fetch configurations")
                return
            
            # Start ping testing
            interval = 300  # 5 minutes
            print(f"\nStarting ping tests (interval: {interval}s)...")
            self.tester.start(interval)
            
            # Run initial test immediately
            print("Running initial tests...")
            self.tester.run_tests()
            
            # Start web interface in separate process
            print("\nStarting web interface...")
            self.start_web_interface()
            
            print("\n" + "="*50)
            print("  Monitoring System Running")
            print("="*50)
            print("\nPress Ctrl+C to stop\n")
            
            # Keep running
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\nStopping monitoring system...")
            self.stop()
            print("Goodbye!")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            self.stop()
    
    def start_web_interface(self):
        """Start the web interface in a separate process"""
        import multiprocessing
        from web_interface import run_web_server
        
        self.web_server = multiprocessing.Process(
            target=run_web_server,
            args=("127.0.0.1", 7070),
            daemon=True
        )
        self.web_server.start()
        print(f"Web interface available at: http://127.0.0.1:7070")
    
    def stop(self):
        """Stop all components"""
        self.tester.stop()
        if self.web_server:
            self.web_server.terminate()

def main():
    """Main entry point"""
    controller = MonitorController()
    controller.run()

if __name__ == "__main__":
    main()