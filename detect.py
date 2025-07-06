#!/usr/bin/env python3

import RPi.GPIO as GPIO
import cv2
import requests
import time
import io
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont


PIR_PIN = 4
#SERVER_URL = "http://192.168.1.4:5000/sensor-input"
SERVER_URL = "http://192.168.1.67:5000/sensor-input"
BACKUP_DIR = "/home/jack/python/room/backup_images"
CAMERA_INDEX = 1
def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIR_PIN, GPIO.IN)

def capture_with_video10():
    """Capture with OpenCV using video10 device"""
    try:
        # Open video10 device specifically
        cap = cv2.VideoCapture(CAMERA_INDEX)
        
        if not cap.isOpened():
            print("Could not open /dev/video10")
            return None, None
        
        # Set camera properties for better performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Give camera time to initialize
        time.sleep(2)
        
        # Try to capture a few frames (sometimes first frames are black)
        ret = False
        frame = None
        for attempt in range(5):
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                break
            time.sleep(0.5)
        
        cap.release()
        
        if ret and frame is not None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Convert frame to PIL image
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            
            # Add timestamp
            draw = ImageDraw.Draw(pil_image)
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # Add text with black background for visibility
            text = timestamp
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Draw black rectangle background
            draw.rectangle([10, 10, 10 + text_width + 10, 10 + text_height + 5], fill=(0, 0, 0))
            # Draw white text
            draw.text((15, 12), text, fill=(255, 255, 255), font=font)
            
            # Convert to bytes
            img_buffer = io.BytesIO()
            pil_image.save(img_buffer, format='JPEG', quality=85)
            img_buffer.seek(0)
            
            return img_buffer.getvalue(), timestamp
        
        return None, None
        
    except Exception as e:
        print(f"video10 capture failed: {e}")
        return None, None



def capture_image_with_timestamp():
    """Capture image using video10 device"""
    print("Attempting to capture image from video10...")
    
    image_data, timestamp = capture_with_video10()
    if image_data:
        print("✓ Captured with video10")
        return image_data, timestamp
    
    print("✗ video10 capture failed")
    return None, None

def send_image_to_server(image_data, timestamp):
    try:
        files = {'image': ('motion_detected.jpg', image_data, 'image/jpeg')}
        data = {'timestamp': timestamp}
        
        response = requests.post(SERVER_URL, files=files, data=data, timeout=10)
        
        if response.status_code == 200:
            print(f"✓ Image sent successfully at {timestamp}")
            return True
        else:
            print(f"✗ Server returned status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to send image: {e}")
        return False

def save_backup_image(image_data, timestamp):
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    filename = f"motion_{timestamp.replace(' ', '_').replace(':', '-')}.jpg"
    filepath = os.path.join(BACKUP_DIR, filename)
    
    try:
        with open(filepath, 'wb') as f:
            f.write(image_data)
        print(f"✓ Backup image saved: {filepath}")
    except Exception as e:
        print(f"✗ Failed to save backup image: {e}")

def test_camera_setup():
    """Test video10 camera setup on startup"""
    print("Testing video10 camera setup...")
    
    # Check if video10 exists
    if os.path.exists("/dev/video10"):
        print("✓ /dev/video10 exists")
    else:
        print("✗ /dev/video10 not found")
        return False
    
    # Test opening video10 with OpenCV
    try:
        cap = cv2.VideoCapture(10)
        if cap.isOpened():
            print("✓ video10 can be opened with OpenCV")
            cap.release()
            return True
        else:
            print("✗ video10 cannot be opened with OpenCV")
            return False
    except Exception as e:
        print(f"✗ Error testing video10: {e}")
        return False

def send_test_alert():
    """Send test alert to server on startup"""
    try:
        data = {'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'test': 'startup'}
        response = requests.post(SERVER_URL.replace('sensor-input', 'security-status'), timeout=5)
        print(f"✓ Server connection test: {response.status_code}")
    except Exception as e:
        print(f"✗ Server connection test failed: {e}")

def main():
    setup_gpio()
    print("="*50)
    print("Motion Detector Starting...")
    print("="*50)
    
    # Run diagnostics
    camera_ok = test_camera_setup()
    if not camera_ok:
        print("Camera test failed. Please check video10 device.")
        print("Make sure your camera is connected and mapped to video10.")
        return
    
    send_test_alert()
    
    print("="*50)
    print("Monitoring GPIO 4 for motion...")
    print("Press Ctrl+C to stop")
    print("="*50)
    
    consecutive_failures = 0
    max_failures = 5
    
    try:
        while True:
            if GPIO.input(PIR_PIN):
                print(f"\n🚨 Motion detected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}!")
                
                # Try to capture image
                image_data, timestamp = capture_image_with_timestamp()
                
                if image_data:
                    consecutive_failures = 0  # Reset failure counter
                    
                    # Try to send to server
                    success = send_image_to_server(image_data, timestamp)
                    
                    if not success:
                        print("Transfer failed, saving backup image...")
                        save_backup_image(image_data, timestamp)
                else:
                    consecutive_failures += 1
                    print(f"Camera capture failed ({consecutive_failures}/{max_failures})")
                    
                    if consecutive_failures >= max_failures:
                        print("Too many consecutive camera failures. Sending alert without image...")
                        try:
                            data = {
                                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                'alert': 'motion_detected_no_image',
                                'error': 'camera_failure'
                            }
                            requests.post(SERVER_URL.replace('sensor-input', 'security-status'), 
                                        json=data, timeout=5)
                        except:
                            pass
                        consecutive_failures = 0  # Reset counter
                
                # Wait before detecting again
                print("Waiting 5 seconds before next detection...")
                time.sleep(5)
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
    finally:
        GPIO.cleanup()
        print("GPIO cleaned up. Goodbye!")

if __name__ == "__main__":
    main()
