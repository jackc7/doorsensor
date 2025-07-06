#!/usr/bin/env python3

import cv2
import time
import io
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

def test_c950_camera(index):
    """Test the C950 camera at specific index"""
    print(f"\n{'='*50}")
    print(f"Testing C950 camera at /dev/video{index}")
    print(f"{'='*50}")
    
    try:
        cap = cv2.VideoCapture(index)
        
        if not cap.isOpened():
            print(f"✗ Cannot open /dev/video{index}")
            return False
        
        # Set camera properties like in your original code
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Get actual properties
        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"Camera properties:")
        print(f"  Resolution: {actual_width}x{actual_height}")
        print(f"  FPS: {fps}")
        
        # Give camera time to initialize (like your original code)
        print("Initializing camera...")
        time.sleep(2)
        
        # Try to capture frames (like your original code)
        successful_captures = 0
        for attempt in range(5):
            print(f"  Capture attempt {attempt + 1}/5...")
            ret, frame = cap.read()
            
            if ret and frame is not None and frame.size > 0:
                successful_captures += 1
                print(f"    ✓ Success! Frame size: {frame.shape}")
                
                # Test the timestamp overlay like your original code
                if attempt == 0:  # Only do this once
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(frame_rgb)
                    
                    draw = ImageDraw.Draw(pil_image)
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
                    except:
                        font = ImageFont.load_default()
                    
                    text = timestamp
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    
                    # Draw timestamp
                    draw.rectangle([10, 10, 10 + text_width + 10, 10 + text_height + 5], fill=(0, 0, 0))
                    draw.text((15, 12), text, fill=(255, 255, 255), font=font)
                    
                    # Convert to JPEG like your original code
                    img_buffer = io.BytesIO()
                    pil_image.save(img_buffer, format='JPEG', quality=85)
                    img_size = len(img_buffer.getvalue())
                    
                    print(f"    ✓ Timestamp overlay added")
                    print(f"    ✓ JPEG conversion successful ({img_size} bytes)")
            else:
                print(f"    ✗ Failed to capture frame")
            
            time.sleep(0.5)
        
        cap.release()
        
        print(f"\nResults: {successful_captures}/5 successful captures")
        
        if successful_captures >= 4:
            print(f"✅ /dev/video{index} works excellent for C950!")
            return True
        elif successful_captures >= 2:
            print(f"⚠️  /dev/video{index} works but has some issues")
            return True
        else:
            print(f"❌ /dev/video{index} has serious problems")
            return False
            
    except Exception as e:
        print(f"✗ Error testing /dev/video{index}: {e}")
        return False

def main():
    print("C950 Camera Detection Test")
    print("This will test both video0 and video1 for your C950 camera")
    
    # Test both possible indices for the C950
    video0_works = test_c950_camera(0)
    video1_works = test_c950_camera(1)
    
    print(f"\n{'='*50}")
    print("SUMMARY:")
    print(f"{'='*50}")
    
    if video0_works and video1_works:
        print("✅ Both /dev/video0 and /dev/video1 work!")
        print("   Recommendation: Use CAMERA_INDEX = 0 (typically more reliable)")
    elif video0_works:
        print("✅ Use CAMERA_INDEX = 0 in your main script")
    elif video1_works:
        print("✅ Use CAMERA_INDEX = 1 in your main script")
    else:
        print("❌ Neither index works. Check camera connection:")
        print("   - Unplug and replug the C950 camera")
        print("   - Run: lsusb | grep -i camera")
        print("   - Check dmesg for errors: dmesg | tail -20")

if __name__ == "__main__":
    main()