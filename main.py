from djitellopy import Tello
import time

# Constants
MOVEMENT_THRESHOLD = 20  # Minimum displacement (cm) required to initiate movement
SPEED = 30  # Movement speed in cm/s
NO_MOVEMENT_TIMEOUT = 7  # Time in seconds before initiating landing due to no movement
home_pad = 4
rover_pad = 3

def find_pad(tello, pad):
    print("Searching for mission pad...")
    base_speed = 10  # Speed in cm/s for controlled movement
    base_distance = 40  # Starting movement distance
    tello.move_up(30)
    # Define the movement pattern
    directions = [
        (base_distance, base_distance),  # Initial corner: Move diagonally
        (-2 * base_distance, 0),  # Move left (relative)
        (0, -2 * base_distance),  # Move up
        (2 * base_distance, 0),  # Move right
        (0, 2 * base_distance),  # Move down
    ]

    for step, (dx, dy) in enumerate(directions, start=1):
        pad_id = tello.get_mission_pad_id()
        if pad_id  == pad:  # If a pad is detected, stop searching
            print(f"Mission pad {pad_id} detected during search at step {step}.")
            return True  # Indicate that a pad was found
        else:
            print(f'no mission pad found')
        # Perform the relative movement
        print(f"Step {step}: Moving X: {dx}, Y: {dy}, Z: 0...")
        try:
            tello.go_xyz_speed(dx, dy, 0, base_speed)
            time.sleep(1)  # Allow time for the movement to complete
        except Exception as e:
            print(f"Error during pad search movement at step {step}: {e}")

    print("Mission pad not found after completing the search pattern.")
    return False  # Indicate that no pad was found

def get_average_pad_coordinates(duration=2):
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
def centre_pad(tello, pad):
    try:
        print("Continuing to move forward slowly...")
        while True:
            pad_id = tello.get_mission_pad_id()
            if pad_id == -1:  # No mission pad detected
                print("No mission pad detected. Initiating find_pad()...")
                if find_pad(tello, pad):  # Try to find a mission pad
                    print("Mission pad found during find_pad(). Returning to centre_pad sequence.")
                    continue  # Re-check the pad after finding it
                else:
                    print("Mission pad not found after search. Retrying...")
                    time.sleep(1)  # Pause before retrying
                    continue

            # Mission pad detected
            print(f"Mission pad {pad_id} detected. Averaging coordinates for 2 seconds...")
            avg_x, avg_y, avg_z = get_average_pad_coordinates()

            if avg_x is None or avg_y is None or avg_z is None:
                print("Failed to calculate average mission pad coordinates. Retrying...")
                continue

            print(f"Averaged pad position - X: {avg_x}, Y: {avg_y}, Z: {avg_z}")

            # Stage 1: Fly above the mission pad
            print(f"Flying above mission pad at relative position - X: {avg_x}, Y: {avg_y}, Z: 40 (constant above)")

            # Calculate overshoot-adjusted position
            overshoot_m = 1
            adjusted_x = round(avg_x * overshoot_m)
            adjusted_y = round(avg_y * overshoot_m)
            adjusted_z = round(-1 * avg_z + 50)  # Z offset remains constant

            # Move the drone to the overshoot-adjusted position
            try: 
                tello.go_xyz_speed(adjusted_x, adjusted_y, adjusted_z, 10)
            except Exception as e:
                print(f'out of range failed at x: {adjusted_x}, y: {adjusted_y}, z: {adjusted_z}')

            print("Flying to position above the mission pad...")
            time.sleep(2)  # Allow time to reach the position
            break  # Exit after successful positioning

        # Ensure the drone stops moving
        tello.send_rc_control(0, 0, 0, 0)

    except Exception as e:
        print(f"An error occurred: {e}")
        tello.land()  # Emergency landing in case of a critical error

    finally:
        # Ensure the drone stops moving
        tello.send_rc_control(0, 0, 0, 0)


# Initialize and connect to the Tello drone
tello = Tello()
tello.connect()

# Enable mission pad detection
tello.enable_mission_pads()
tello.set_mission_pad_detection_direction(0)  # 0: detect both directions

