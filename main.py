from djitellopy import Tello
import time

# Initialize the Tello drone
tello = Tello()

try:
    # Connect to the Tello drone
    tello.connect()

    # Check the battery level
    battery_level = tello.get_battery()
    print(f"Battery level: {battery_level}%")
    if battery_level < 20:
        print("Battery too low for takeoff. Please charge the drone.")
        raise Exception("Low Battery")

    # Enable mission pad detection
    tello.enable_mission_pads()
    tello.set_mission_pad_detection_direction(0)  # 0: both, 1: downward, 2: forward

    # Takeoff
    tello.takeoff()
    time.sleep(2)

    # Wait until a mission pad is detected
    pad_id = tello.get_mission_pad_id()
    while pad_id == -1:  # -1 means no pad detected
        print("Searching for mission pad...")
        pad_id = tello.get_mission_pad_id()
        time.sleep(0.5)
    
    print(f"Mission pad {pad_id} detected")

    # Define target altitude for landing approach
    z_target = 30       # Desired altitude (in cm) above the mission pad
    min_altitude = 10   # Minimum allowed altitude
    max_altitude = 40   # Maximum allowed altitude
    tolerance_xy = 20   # Tolerance for x and y positioning
    tolerance_z = 10    # Tolerance for altitude
    max_z_step = 20     # Maximum descent (or ascent) per command in cm

    while True:
        # Check if the Mission Pad is detected
        pad_id = tello.get_mission_pad_id()
        if pad_id == -1:
            print("Mission pad lost, waiting to reacquire...")
            time.sleep(0.5)
            continue  # Skip to the next loop iteration until the pad is detected again

        # Get the x, y, z distances to the pad
        pad_x = tello.get_mission_pad_distance_x()
        pad_y = tello.get_mission_pad_distance_y()
        pad_z = tello.get_mission_pad_distance_z()

        # Ignore invalid coordinates (-100, -100, -100)
        if pad_x == -100 or pad_y == -100 or pad_z == -100:
            print("Invalid coordinates detected, retrying...")
            time.sleep(0.5)
            continue

        print(f"Relative position to pad - X: {pad_x}, Y: {pad_y}, Z: {pad_z}")

        # Adjust z value to gradually approach the target altitude
        z_movement = z_target - pad_z  # Calculate the desired z movement
        if abs(z_movement) > max_z_step:
            z_movement = max_z_step if z_movement > 0 else -max_z_step  # Limit to max_z_step

        # Enforce altitude limits (10 cm to 40 cm)
        target_altitude = pad_z + z_movement
        if target_altitude < min_altitude:
            z_movement = min_altitude - pad_z  # Adjust to minimum altitude
        elif target_altitude > max_altitude:
            z_movement = max_altitude - pad_z  # Adjust to maximum altitude

        # Check if the drone is within tolerance in all axes
        if abs(pad_x) <= tolerance_xy and abs(pad_y) <= tolerance_xy and abs(pad_z - z_target) <= tolerance_z:
            print("Centered over the mission pad and at target altitude.")
            break  # Exit the loop once centered and at target altitude

        # Ensure at least one of x, y, or z is outside the -20 to 20 range
        if not (abs(pad_x) <= tolerance_xy and abs(pad_y) <= tolerance_xy and abs(pad_z - z_target) <= tolerance_z):
            # Move to the calculated position relative to the pad at a defined speed
            speed = 20
            tello.go_xyz_speed_mid(pad_x, pad_y, 30, speed, pad_id)
        
        # Small delay to allow for positioning adjustments
        time.sleep(1)

    # Land once aligned over the pad
    tello.land()

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Ensure mission pad detection is disabled after landing
    try:
        tello.disable_mission_pads()
    except Exception as disable_error:
        print(f"Error disabling mission pads: {disable_error}")

    # Disconnect the drone
    try:
        tello.end()
    except Exception as disconnect_error:
        print(f"Error disconnecting from Tello: {disconnect_error}")
