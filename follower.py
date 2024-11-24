from djitellopy import Tello
import time

# Constants
MOVEMENT_THRESHOLD = 20  # Minimum displacement (cm) required to initiate movement
SPEED = 30  # Movement speed in cm/s
NO_MOVEMENT_TIMEOUT = 7  # Time in seconds before initiating landing due to no movement
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
def pre_flip(tello):
    try:


        print("Continuing to move forward slowly...")
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

                # Calculate overshoot-adjusted position
                overshoot_m = 0.8
                adjusted_x = round(avg_x * overshoot_m)
                adjusted_y = round(avg_y * overshoot_m)
                adjusted_z = round(-1 * avg_z + 50)  # Z offset remains constant

                # Move the drone to the overshoot-adjusted position
                tello.go_xyz_speed(adjusted_x, adjusted_y, adjusted_z, speed)
                print("Flying to position above the mission pad...")
                time.sleep(2)  # Allow time to reach the position
                break  # Exit after successful positioning

            # Slowly move forward
            time.sleep(0.5)  # Pause to prevent constant polling

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

def initiate_landing_sequence(tello):
    while True:
        pad_id = tello.get_mission_pad_id()
        if pad_id == -1:  # If no pad is detected, keep retrying
            print("No mission pad detected. Searching...")
            time.sleep(1)
            continue

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
            overshoot_m = 1
            adjusted_x = round(avg_x * overshoot_m)
            adjusted_y = round(avg_y * overshoot_m)
            adjusted_z = round(-1 * avg_z + 10)  # Z offset remains constant

            tello.go_xyz_speed(adjusted_x, adjusted_y, adjusted_z, speed)
            print("Flying to position above the mission pad...")
            time.sleep(1)  # Allow time to reach the position

            # Rescan the mission pad for fine adjustments
            print("Rescanning for fine adjustments...")
            while True:  # Retry loop for fine adjustments
                pad_id = tello.get_mission_pad_id()
                if pad_id == -1:
                    print("Mission pad lost during fine adjustments. Retrying...")
                    time.sleep(1)
                    break  # Break inner retry loop to re-detect pad at top-level loop

                avg_x, avg_y, avg_z = get_average_pad_coordinates()

                if avg_x is None or avg_y is None or avg_z is None:
                    print("Failed to calculate fine adjustment coordinates. Retrying...")
                    continue

                print(f"Fine adjustment position - X: {avg_x}, Y: {avg_y}, Z: {avg_z}")

                # Stage 2: Perform minor adjustments and descend
                print("Making minor adjustments and descending...")
                undershoot_m = 1.3
                adjusted_x = round(avg_x * undershoot_m)
                adjusted_y = round(avg_y * undershoot_m)
                adjusted_z = round(-1 * avg_z + 10)  # Descend without additional offset

                tello.go_xyz_speed(adjusted_x, adjusted_y, adjusted_z, 10)
                print("Descending to the mission pad...")
                time.sleep(1)  # Allow time for adjustments and descent

                # Land once the drone is aligned
                if abs(avg_x) < 8 and abs(avg_y) < 8:  # Within centering threshold
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

#step1
try:
    #state 1


    tello.go_xyz_speed(110, -80, 0, 50)
    initiate_landing_sequence(tello)
    time.sleep(8)
    tello.takeoff()
    tello.go_xyz_speed(-110, 80, 0, 50)
    time.sleep(1)
    pre_flip(tello)
    tello.flip_left()
    time.sleep(1)
    tello.move_right(40)
    tello.move_up(20)

    pre_flip(tello)


    #state 2

    tello.rotate_clockwise(90)
    tello.go_xyz_speed(+160, -120, 0, 50)
    initiate_landing_sequence(tello)
    # tello.land()
    time.sleep(8)
    tello.takeoff()
    tello.go_xyz_speed(-160, +120, 0, 50)
    time.sleep(1)
    pre_flip(tello)
    tello.flip_left()

    #state 3
    tello.rotate_clockwise(90)
    tello.go_xyz_speed(100, -70, 0, 50)
    tello.go_xyz_speed(100, -70, 0, 50)
    initiate_landing_sequence(tello)
    time.sleep(8)
    tello.takeoff()
    tello.go_xyz_speed(-110, 80, 0, 50)
    time.sleep(1)
    pre_flip(tello)
    tello.flip_left()
    tello.land()







finally:
    tello.disable_mission_pads()
    tello.end()
# # Counter to track current stop
# stop_counter = 0


# """#State = 0, going from centre to intial position, if this is in position, when the rover passes, we can detect
# #(BUT, it might be better to run this code after rover pass), because placing the bridge might be harder than anticipated, and it could take up time
# tello.move_forward(110)
# tello.rotate_clockwise(90)
# tello.move_forward(60)