# Print battery level
print(f'Battery level: {tello.get_battery()}%')
MOVEMENT_THRESHOLD = 20  # Minimum displacement (cm) required to initiate movement
CENTERING_THRESHOLD = 5  # Threshold for centering on a pad
SPEED = 30  # Movement speed in cm/s
NO_MOVEMENT_TIMEOUT = 7  # Time in seconds before initiating landing due to no movement

def initiate_landing_sequence(tello, pad):
    no_pad_start_time = None  # Track the time when no pad is detected
    current_height = tello.get_height()  # Get the current height of the drone
    if (current_height < 100):
        tello.move_up(20)
    while True:
        pad_id = tello.get_mission_pad_id()
        if pad_id == -1:  # No pad detected
            if no_pad_start_time is None:
                no_pad_start_time = time.time()  # Start timer when pad is not detected
            elif time.time() - no_pad_start_time >= 2:  # Check if 2 seconds have passed
                print("No mission pad detected for 2 seconds. Activating find_pad()...")
                if find_pad(tello, pad):  # If pad is found during the search
                    print("Mission pad found. Returning to landing sequence.")
                    no_pad_start_time = None  # Reset the timer
                    continue  # Continue the landing sequence
                else:
                    print("Mission pad not found after search. Retrying...")
                    no_pad_start_time = None  # Reset the timer
            else:
                print("No mission pad detected. Waiting for 2 seconds...")
            time.sleep(0.5)  # Prevent tight looping
            continue

        # Pad detected; reset the no-pad timer
        no_pad_start_time = None

        print(f"Mission pad {pad_id} detected. Averaging coordinates for 2 seconds...")
        avg_x, avg_y, avg_z = get_average_pad_coordinates(2.5)

        if avg_x is None or avg_y is None or avg_z is None:
            print("Failed to calculate average mission pad coordinates. Retrying...")
            continue

        print(f"Averaged pad position - X: {avg_x}, Y: {avg_y}, Z: {avg_z}")

        # Stage 1: Fly above the mission pad
        print(f"Flying above mission pad at relative position - X: {avg_x}, Y: {avg_y}, Z: 40 (constant above)")

        try:
            # Fly to the pad with a constant Z offset
            overshoot_m = 1
            adjusted_x = round(avg_x * overshoot_m)
            adjusted_y = round(avg_y * overshoot_m)
            adjusted_z = round(max(-1 * avg_z - 10, -30))  # Z offset remains constant

            tello.go_xyz_speed(adjusted_x, adjusted_y, adjusted_z, 10)
            time.sleep(1)
            avg_x, avg_y, avg_z = get_average_pad_coordinates(0.3)
            print('double check: x:', avg_x, "y:", avg_y)
            while True:  # Retry loop for fine adjustments
                pad_id = tello.get_mission_pad_id()
                if pad_id == -1:
                    print("Mission pad lost during fine adjustments. Retrying...")
                    time.sleep(1)
                    break  # Break inner retry loop to re-detect pad at top-level loop

                avg_x, avg_y, avg_z = get_average_pad_coordinates(1)

                if avg_x is None or avg_y is None or avg_z is None:
                    print("Failed to calculate fine adjustment coordinates. Retrying...")
                    continue

                print(f"Fine adjustment position - X: {avg_x}, Y: {avg_y}, Z: {avg_z}")

                # Stage 2: Perform minor adjustments and descend
                print("Making minor adjustments and descending...")
                undershoot_m = 1.3
                adjusted_x = round(avg_x * undershoot_m)
                adjusted_y = round(avg_y * undershoot_m)
                adjusted_z = round(-1 * avg_z)  # Descend without additional offset
                if (adjusted_z < -20):
                    tello.move_down(20)
                tello.go_xyz_speed(adjusted_x, adjusted_y, 0, 10)
                print("Descending to the mission pad...")
                time.sleep(1)  # Allow time for adjustments and descent

                # Land once the drone is aligned
                if abs(avg_x) < 10 and abs(avg_y) < 10 and tello.height() < 50:  # Within centering threshold
                    print("Close to mission pad. Landing directly.")
                    tello.land()
                    return  # Exit the entire function
                break  # Break inner retry loop if fine adjustment is successful

        except Exception as e:
            print(f"An error occurred during the flight: {e}")
            tello.land()
            return


