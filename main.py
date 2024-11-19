from djitellopy import Tello
import time

# Initialize the Tello drone
tello = Tello()

# Connect to the Tello drone
tello.connect()

# Check the battery level
battery_level = tello.get_battery()
print(f"Battery level: {battery_level}%")
if battery_level < 20:
    print("Battery too low for takeoff. Please charge the drone.")
    exit()

# Enable mission pad detection
tello.enable_mission_pads()
tello.set_mission_pad_detection_direction(0)  # 0: both, 1: downward, 2: forward

# Takeoff
tello.takeoff()
time.sleep(2)

# Helper function to average mission pad coordinates over 2 seconds
def get_average_pad_coordinates(duration=1):
    x_values, y_values, z_values = [], [], []
    start_time = time.time()
    while time.time() - start_time < duration:
        pad_x = tello.get_mission_pad_distance_x()
        pad_y = tello.get_mission_pad_distance_y()
        pad_z = tello.get_mission_pad_distance_z()

        # Only include valid coordinates in the average
        if pad_x != -100 and pad_y != -100 and pad_z != -100:
            x_values.append(pad_x)
            y_values.append(pad_y)
            z_values.append(pad_z)

        time.sleep(0.1)  # Sample every 0.1 seconds

    if not x_values or not y_values or not z_values:
        print("No valid mission pad data collected.")
        return None, None, None

    # Compute integer averages
    avg_x = int(sum(x_values) / len(x_values))
    avg_y = int(sum(y_values) / len(y_values))
    avg_z = int(sum(z_values) / len(z_values))

    return avg_x, avg_y, avg_z

# Start detecting mission pad
print("Looking for a mission pad...")
while True:
    pad_id = tello.get_mission_pad_id()

    if pad_id != -1:  # Mission pad detected
        print(f"Mission pad {pad_id} detected. Averaging coordinates for 2 seconds...")
        avg_x, avg_y, avg_z = get_average_pad_coordinates()

        if avg_x is None or avg_y is None or avg_z is None:
            print("Failed to calculate average mission pad coordinates. Retrying...")
            continue

        print(f"Averaged pad position - X: {avg_x}, Y: {avg_y}, Z: {avg_z}")

        # Stage 1: Fly above the mission pad
        print(f"Flying above mission pad at relative position - X: {avg_x}, Y: {avg_y}, Z: 40 (constant above)")
        speed = 30  # Speed in cm/s
        try:
            # Fly to the pad with a constant Z offset
            # Apply overshoot multiplier for X and Y
            overshoot_m = 0.85
            adjusted_x = round(-1 * avg_x * overshoot_m)
            adjusted_y = round(-1 * avg_y * overshoot_m)
            adjusted_z = round(-1 * avg_z + 10)  # Z offset remains constant

            # Fly to the overshoot-adjusted position
            tello.go_xyz_speed(adjusted_x, adjusted_y, adjusted_z, speed)
            print("Flying to position above the mission pad...")
            time.sleep(2)  # Allow time to reach the position

            # Rescan the mission pad for fine adjustments
            print("Rescanning for fine adjustments...")
            pad_id = tello.get_mission_pad_id()
            if pad_id != -1:
                avg_x, avg_y, avg_z = get_average_pad_coordinates()

                if avg_x is None or avg_y is None or avg_z is None:
                    print("Failed to calculate fine adjustment coordinates. Retrying...")
                    continue

                print(f"Fine adjustment position - X: {avg_x}, Y: {avg_y}, Z: {avg_z}")

                # Stage 2: Perform minor adjustments and descend
                print("Making minor adjustments and descending...")
                # Apply undershoot multiplier for X and Y
                undershoot_m = 1.2
                adjusted_x = round(-1 * avg_x * undershoot_m)
                adjusted_y = round(-1 * avg_y * undershoot_m)
                adjusted_z = round(-1 * avg_z)  # Descend without additional offset

                # Fly to the undershoot-adjusted position
                tello.go_xyz_speed(adjusted_x, adjusted_y, adjusted_z, 10)
                print("Descending to the mission pad...")
                time.sleep(1)  # Allow time for adjustments and descent

                # Land once the drone is aligned
                print("Landing on the mission pad...")
                tello.land()
                break  # Exit the loop after landing
            else:
                print("Mission pad lost during fine adjustments. Retrying...")
                continue

        except Exception as e:
            print(f"An error occurred during the flight: {e}")
            tello.land()
            break
    else:
        print("No mission pad detected. Searching...")
        time.sleep(0.5)

# Disable mission pad detection
tello.disable_mission_pads()

# Disconnect the drone
tello.end()