# #State = 1, the first stop, we landed once
# tello.move_right(100)
# #we should have visual cue of pad 2-> move to location of pad 2
# tello.move_back(50)
# #we should have visual cue of pad 1, thats base, move to location of pad 1
# tello.move_down(20) #descend for more accurate drop
# tello.flip_back() #the payload is dropped here
# tello.move_up(20)
# tello.move_forward(50)
# #Visual cue of pad 2, move to pad 2 location.
# tello.move_forward(100)
# tello.rotate_clockwise(90)
# tello.move_forward(70)
# #Visual cue of pad 9 again 
# """

# # Track last movement time
# last_movement_time = time.time()



# try:
#     while True:
#         # Get the current mission pad ID
#         pad_id = tello.get_mission_pad_id()

#         if pad_id != -1:  # Mission pad detected
#             # Get distances from the mission pad
#             pad_x = tello.get_mission_pad_distance_x()
#             pad_y = tello.get_mission_pad_distance_y()

#             # Only move if both X and Y exceed the threshold
#             if abs(pad_x) > MOVEMENT_THRESHOLD or abs(pad_y) > MOVEMENT_THRESHOLD:
#                 print(f"Moving to pad position - X: {pad_x}, Y: {pad_y}")
#                 tello.go_xyz_speed(pad_x, pad_y, 0, SPEED)
#                 last_movement_time = time.time()  # Update last movement time
#             else:
#                 print(f"Within threshold. Staying in position - X: {pad_x}, Y: {pad_y}")
#         else:
#             print("No mission pad detected. Searching...")
#             tello.send_rc_control(0, 0, 0, 0)

#         # Check if no movement has been made for the timeout period
#         if time.time() - last_movement_time > NO_MOVEMENT_TIMEOUT:
#             print("No movement detected for 7 seconds. Initiating landing sequence...")
#             pad_id = tello.get_mission_pad_id()

#             if pad_id != -1:  # Mission pad detected
#                 tello.move_down(40)
#                 print(f"Mission pad {pad_id} detected. Averaging coordinates for 2 seconds...")
#                 avg_x, avg_y, avg_z = get_average_pad_coordinates()

#                 if avg_x is None or avg_y is None or avg_z is None:
#                     print("Failed to calculate average mission pad coordinates. Retrying...")
#                     continue

#                 print(f"Averaged pad position - X: {avg_x}, Y: {avg_y}, Z: {avg_z}")

#                 # Stage 1: Fly above the mission pad
#                 print(f"Flying above mission pad at relative position - X: {avg_x}, Y: {avg_y}, Z: 40 (constant above)")
#                 speed = 30  # Speed in cm/s
#                 try:
#                     # Fly to the pad with a constant Z offset
#                     # Apply overshoot multiplier for X and Y
#                     overshoot_m = 1
#                     adjusted_x = round(avg_x * overshoot_m)
#                     adjusted_y = round(avg_y * overshoot_m)
#                     adjusted_z = round(-1*avg_z +10)  # Z offset remains constant

#                     # Fly to the overshoot-adjusted position
#                     tello.go_xyz_speed(adjusted_x, adjusted_y, adjusted_z, speed)
#                     print("Flying to position above the mission pad...")
#                     time.sleep(2)  # Allow time to reach the position

#                     # Rescan the mission pad for fine adjustments
#                     print("Rescanning for fine adjustments...")
#                     pad_id = tello.get_mission_pad_id()
#                     if pad_id != -1:
#                         avg_x, avg_y, avg_z = get_average_pad_coordinates()

#                         if avg_x is None or avg_y is None or avg_z is None:
#                             print("Failed to calculate fine adjustment coordinates. Retrying...")
#                             continue

#                         print(f"Fine adjustment position - X: {avg_x}, Y: {avg_y}, Z: {avg_z}")

#                         # Stage 2: Perform minor adjustments and descend
#                         print("Making minor adjustments and descending...")
#                         # Apply undershoot multiplier for X and Y
#                         undershoot_m = 1.3
#                         adjusted_x = round(avg_x * undershoot_m)
#                         adjusted_y = round(avg_y * undershoot_m)
#                         adjusted_z = round(-1*avg_z)  # Descend without additional offset
#                         if abs(avg_x) < 5 and abs(avg_y) < 5:  # If within 5 cm of the pad, land
#                             print("Close to mission pad. Landing directly.")
#                             tello.land()
#                             break
#                         # Fly to the undershoot-adjusted position
#                         tello.go_xyz_speed(adjusted_x, adjusted_y, adjusted_z, 10)
#                         print("Descending to the mission pad...")
#                         time.sleep(1)  # Allow time for adjustments and descent

#                         # Land once the drone is aligned
#                         print("Landing on the mission pad...")
#                         tello.land()
#                         break  # Exit the loop after landing
#                     else:
#                         print("Mission pad lost during fine adjustments. Retrying...")
#                         continue

#                 except Exception as e:
#                     print(f"An error occurred during the flight: {e}")
#                     tello.land()
#                     break
#             break

#         time.sleep(0.1)  # Check every 0.1 seconds

# finally:
#     # Disable mission pad detection and safely end
#     tello.disable_mission_pads()
#     tello.end()