# Takeoff
tello.takeoff()
flip_mode = True
#step1
try:
    #state 1


    tello.go_xyz_speed(110, -80, 0, 50)
    initiate_landing_sequence(tello, rover_pad)
    time.sleep(8)
    tello.takeoff()
    tello.go_xyz_speed(-110, 80, 0, 50)
    time.sleep(2)
    if flip_mode:
        centre_pad(tello, home_pad)
        time.sleep(1)
        tello.move_right(20)
        time.sleep(1)
        tello.move_down(30)
        time.sleep(1)
        tello.flip_left()
        time.sleep(1)
        tello.move_right(20)
        tello.move_up(20)
        time.sleep(2)
        centre_pad(tello, home_pad)
    else:
        initiate_landing_sequence(tello, home_pad)
        time.sleep(5)
        tello.takeoff()
        time.sleep(3)
        centre_pad(tello, home_pad)
    time.sleep(2)

    # #state 2

    tello.rotate_clockwise(90)
    time.sleep(1)
    tello.go_xyz_speed(+160, -120, 0, 50)
    initiate_landing_sequence(tello, rover_pad)
    # tello.land()
    time.sleep(8)
    tello.takeoff()
    time.sleep(2)
    tello.go_xyz_speed(-160, +120, 0, 50)
    time.sleep(3)
    tello.rotate_counter_clockwise(90)
    time.sleep(3)
    if flip_mode:
        centre_pad(tello, home_pad)
        time.sleep(1)
        tello.move_right(20)
        time.sleep(1)
        tello.move_down(30)
        time.sleep(1)
        tello.flip_left()
        time.sleep(1)
        tello.move_right(20)
        tello.move_up(20)
        centre_pad(tello, home_pad)
        time.sleep(1)
    else:
        initiate_landing_sequence(tello, home_pad)
        time.sleep(7)
        tello.takeoff()
        time.sleep(4)
        centre_pad(tello, home_pad)
    time.sleep(5)


    #state 3
    time.sleep(2)
    tello.rotate_clockwise(180)
    time.sleep(6)
    tello.go_xyz_speed(120, -85, 0, 50)
    time.sleep(1)
    tello.move_up(20)
    time.sleep(1)
    initiate_landing_sequence(tello, rover_pad)
    time.sleep(8)
    tello.takeoff()
    tello.go_xyz_speed(-120, 85, 0, 50)
    time.sleep(1)
    tello.rotate_clockwise(180)
    time.sleep(1)
    if flip_mode:
        centre_pad(tello, home_pad)
        time.sleep(1)
        tello.move_right(20)
        time.sleep(1)
        tello.move_down(30)
        time.sleep(1)
        tello.flip_left()
        time.sleep(1)
        tello.move_right(20)
        tello.move_up(20)
        time.sleep(1)
        initiate_landing_sequence(tello, home_pad)
    else:
        initiate_landing_sequence(tello, home_pad)
        time.sleep(1)
    tello.takeoff()
    #state 4
    time.sleep(1)
    tello.takeoff()
    time.sleep(1)
    tello.rotate_clockwise(180)
    time.sleep(1)
    tello.go_xyz_speed(-170,120,0,10)
    time.sleep(1)
    initiate_landing_sequence(tello, rover_pad)
    time.sleep(7)
    tello.takeoff()
    time.sleep(1)
    tello.go_xyz_speed(170,-120,0,10)
    time.sleep(1)
    tello.rotate_clockwise(180)
    time.sleep(1)
    if flip_mode:
        centre_pad(tello, home_pad)
        time.sleep(1)
        tello.move_right(20)
        time.sleep(1)
        tello.move_down(30)
        time.sleep(1)
        tello.flip_left()
        time.sleep(1)
        tello.move_right(20)
        tello.move_up(20)
        time.sleep(1)
        initiate_landing_sequence(tello, home_pad)
    else:
        initiate_landing_sequence(tello, home_pad)
        time.sleep(1)
    




finally:
    tello.disable_mission_pads()
    tello.end()
